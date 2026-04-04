from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from database import create_db_and_tables, get_async_session, Post
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from src.image.images import imagekit
import shutil
import os
import tempfile
import uuid


def _file_kind(content_type: str | None) -> str:
    if content_type and content_type.startswith("video"):
        return "video"
    return "image"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(title="Media Sharing API", lifespan=lifespan)


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
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
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]

    post_data = []
    for post in posts:
        post_data.append({
            "id": str(post.id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at
        })

    return post_data
