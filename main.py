import os
from importlib.metadata import files

from fastapi import FastAPI
import os
from PIL import Image
from tools.image_tools import ImageTools

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/tools/cutImg/{local_path:path}")
async def cut_img(local_path: str):
    result = ImageTools.cut_bottom(local_path)
    if result:
        return {"message": f"图片处理成功: {local_path}"}
    return {"message": f"图片处理失败: {local_path}", "status": "error"}
