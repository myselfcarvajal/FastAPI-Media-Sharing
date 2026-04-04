from dotenv import load_dotenv
from imagekitio import ImageKit
import os

load_dotenv()

# Client-side / URL building (not ImageKit() constructor params in SDK v5+)
IMAGEKIT_PUBLIC_KEY = os.getenv("IMAGEKIT_PUBLIC_KEY")
URL_ENDPOINT = os.getenv("IMAGEKIT_URL_ENDPOINT")

imagekit = ImageKit(private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"))
