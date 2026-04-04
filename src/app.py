from typing import cast
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from database import User, create_db_and_tables, get_async_session, Post
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from src.image.images import imagekit
import shutil
import os
import tempfile
import uuid
from src.users.users import auth_backend, current_active_user, fastapi_users
from src.users.schema import UserRead, UserCreate, UserUpdate


def _file_kind(content_type: str | None) -> str:
    if content_type and content_type.startswith("video"):
        return "video"
    return "image"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(title="Media Sharing API", lifespan=lifespan)

app.include_router(fastapi_users.get_auth_router(
    auth_backend), prefix='/auth/jwt', tags=["auth"])
app.include_router(fastapi_users.get_register_router(
    UserRead, UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(),
                   prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(
    UserRead), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(
    UserRead, UserUpdate), prefix="/users", tags=["users"])


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    safe_name = file.filename or "upload" + uuid.uuid4().hex
    suffix = os.path.splitext(safe_name)[1]
    temp_file_path: str | None = None
    upload_result = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        with open(temp_file_path, "rb") as local_file:
            file_bytes = local_file.read()

        upload_result = imagekit.files.upload(
            file=file_bytes,
            file_name=safe_name,
            use_unique_file_name=True,
            tags=["backend-uploads"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if temp_file_path:
            os.unlink(temp_file_path)

    if upload_result is None or not upload_result.url:
        raise HTTPException(
            status_code=500, detail="ImageKit upload did not succeed")

    post = Post(
        user_id=user.id,
        caption=caption,
        url=upload_result.url,
        file_type=_file_kind(file.content_type),
        file_name=safe_name,
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


@app.get("/feed")
async def get_feed(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]

    result = await session.execute(select(User))
    users = [row[0] for row in result.all()]

    user_dict = {user.id: user.email for user in users}

    post_data = []
    for post in posts:
        post_data.append({
            "id": str(post.id),
            "user_id": str(post.user_id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at,
            "is_owner": cast(uuid.UUID, post.user_id) == cast(uuid.UUID, user.id),
            "email": user_dict.get(cast(uuid.UUID, post.user_id), "Unknown")
        })

    return post_data


@app.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        post_uuid = uuid.UUID(post_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid post id") from None

    post = await session.get(Post, post_uuid)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if cast(uuid.UUID, post.user_id) != cast(uuid.UUID, user.id):
        raise HTTPException(
            status_code=403, detail="You don't have permission to delete this post")

    await session.delete(post)
    await session.commit()
    return {"message": "Post deleted successfully"}
