import os
from importlib.metadata import files

from fastapi import FastAPI
import os
from PIL import Image

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/tools/cutImg/{local_path:path}")
async def cut_img(local_path: str):
    for filename in os.listdir(local_path):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            # 构建完整的文件路径
            file_path = os.path.join(local_path, filename)
            # 打开图像文件
            with Image.open(file_path) as img:
                width, height = img.size
                # 定义裁剪区域 默认裁剪底部5px
                crop_area = (0, 0, width, height - 50)
                # 裁剪图像 覆盖原图
                img_cropped = img.crop(crop_area)
                img_cropped.save(file_path)
    return {"message": f"Received path: {local_path} operate down"}
