import os
from importlib.metadata import files
from datetime import datetime

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
async def playwright_login(force: bool = False):
    """
    Playwright搭桥 - 让用户手动登录小红书
    
    :param force: 是否强制重新登录（忽略缓存）
    """
    from tools.image_tools import ImageTools
    
    result = await ImageTools.playwright_login_bridge(force_login=force)
    
    if result["status"] == "success":
        response_data = {
            "message": result["message"],
            "data": {
                "cookies_file": result["cookies_file"],
                "cookies_count": result["cookies_count"]
            }
        }
        # 如果有剩余时间信息，添加到响应中
        if "remaining_minutes" in result:
            response_data["data"]["remaining_minutes"] = result["remaining_minutes"]
        return response_data
    else:
        return {
            "message": result["message"],
            "status": "error"
        }


@app.get("/tools/cookieStatus")
async def check_cookie_status():
    """检查Cookie缓存状态"""
    from tools.image_tools import CookieManager
    
    cookie_manager = CookieManager()
    cookies = cookie_manager.get_cookies()
    
    if cookies:
        remaining_time = cookie_manager.get_remaining_time()
        if remaining_time:
            minutes_left = remaining_time.total_seconds() / 60
            return {
                "status": "valid",
                "message": f"Cookies有效，剩余{minutes_left:.1f}分钟",
                "data": {
                    "cookies_count": len(cookies),
                    "remaining_minutes": minutes_left,
                    "expires_at": (datetime.now() + remaining_time).isoformat()
                }
            }
    
    return {
        "status": "expired",
        "message": "Cookies已过期或不存在",
        "data": {
            "cookies_count": 0,
            "remaining_minutes": 0
        }
    }


@app.get("/tools/getImgViaPlaywright")
async def get_img_via_playwright(urls: str, headless: bool = True, max_concurrent: int = 1):
    """
    【智能批量接口】使用Playwright批量抓取小红书图片
    - 支持单个或多个URL（用逗号分隔）
    - 自动判断Cookie状态
    - Cookie有效：直接爬取（后台静默运行）
    - Cookie无效：自动弹窗登录，然后批量爬取
    - 15分钟内所有请求复用同一Cookie
    
    :param urls: 小红书链接（单个URL或多个URL用逗号分隔）
    :param headless: 是否使用无头浏览器爬取（默认True，后台静默运行）
    :param max_concurrent: 最大并发数（默认1，串行处理）
    """
    from tools.image_tools import ImageTools, CookieManager
    import asyncio
    
    # 解析URL列表
    url_list = [url.strip() for url in urls.split(',') if url.strip()]
    
    if not url_list:
        return {
            "status": "error",
            "message": "请提供至少一个有效的URL",
            "hint": "URL参数不能为空，多个URL用逗号分隔"
        }
    
    # 检查Cookie状态
    cookie_manager = CookieManager()
    if cookie_manager.is_valid():
        remaining_time = cookie_manager.get_remaining_time()
        if remaining_time:
            initial_cookie_status = f"Cookie有效（剩余{remaining_time.total_seconds()/60:.1f}分钟）"
        else:
            initial_cookie_status = "Cookie即将过期"
    else:
        initial_cookie_status = "Cookie无效，将自动登录"
    
    print(f"🚀 开始批量处理 {len(url_list)} 个URL")
    print(f"📊 初始Cookie状态: {initial_cookie_status}")
    
    results = []
    success_count = 0
    error_count = 0
    
    # 批量处理每个URL
    for i, url in enumerate(url_list, 1):
        print(f"\n📥 处理第 {i}/{len(url_list)} 个URL: {url}")
        
        try:
            # auto_login=True，自动处理登录（只有第一个需要登录，后续复用Cookie）
            result = await ImageTools.get_img_via_playwright(url, auto_login=True, headless=headless)
            
            if result:
                success_count += 1
                result_data = {
                    "url": url,
                    "status": "success",
                    "message": f"第{i}个URL处理成功",
                    "index": i
                }
                print(f"✅ 第{i}个URL处理成功")
            else:
                error_count += 1
                result_data = {
                    "url": url,
                    "status": "error", 
                    "message": f"第{i}个URL处理失败",
                    "index": i,
                    "hint": "请检查URL是否正确"
                }
                print(f"❌ 第{i}个URL处理失败")
                
            results.append(result_data)
            
        except Exception as e:
            error_count += 1
            result_data = {
                "url": url,
                "status": "error",
                "message": f"第{i}个URL处理异常: {str(e)}",
                "index": i
            }
            results.append(result_data)
            print(f"💥 第{i}个URL处理异常: {str(e)}")
    
    # 最终Cookie状态
    final_cookie_manager = CookieManager()
    if final_cookie_manager.is_valid():
        remaining_time = final_cookie_manager.get_remaining_time()
        if remaining_time:
            final_cookie_status = f"Cookie仍然有效（剩余{remaining_time.total_seconds()/60:.1f}分钟）"
        else:
            final_cookie_status = "Cookie已接近过期"
    else:
        final_cookie_status = "Cookie已过期"
    
    print(f"\n🎉 批量处理完成！成功: {success_count}, 失败: {error_count}")
    
    return {
        "status": "completed",
        "message": f"批量处理完成，成功{success_count}个，失败{error_count}个",
        "summary": {
            "total_urls": len(url_list),
            "success_count": success_count,
            "error_count": error_count,
            "initial_cookie_status": initial_cookie_status,
            "final_cookie_status": final_cookie_status,
            "browser_mode": "headless" if headless else "visible"
        },
        "results": results
    }


@app.get("/tools/")
async def get_img_with_auto_login(url: str, headless: bool = False):
    """
    使用Playwright抓取小红书图片，自动处理登录和Cookie管理
    - Cookie有15分钟有效期
    - 过期后自动重新登录
    
    :param url: 小红书链接
    :param headless: 是否使用无头浏览器（默认False，使用可见浏览器）
    """
    from tools.image_tools import ImageTools, CookieManager
    
    try:
        # 检查cookie状态
        cookie_manager = CookieManager()
        cookies = cookie_manager.get_cookies()
        
        if cookies:
            remaining_time = cookie_manager.get_remaining_time()
            if remaining_time:
                print(f"✅ 使用缓存的Cookies，剩余有效期: {remaining_time.total_seconds()/60:.1f}分钟")
        else:
            print("⚠️ Cookies已过期或不存在，需要重新登录")
        
        # 调用抓取函数，auto_login=True会自动处理登录
        result = await ImageTools.get_img_via_playwright(url, auto_login=True, headless=headless)
        
        if result:
            return {
                "status": "success",
                "message": f"图片处理成功: {url}",
                "cookie_status": "valid" if cookie_manager.is_valid() else "refreshed",
                "browser_mode": "headless" if headless else "visible"
            }
        else:
            return {
                "status": "error",
                "message": f"图片处理失败: {url}",
                "hint": "请检查URL是否正确或稍后重试"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"处理请求时发生错误: {str(e)}"
        }


# 添加直接启动入口
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
