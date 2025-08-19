import os
from importlib.metadata import files

from fastapi import FastAPI
import os
from PIL import Image
from tools.image_tools import ImageTools
from tools.option_tools import OptionTools
from tools.story_tools import StoryTools

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


@app.get("/tools/getImgViaUrl")
async def get_img_via_url(url: str):
    result = ImageTools.get_img_via_url(url)
    if result:
        return {"message": f"图片处理成功: {url}"}
    return {"message": f"图片处理失败: {url}", "status": "error"}


@app.get("/tools/calculateOptionYield")
async def calculate_option_yield():
    option_tools = OptionTools()
    result = option_tools.calculate_yield()
    if result:
        return {"message": "计算收益率成功"}
    return {"message": "计算收益率失败", "status": "error"}


@app.get("/tools/generateDailyStory")
async def generate_daily_story():
    """生成每日暧昧小故事"""
    story_tools = StoryTools()
    result = story_tools.generate_daily_story()
    
    if result["status"] == "success":
        return {
            "message": "故事生成成功",
            "data": {
                "keywords": result["keywords"],
                "word_count": result["word_count"],
                "filepath": result["filepath"],
                "generated_at": result["generated_at"]
            }
        }
    else:
        return {
            "message": "故事生成失败", 
            "status": "error",
            "error": result.get("error_message", "未知错误")
        }


@app.get("/tools/testSiliconFlowAPI")
async def test_silicon_flow_api(prompt: str = "你好，请介绍一下你自己"):
    """测试硅基流动API对话接口"""
    story_tools = StoryTools()
    result = story_tools.call_siliconflow_api(prompt)
    
    if result and not result.startswith("❌"):
        return {
            "message": "API测试成功",
            "response": result,
            "character_count": len(result)
        }
    else:
        return {
            "message": "API测试失败",
            "status": "error", 
            "error": result
        }


# 添加直接启动入口
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
