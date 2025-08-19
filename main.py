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


@app.get("/tools/analyzeImageAndGenerateName")
async def analyze_image_and_generate_name(image_url: str):
    """测试图片识别和暧昧文件夹名生成功能"""
    try:
        from tools.image_tools import ImageTools
        
        # 加载配置获取API密钥
        config = ImageTools._load_config()
        api_key = config.get("siliconflow", {}).get("api_key")
        
        if not api_key:
            return {
                "message": "API密钥未配置",
                "status": "error"
            }
        
        # 分析图片
        keywords = ImageTools.get_image_analysis_keywords(image_url, api_key)
        
        if keywords and not keywords.startswith("❌"):
            # 生成暧昧文件夹名
            romantic_name = ImageTools.generate_romantic_folder_name(keywords)
            
            return {
                "message": "图片分析成功",
                "data": {
                    "image_url": image_url,
                    "keywords": keywords,
                    "romantic_folder_name": romantic_name
                }
            }
        else:
            return {
                "message": "图片分析失败",
                "status": "error",
                "error": keywords
            }
            
    except Exception as e:
        return {
            "message": "处理失败",
            "status": "error",
            "error": str(e)
        }


@app.get("/tools/processManualDownload")
async def process_manual_download(download_folder: str):
    """处理手动下载文件夹中的图片（适用于RoxyBrowser手动下载）"""
    from tools.image_tools import ImageTools
    
    result = ImageTools.process_manual_download_folder(download_folder)
    
    if result["status"] == "success":
        return {
            "message": result["message"],
            "data": {
                "processed_count": result["processed_count"],
                "total_count": result["total_count"],
                "output_folder": result["output_folder"],
                "processed_files": result["processed_files"]
            }
        }
    else:
        return {
            "message": result["message"],
            "status": "error"
        }


@app.get("/tools/playwrightLogin")
async def playwright_login():
    """Playwright搭桥 - 让用户手动登录小红书"""
    from tools.image_tools import ImageTools
    
    result = await ImageTools.playwright_login_bridge()
    
    if result["status"] == "success":
        return {
            "message": result["message"],
            "data": {
                "cookies_file": result["cookies_file"],
                "cookies_count": result["cookies_count"]
            }
        }
    else:
        return {
            "message": result["message"],
            "status": "error"
        }


@app.get("/tools/getImgViaPlaywright")
async def get_img_via_playwright(url: str):
    """使用Playwright和已保存的Cookies抓取小红书图片"""
    from tools.image_tools import ImageTools
    
    result = await ImageTools.get_img_via_playwright(url)
    
    if result:
        return {
            "message": f"图片处理成功: {url}"
        }
    else:
        return {
            "message": f"图片处理失败: {url}",
            "status": "error",
            "hint": "如果是登录问题，请先调用 GET /tools/playwrightLogin 接口进行登录"
        }


# 添加直接启动入口
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
