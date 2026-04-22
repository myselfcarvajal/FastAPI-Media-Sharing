import os

from dotenv import load_dotenv
import uvicorn

load_dotenv()

PORT = int(os.environ["PORT"])

if __name__ == "__main__":
    uvicorn.run("src.app:app", host="0.0.0.0", port=PORT, reload=True)
