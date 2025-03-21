import os
from importlib.metadata import files

from fastapi import FastAPI
import os
from PIL import Image
from tools.image_tools import ImageTools
from tools.option_tools import OptionTools

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/tools/cutImg/{local_path:path}")
async def cut_img(local_path: str):
    result = ImageTools.cut_bottom(local_path, 50)
    if result:
        return {"message": f"图片处理成功: {local_path}"}
    return {"message": f"图片处理失败: {local_path}", "status": "error"}


@app.get("/tools/calculateOptionYield")
async def calculate_option_yield():
    option_tools = OptionTools()
    result = option_tools.calculate_yield()
    if result:
        return {"message": "计算收益率成功"}
    return {"message": "计算收益率失败", "status": "error"}


# 添加直接启动入口
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
