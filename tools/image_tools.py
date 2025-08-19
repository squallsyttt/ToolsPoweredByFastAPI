# 完善代码 18998
import os
import json
from datetime import datetime
from PIL import Image
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from playwright.async_api import async_playwright
import time
import base64
import io


class ImageTools:
    
    @staticmethod  
    async def playwright_login_bridge() -> dict:
        """
        使用Playwright搭桥，让用户手动登录小红书
        
        :return: 包含登录状态和Cookie的结果
        """
        try:
            print("🎭 启动Playwright搭桥模式...")
            
            async with async_playwright() as p:
                # 启动可见的浏览器供用户登录
                browser = await p.chromium.launch(
                    headless=False,  # 可见模式让用户登录
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor",
                    ]
                )
                
                # 创建浏览器上下文
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                )
                
                page = await context.new_page()
                
                print("🌐 正在打开小红书登录页面...")
                await page.goto("https://www.xiaohongshu.com/")
                
                print("👤 请在打开的浏览器窗口中手动登录小红书...")
                print("✋ 登录完成后，请在控制台按 Enter 键继续...")
                
                # 等待用户手动登录 - 这里需要用异步方式处理用户输入
                import asyncio
                import sys
                
                # 创建一个简单的异步输入等待
                print("💡 请在浏览器中登录完成后，等待3分钟或手动停止服务器重新启动")
                await asyncio.sleep(180)  # 等待3分钟让用户登录
                
                # 获取当前的Cookies
                cookies = await context.cookies()
                
                # 保存Cookies到文件
                cookies_file = "xiaohongshu_cookies.json"
                with open(cookies_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Cookies已保存到: {cookies_file}")
                
                # 验证登录状态
                await page.goto("https://www.xiaohongshu.com/user/profile/me")
                await asyncio.sleep(2)
                
                # 检查是否成功访问个人页面
                current_url = page.url
                is_logged_in = "login" not in current_url.lower()
                
                await browser.close()
                
                if is_logged_in:
                    return {
                        "status": "success",
                        "message": "登录成功，Cookies已保存",
                        "cookies_file": cookies_file,
                        "cookies_count": len(cookies)
                    }
                else:
                    return {
                        "status": "error", 
                        "message": "登录验证失败，请重新尝试"
                    }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Playwright搭桥过程中发生错误: {str(e)}"
            }
    
    @staticmethod
    async def check_playwright_login_status() -> dict:
        """
        检查Playwright登录状态是否有效
        使用轻量级检查，避免不必要的浏览器启动
        
        :return: 登录状态检查结果
        """
        try:
            print("🔍 正在检查Playwright登录状态...")
            
            # 检查Cookies文件是否存在
            cookies_file = "xiaohongshu_cookies.json"
            if not os.path.exists(cookies_file):
                print("❌ 未找到登录Cookies文件")
                return {
                    "status": "invalid",
                    "message": "未找到登录Cookies文件",
                    "need_login": True
                }
            
            # 读取并检查Cookies
            with open(cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            if not cookies:
                print("❌ Cookies文件为空")
                return {
                    "status": "invalid", 
                    "message": "Cookies文件为空",
                    "need_login": True
                }
            
            print(f"📄 找到 {len(cookies)} 个Cookies")
            
            # 检查关键Cookie是否存在（小红书的关键认证cookie）
            key_cookies = ['web_session', 'websectiga', 'sec_poison_id']
            has_key_cookies = any(cookie.get('name') in key_cookies for cookie in cookies)
            
            if not has_key_cookies:
                print("⚠️ 缺少关键认证Cookies")
                return {
                    "status": "invalid",
                    "message": "缺少关键认证Cookies",
                    "need_login": True
                }
            
            # 检查Cookies的过期时间
            import time
            current_time = time.time()
            expired_count = 0
            
            for cookie in cookies:
                if 'expires' in cookie and cookie['expires'] > 0:
                    if cookie['expires'] < current_time:
                        expired_count += 1
            
            if expired_count > len(cookies) * 0.5:  # 如果超过一半的cookies过期
                print(f"⚠️ 大部分Cookies已过期 ({expired_count}/{len(cookies)})")
                return {
                    "status": "invalid",
                    "message": "大部分Cookies已过期",
                    "need_login": True
                }
            
            print(f"✅ Cookies基础检查通过，有效期内cookies: {len(cookies) - expired_count}/{len(cookies)}")
            
            # 只有在基础检查通过后，才进行实际的网络验证（轻量级）
            print("🌐 进行快速网络验证...")
            
            async with async_playwright() as p:
                # 启动无头浏览器进行快速验证
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor",
                        "--disable-images",  # 禁用图片加载
                        "--disable-javascript",  # 禁用JS
                    ]
                )
                
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                )
                
                # 添加Cookies
                await context.add_cookies(cookies)
                page = await context.new_page()
                
                try:
                    # 直接访问一个简单的API端点进行快速验证
                    response = await page.goto("https://www.xiaohongshu.com/api/sns/web/v1/user/selfinfo", timeout=5000)
                    
                    if response and response.status == 200:
                        print("✅ API验证通过，登录状态有效")
                        await browser.close()
                        return {
                            "status": "valid",
                            "message": "登录状态有效",
                            "need_login": False,
                            "cookies_count": len(cookies)
                        }
                    else:
                        print(f"⚠️ API验证失败，状态码: {response.status if response else 'None'}")
                        
                except Exception as api_error:
                    print(f"⚠️ API验证异常: {str(api_error)}")
                
                await browser.close()
                
                # API验证失败，返回需要登录
                return {
                    "status": "invalid",
                    "message": "API验证失败，登录状态可能已过期",
                    "need_login": True
                }
                
        except Exception as e:
            print(f"❌ 检查登录状态时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"检查登录状态时发生错误: {str(e)}",
                "need_login": True
            }
    
    @staticmethod
    async def get_img_via_playwright(url: str) -> bool:
        """
        使用Playwright和已保存的Cookies抓取小红书图片
        自动检查登录状态，如果无效则弹出登录窗口
        
        :param url: 小红书链接
        :return: 是否成功
        """
        try:
            print(f"🎭 使用Playwright抓取小红书图片...")
            
            # 1. 先检查登录状态
            login_status = await ImageTools.check_playwright_login_status()
            print(f"🔍 登录状态检查结果: {login_status['message']}")
            
            # 2. 只有在真正需要登录时才触发登录流程
            if login_status.get('need_login', False):
                print("⚠️ 检测到需要重新登录，但让我们先尝试直接抓取...")
                print("💡 如果抓取失败，您可以手动调用 /tools/playwrightLogin 接口重新登录")
                
                # 不自动弹窗，而是先尝试使用现有cookies继续
                # 如果真的失败了，在错误消息中提示用户手动登录
            
            # 3. 现在开始正常的抓取流程
            # 检查Cookies文件是否存在
            cookies_file = "xiaohongshu_cookies.json"
            if not os.path.exists(cookies_file):
                print("❌ 未找到Cookies文件，请先调用 /tools/playwrightLogin 接口进行登录")
                return False
            
            # 读取保存的Cookies
            with open(cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            print(f"📄 加载了 {len(cookies)} 个Cookies")
            
            import asyncio
            async with async_playwright() as p:
                # 启动无头浏览器
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox", 
                        "--disable-dev-shm-usage",
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor",
                    ]
                )
                
                # 创建上下文并添加Cookies
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                )
                
                # 添加Cookies
                await context.add_cookies(cookies)
                
                page = await context.new_page()
                
                print("🌐 正在访问小红书页面...")
                await page.goto(url)
                
                # 等待页面加载
                await page.wait_for_timeout(3000)
                
                # 检查是否被重定向到登录页
                current_url = page.url
                if "login" in current_url.lower():
                    print("⚠️ Cookies已过期，被重定向到登录页")
                    print("💡 请调用 GET /tools/playwrightLogin 接口重新登录")
                    await browser.close()
                    return False
                
                print("✅ 成功访问页面，开始抓取图片...")
                
                # 创建输出文件夹
                current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = os.path.join("resource", f"playwright_{current_time}")
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                print(f"📁 创建输出文件夹: {output_dir}")
                
                # 等待图片加载
                await page.wait_for_timeout(5000)
                
                # 查找图片元素
                img_selectors = [
                    '.note-slider-img',
                    '.swiper-slide img', 
                    '.img-container img',
                    'img[src*="sns-webpic"]',
                    'img[data-src*="sns-webpic"]'
                ]
                
                img_urls = []
                unique_urls = set()
                
                for selector in img_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements:
                            img_url = await element.get_attribute('src') or await element.get_attribute('data-src')
                            if img_url and 'sns-webpic' in img_url and img_url not in unique_urls:
                                unique_urls.add(img_url)
                                img_urls.append(img_url)
                                print(f"📌 找到图片: {img_url}")
                    except Exception:
                        continue
                
                print(f"📊 共找到 {len(img_urls)} 张图片")
                
                if not img_urls:
                    print("❌ 未找到有效图片")
                    await browser.close()
                    return False
                
                # 下载图片
                success_count = 0
                for index, img_url in enumerate(img_urls):
                    try:
                        print(f"📥 下载第 {index+1}/{len(img_urls)} 张图片...")
                        
                        # 使用requests下载图片
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                            'Referer': url
                        }
                        
                        response = requests.get(img_url, headers=headers, timeout=30)
                        response.raise_for_status()
                        
                        # 保存为临时文件，然后转换格式
                        temp_file_path = os.path.join(output_dir, f"temp_image_{index+1}")
                        
                        with open(temp_file_path, 'wb') as f:
                            f.write(response.content)
                        
                        # 使用PIL转换为jpg格式
                        try:
                            with Image.open(temp_file_path) as img:
                                # 如果是RGBA模式，转换为RGB（用于jpg格式）
                                if img.mode in ('RGBA', 'LA', 'P'):
                                    # 创建白色背景
                                    background = Image.new('RGB', img.size, (255, 255, 255))
                                    if img.mode == 'P':
                                        img = img.convert('RGBA')
                                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                                    img = background
                                elif img.mode not in ('RGB', 'L'):
                                    img = img.convert('RGB')
                                
                                # 保存为jpg格式
                                file_path = os.path.join(output_dir, f"image_{index+1}.jpg")
                                img.save(file_path, 'JPEG', quality=95)
                                
                        except Exception as convert_error:
                            print(f"⚠️ 图片格式转换失败，保存原格式: {convert_error}")
                            # 如果转换失败，使用原格式
                            ext = 'jpg'  # 默认扩展名
                            if '.png' in img_url or 'png' in response.headers.get('content-type', ''):
                                ext = 'png'
                            elif '.webp' in img_url or 'webp' in response.headers.get('content-type', ''):
                                ext = 'webp'
                            
                            file_path = os.path.join(output_dir, f"image_{index+1}.{ext}")
                            import shutil
                            shutil.move(temp_file_path, file_path)
                        else:
                            # 删除临时文件
                            os.remove(temp_file_path)
                        
                        # 裁剪图片去除水印
                        try:
                            img = Image.open(file_path)
                            width, height = img.size
                            pixels_to_cut = 50
                            if height > pixels_to_cut:
                                crop_area = (0, 0, width, height - pixels_to_cut)
                                img_cropped = img.crop(crop_area)
                                img.close()
                                img_cropped.save(file_path)
                                print(f"✅ 图片下载并裁剪成功: {file_path}")
                            else:
                                img.close()
                                print(f"✅ 图片下载成功: {file_path}")
                        except Exception as crop_error:
                            print(f"⚠️ 图片裁剪失败但下载成功: {crop_error}")
                        
                        success_count += 1
                        
                    except Exception as e:
                        print(f"❌ 下载图片失败: {str(e)}")
                
                await browser.close()
                
                # AI识别并重命名文件夹
                if success_count > 0 and img_urls:
                    print("\\n🔍 开始AI图片识别...")
                    try:
                        config = ImageTools._load_config()
                        api_key = config.get("siliconflow", {}).get("api_key")
                        
                        if api_key:
                            # 使用第一张图片进行识别
                            first_image_url = img_urls[0]
                            keywords = ImageTools.get_image_analysis_keywords(first_image_url, api_key)
                            
                            if keywords and not keywords.startswith("❌"):
                                # 生成暧昧文件夹名
                                romantic_name = ImageTools.generate_romantic_folder_name(keywords)
                                
                                # 重命名文件夹
                                parent_dir = os.path.dirname(output_dir)
                                new_output_dir = os.path.join(parent_dir, romantic_name)
                                
                                if os.path.exists(output_dir) and not os.path.exists(new_output_dir):
                                    os.rename(output_dir, new_output_dir)
                                    print(f"✨ 文件夹已重命名为: {new_output_dir}")
                                    output_dir = new_output_dir
                                    
                                    # 保存AI描述到文本文件
                                    try:
                                        # 使用清理后的文件夹名作为文本文件名
                                        text_filename = f"{romantic_name}.txt"
                                        text_file_path = os.path.join(output_dir, text_filename)
                                        
                                        with open(text_file_path, 'w', encoding='utf-8') as f:
                                            f.write(f"AI图片分析结果\n")
                                            f.write(f"=" * 30 + "\n\n")
                                            f.write(f"标题: {romantic_name}\n\n")
                                            f.write(f"AI描述:\n{keywords}\n\n")
                                            f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                        
                                        print(f"📄 AI描述已保存到: {text_file_path}")
                                    except Exception as text_error:
                                        print(f"⚠️ 保存AI描述文件失败: {text_error}")
                        
                    except Exception as e:
                        print(f"⚠️ AI识别过程出错: {e}")
                
                print(f"🎉 任务完成！成功下载 {success_count}/{len(img_urls)} 张图片")
                print(f"📂 保存位置: {output_dir}")
                return success_count > 0
                
        except Exception as e:
            print(f"❌ Playwright抓取过程中发生错误: {str(e)}")
            return False
    
    @staticmethod
    def process_manual_download_folder(download_folder: str) -> dict:
        """
        处理手动下载文件夹中的图片（适用于RoxyBrowser手动下载）
        
        :param download_folder: 下载文件夹路径
        :return: 处理结果
        """
        try:
            print(f"🔍 开始处理手动下载文件夹: {download_folder}")
            
            if not os.path.exists(download_folder):
                return {
                    "status": "error",
                    "message": f"下载文件夹不存在: {download_folder}"
                }
            
            # 查找图片文件
            image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
            image_files = []
            
            for filename in os.listdir(download_folder):
                if any(filename.lower().endswith(ext) for ext in image_extensions):
                    image_files.append(os.path.join(download_folder, filename))
            
            if not image_files:
                return {
                    "status": "error", 
                    "message": "下载文件夹中未找到图片文件"
                }
            
            print(f"📁 找到 {len(image_files)} 张图片")
            
            # 创建以当前时间命名的处理文件夹
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join("resource", f"manual_{current_time}")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            print(f"📁 创建输出文件夹: {output_dir}")
            
            processed_files = []
            success_count = 0
            
            # 处理每张图片
            for i, image_file in enumerate(image_files):
                try:
                    print(f"🔄 处理第 {i+1}/{len(image_files)} 张图片: {os.path.basename(image_file)}")
                    
                    # 复制并重命名图片
                    ext = os.path.splitext(image_file)[1].lower()
                    new_filename = f"image_{i+1}{ext}"
                    new_file_path = os.path.join(output_dir, new_filename)
                    
                    # 复制文件
                    import shutil
                    shutil.copy2(image_file, new_file_path)
                    
                    # 执行裁剪（去除小红书水印）
                    try:
                        print(f"✂️ 正在裁剪图片: {new_file_path}")
                        img = Image.open(new_file_path)
                        width, height = img.size
                        pixels_to_cut = 50
                        if height > pixels_to_cut:
                            crop_area = (0, 0, width, height - pixels_to_cut)
                            img_cropped = img.crop(crop_area)
                            img.close()
                            img_cropped.save(new_file_path)
                            print(f"✅ 图片裁剪成功")
                        else:
                            img.close()
                            print(f"⚠️ 图片高度 ({height}px) 小于裁剪像素 ({pixels_to_cut}px)，跳过裁剪")
                    except Exception as crop_error:
                        print(f"❌ 裁剪图片时发生错误: {str(crop_error)}")
                    
                    processed_files.append(new_file_path)
                    success_count += 1
                    print(f"✅ 图片处理成功: {new_file_path}")
                    
                except Exception as e:
                    print(f"❌ 处理图片失败: {str(e)}")
            
            # 如果处理成功且有图片，进行图片识别并重命名文件夹
            if success_count > 0 and processed_files:
                print(f"\\n🔍 开始分析第一张图片生成暧昧文件夹名...")
                try:
                    # 加载配置获取API密钥
                    config = ImageTools._load_config()
                    api_key = config.get("siliconflow", {}).get("api_key")
                    
                    if api_key:
                        # 使用第一张图片进行识别（需要先上传到网络）
                        first_image_path = processed_files[0]
                        print(f"📸 使用第一张图片进行分析: {os.path.basename(first_image_path)}")
                        
                        # 为了使用API，我们需要将图片转为base64
                        with open(first_image_path, 'rb') as f:
                            image_data = f.read()
                            base64_image = base64.b64encode(image_data).decode('utf-8')
                            
                        keywords = ImageTools.analyze_image_with_base64(base64_image, api_key)
                        
                        if keywords and not keywords.startswith("❌"):
                            # 生成暧昧文件夹名
                            romantic_name = ImageTools.generate_romantic_folder_name(keywords)
                            
                            # 构建新的文件夹路径
                            parent_dir = os.path.dirname(output_dir)
                            new_output_dir = os.path.join(parent_dir, romantic_name)
                            
                            # 重命名文件夹
                            if os.path.exists(output_dir) and not os.path.exists(new_output_dir):
                                os.rename(output_dir, new_output_dir)
                                print(f"✨ 文件夹已重命名为: {new_output_dir}")
                                output_dir = new_output_dir
                                
                                # 保存AI描述到文本文件
                                try:
                                    # 使用清理后的文件夹名作为文本文件名
                                    text_filename = f"{romantic_name}.txt"
                                    text_file_path = os.path.join(output_dir, text_filename)
                                    
                                    with open(text_file_path, 'w', encoding='utf-8') as f:
                                        f.write(f"AI图片分析结果\n")
                                        f.write(f"=" * 30 + "\n\n")
                                        f.write(f"标题: {romantic_name}\n\n")
                                        f.write(f"AI描述:\n{keywords}\n\n")
                                        f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                    
                                    print(f"📄 AI描述已保存到: {text_file_path}")
                                except Exception as text_error:
                                    print(f"⚠️ 保存AI描述文件失败: {text_error}")
                            else:
                                print(f"⚠️ 文件夹重命名失败，目标路径可能已存在: {new_output_dir}")
                        else:
                            print(f"⚠️ 图片识别失败: {keywords}")
                    else:
                        print("⚠️ 未配置API密钥，跳过图片识别和文件夹重命名")
                        
                except Exception as e:
                    print(f"⚠️ 图片识别或文件夹重命名过程中出现错误: {e}")
            
            return {
                "status": "success",
                "message": f"成功处理 {success_count}/{len(image_files)} 张图片",
                "processed_count": success_count,
                "total_count": len(image_files),
                "output_folder": output_dir,
                "processed_files": [os.path.basename(f) for f in processed_files]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"处理手动下载文件夹时发生错误: {str(e)}"
            }
    
    @staticmethod
    def analyze_image_with_base64(base64_image: str, api_key: str) -> str:
        """
        使用base64编码的图片进行分析
        
        :param base64_image: base64编码的图片数据
        :param api_key: API密钥
        :return: 分析结果关键词
        """
        try:
            print(f"🧠 使用base64图片数据进行分析...")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "Qwen/Qwen2.5-VL-32B-Instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请分析这张图片，用中文给出文章标题描述，要求：1.描述画面主要内容 2.适合用作图集名称 3.带有一点暧昧色彩。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 200
            }

            api_url = "https://api.siliconflow.cn/v1/chat/completions"
            response = requests.post(api_url, headers=headers, json=payload)
            
            print(f"📊 响应状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ 响应内容: {response.text}")
                
            response.raise_for_status()

            result = response.json()
            keywords = result['choices'][0]['message']['content']
            
            print(f"✅ 图片分析成功。关键词: {keywords}")
            return keywords

        except Exception as e:
            error_message = f"❌ 图片分析失败: {e}"
            print(error_message)
            return error_message
    @staticmethod
    def _extract_image_from_slide(slide, index):
        """从slide元素中提取图片URL"""
        img_selectors = [
            '.note-slider-img',
            '.img-container img',
            'img[src*="sns-webpic"]',
            'img[data-src*="sns-webpic"]',
            'img'
        ]

        for img_sel in img_selectors:
            try:
                img_element = slide.find_element(By.CSS_SELECTOR, img_sel)
                img_url = img_element.get_attribute('src')
                if not img_url:
                    img_url = img_element.get_attribute('data-src') or img_element.get_attribute('data-original')
                if img_url and ('sns-webpic' in img_url or 'xhscdn' in img_url):
                    print(f"✅ 在slide #{index}中找到图片: {img_sel}")
                    return img_url
            except Exception:
                continue
        return None

    @staticmethod
    def _get_total_image_count(driver):
        """获取总图片数的多种尝试"""
        # 方法1: 分页指示器
        try:
            frac_el = driver.find_element(By.CSS_SELECTOR, '.fraction')
            if frac_el and '/' in frac_el.text:
                parts = frac_el.text.strip().split('/')
                if len(parts) == 2 and parts[1].isdigit():
                    count = int(parts[1])
                    print(f"📊 分页指示器显示: {count} 张图")
                    return count
        except Exception:
            pass

        # 方法2: 计算slide数量
        try:
            slides = driver.find_elements(By.CSS_SELECTOR, '.swiper-slide[data-swiper-slide-index]')
            if slides:
                indices = set()
                for slide in slides:
                    idx = slide.get_attribute('data-swiper-slide-index')
                    if idx and idx.isdigit():
                        indices.add(int(idx))
                if indices:
                    count = len(indices)
                    print(f"📊 slide索引计算: {count} 张图")
                    return count
        except Exception:
            pass

        # 方法3: meta标签中的图片数量
        try:
            meta_images = driver.find_elements(By.CSS_SELECTOR, 'meta[property="og:image"]')
            if meta_images:
                count = len(meta_images)
                print(f"📊 meta标签显示: {count} 张图")
                return count
        except Exception:
            pass

        print("📊 无法确定总图片数，使用默认值")
        return None

    @staticmethod
    def _trigger_carousel_navigation(driver, img_urls, unique_urls, total_count):
        """触发轮播导航获取更多图片"""
        try:
            # 查找轮播控制按钮
            next_btn_selectors = [
                '.arrow-controller.right .btn-wrapper',
                '.arrow-controller.right',
                '.swiper-button-next',
                '[class*="next"]',
                '[class*="arrow"][class*="right"]'
            ]

            next_btn = None
            for selector in next_btn_selectors:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, selector)
                    if btn.is_displayed() and btn.is_enabled():
                        next_btn = btn
                        print(f"✅ 找到轮播按钮: {selector}")
                        break
                except Exception:
                    continue

            if not next_btn:
                print("⚠️ 未找到可用的轮播按钮")
                return False

            # 点击轮播按钮收集图片
            max_clicks = min(total_count * 2 if total_count else 10, 15)
            initial_count = len(img_urls)

            for step in range(max_clicks):
                try:
                    # 尝试点击
                    driver.execute_script("arguments[0].click();", next_btn)
                    time.sleep(1.2)  # 增加等待时间

                    # 查找当前活动的图片
                    active_selectors = [
                        '.swiper-slide-active img.note-slider-img',
                        '.swiper-slide-active img',
                        '.active img',
                        '.current img'
                    ]

                    for selector in active_selectors:
                        try:
                            active_img = driver.find_element(By.CSS_SELECTOR, selector)
                            img_url = active_img.get_attribute('src') or active_img.get_attribute('data-src') or active_img.get_attribute('data-original')
                            if img_url and img_url not in unique_urls and ('sns-webpic' in img_url or 'xhscdn' in img_url):
                                unique_urls.add(img_url)
                                img_urls.append(img_url)
                                print(f"➕ 轮播新增图片 #{len(img_urls)}: {img_url}")
                                break
                        except Exception:
                            continue

                    # 检查是否已收集足够图片
                    if total_count and len(img_urls) >= total_count:
                        print("✅ 已收集到预期数量的图片")
                        break

                    # 检查是否有新图片，如果连续几次没有新图片则停止
                    if step > 3 and len(img_urls) == initial_count:
                        print("⚠️ 连续点击未获得新图片，停止轮播")
                        break

                except Exception as e:
                    print(f"⚠️ 轮播点击失败: {str(e)}")
                    break

            new_count = len(img_urls) - initial_count
            print(f"🎯 轮播补齐获得 {new_count} 张新图片")
            return new_count > 0

        except Exception as e:
            print(f"❌ 轮播导航失败: {str(e)}")
            return False

    @staticmethod
    def _trigger_scroll_lazy_loading(driver, img_urls, unique_urls):
        """通过滚动触发懒加载"""
        try:
            print("📜 尝试滚动触发懒加载...")
            initial_count = len(img_urls)

            # 滚动到轮播容器
            try:
                carousel = driver.find_element(By.CSS_SELECTOR, '.swiper-container, .swiper, [class*="swiper"]')
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", carousel)
                time.sleep(1)
            except Exception:
                pass

            # 模拟鼠标悬停和移动
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(driver)

                # 在轮播区域移动鼠标
                carousel_area = driver.find_element(By.CSS_SELECTOR, '.swiper-container, .swiper, [class*="swiper"]')
                actions.move_to_element(carousel_area).perform()
                time.sleep(0.5)

                # 模拟左右移动
                actions.move_by_offset(100, 0).perform()
                time.sleep(0.5)
                actions.move_by_offset(-200, 0).perform()
                time.sleep(0.5)
                actions.move_by_offset(100, 0).perform()
                time.sleep(1)

            except Exception:
                pass

            # 检查是否有新图片被加载
            try:
                new_images = driver.find_elements(By.CSS_SELECTOR, 'img[src*="sns-webpic"], img[data-src*="sns-webpic"]')
                for img in new_images:
                    img_url = img.get_attribute('src') or img.get_attribute('data-src')
                    if img_url and img_url not in unique_urls:
                        unique_urls.add(img_url)
                        img_urls.append(img_url)
                        print(f"📜 滚动触发新图片: {img_url}")
            except Exception:
                pass

            new_count = len(img_urls) - initial_count
            print(f"📜 滚动触发获得 {new_count} 张新图片")

        except Exception as e:
            print(f"❌ 滚动触发失败: {str(e)}")

    @staticmethod
    def get_img_via_url(url: str) -> bool:
        try:
            print(f"🚀 开始处理小红书链接...")
            
            # 设置Chrome选项（无头模式 + 反检测）
            print("⚙️ 正在配置无头浏览器选项...")
            chrome_options = Options()

            # 无头模式
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # 基础窗口设置
            chrome_options.add_argument("--window-size=1920,1080")
            
            # 性能优化参数（无头模式）
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-component-update")
            chrome_options.add_argument("--disable-client-side-phishing-detection")
            chrome_options.add_argument("--disable-hang-monitor")
            chrome_options.add_argument("--disable-prompt-on-repost")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")

            # 内存和缓存优化
            chrome_options.add_argument("--memory-pressure-off")
            chrome_options.add_argument("--max_old_space_size=4096")
            chrome_options.add_argument("--aggressive-cache-discard")

            # 网络优化
            chrome_options.add_argument("--disable-background-downloads")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--disable-login-animations")
            chrome_options.add_argument("--disable-notifications")

            # 更新User-Agent到较新版本，更像真实用户
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
            
            # 增强反检测措施
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 设置页面加载策略
            chrome_options.page_load_strategy = 'eager'  # 不等待所有资源加载完成

            # 初始化WebDriver
            print("🌐 正在启动无头浏览器...")
            try:
                driver = webdriver.Chrome(options=chrome_options)
                
                # 执行反检测脚本
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                print("✅ 无头浏览器启动成功，已启用反检测")

            except TimeoutError:
                print("❌ 浏览器启动超时（30秒），请检查Chrome和ChromeDriver版本是否匹配")
                return False
            except Exception as e:
                print(f"❌ 浏览器启动失败: {str(e)}")
                print("💡 建议检查：")
                print("   1. Chrome浏览器是否已安装")
                print("   2. ChromeDriver版本是否与Chrome版本匹配")
                print("   3. ChromeDriver是否在PATH环境变量中")
                return False
            
            print("📡 正在访问页面...")
            try:
                # 设置页面加载超时
                driver.set_page_load_timeout(30)
                start_time = time.time()
                driver.get(url)
                load_time = time.time() - start_time
                print(f"✅ 页面访问成功，耗时: {load_time:.2f}秒")

                # 执行人类行为模拟
                print("🤖 模拟真实用户行为...")
                
                # 等待页面稍微加载
                time.sleep(2)
                
                # 模拟鼠标移动和滚动
                try:
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(driver)
                    
                    # 随机鼠标移动
                    actions.move_by_offset(100, 200).perform()
                    time.sleep(0.5)
                    actions.move_by_offset(-50, -100).perform()
                    time.sleep(0.5)
                    
                    # 轻微滚动
                    driver.execute_script("window.scrollBy(0, 100);")
                    time.sleep(1)
                    driver.execute_script("window.scrollBy(0, -50);")
                    time.sleep(1)
                    
                except Exception:
                    pass
                
                # 检查是否被重定向到登录页面
                current_url = driver.current_url
                if 'login' in current_url.lower() or 'signin' in current_url.lower():
                    print(f"⚠️ 检测到登录页面重定向，token可能已过期")
                    print(f"📍 当前URL: {current_url}")
                    print("💡 可能的解决方案:")
                    print("   1. 获取新的有效链接（重新复制小红书链接）")
                    print("   2. 尝试在浏览器中手动访问并复制新的链接")
                    print("   3. 检查小红书是否更新了反爬虫机制")
                    driver.quit()
                    return False

            except Exception as e:
                print(f"❌ 页面访问失败: {str(e)}")
                driver.quit()
                return False

            # 使用WebDriverWait智能等待，最长20秒
            print("⏳ 正在等待页面加载完成（最长等待20秒）...")
            wait = WebDriverWait(driver, 20)

            # 创建以当前时间命名的文件夹
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join("resource", current_time)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            print(f"📁 已创建输出文件夹: {output_dir}")

            # 等待图片元素加载
            print("🔍 正在搜索页面中的图片元素...")

            # 先等待页面基本结构加载完成
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.swiper-container, .swiper, [class*="swiper"]')))
                print("✅ 轮播容器已加载")
            except Exception:
                print("⚠️ 未找到轮播容器，尝试查找其他图片结构...")

            # 等待更长时间让页面完全加载和懒加载图片有机会加载
            print("⏳ 等待页面完全加载...")
            time.sleep(5)  # 增加等待时间

            # 使用多种策略查找图片
            print("🎯 使用多重策略查找图片...")

            img_urls = []
            unique_urls = set()

            # 策略1: 基于data-swiper-slide-index查找
            try:
                print("📍 策略1: 基于data-swiper-slide-index查找...")
                slides_with_index = driver.find_elements(By.CSS_SELECTOR, '.swiper-slide[data-swiper-slide-index]')

                if slides_with_index:
                    # 收集并排序去重后的真实索引
                    index_set = set()
                    for slide in slides_with_index:
                        idx = slide.get_attribute('data-swiper-slide-index')
                        if idx is not None and idx.isdigit():
                            index_set.add(int(idx))
                    sorted_indices = sorted(index_set)

                    print(f"✅ 找到 {len(sorted_indices)} 个真实slide（index范围: {sorted_indices[0] if sorted_indices else 'N/A'}-{sorted_indices[-1] if sorted_indices else 'N/A'}）")

                    # 从每个slide索引中提取图片URL
                    for index in sorted_indices:
                        print(f"🔍 处理slide #{index}...")

                        # 动态定位当前索引的slide
                        try:
                            slide = driver.find_element(By.CSS_SELECTOR, f'.swiper-slide[data-swiper-slide-index="{index}"]')
                        except Exception:
                            print(f"⚠️ slide #{index} 未能定位，跳过。")
                            continue

                        # 在当前slide中查找图片
                        img_url = ImageTools._extract_image_from_slide(slide, index)
                        if img_url and img_url not in unique_urls:
                            unique_urls.add(img_url)
                            img_urls.append(img_url)
                            print(f"📌 slide #{index}图片URL: {img_url}")

                print(f"📊 策略1收集到 {len(img_urls)} 张图片")

            except Exception as e:
                print(f"⚠️ 策略1失败: {str(e)}")

            # 策略2: 查找所有可见的图片元素（备用策略）
            if len(img_urls) == 0:
                print("📍 策略2: 查找所有可见图片元素...")
                try:
                    # 查找多种可能的图片选择器
                    img_selectors = [
                        '.note-slider-img',
                        '.swiper-slide img',
                        '.img-container img',
                        '[class*="slider"] img',
                        '[class*="swiper"] img',
                        'img[src*="sns-webpic"]',  # 小红书图片CDN
                        'img[data-src*="sns-webpic"]'
                    ]

                    for selector in img_selectors:
                        try:
                            images = driver.find_elements(By.CSS_SELECTOR, selector)
                            for img in images:
                                img_url = img.get_attribute('src') or img.get_attribute('data-src') or img.get_attribute('data-original')
                                if img_url and img_url not in unique_urls and 'sns-webpic' in img_url:
                                    unique_urls.add(img_url)
                                    img_urls.append(img_url)
                                    print(f"📌 策略2找到图片: {img_url}")
                        except Exception:
                            continue

                    print(f"📊 策略2额外收集到 {len(img_urls)} 张图片")

                except Exception as e:
                    print(f"⚠️ 策略2失败: {str(e)}")

            if not img_urls:
                print("❌ 所有策略都未找到有效图片")
                print("📄 正在分析页面内容...")
                print(f"页面标题: {driver.title}")
                print(f"当前URL: {driver.current_url}")

                # 检查是否有登录提示或其他阻拦
                try:
                    login_elements = driver.find_elements(By.CSS_SELECTOR, '[class*="login"], [class*="Login"], .sign-in, .signin')
                    if login_elements:
                        print("⚠️ 检测到登录相关元素，可能需要登录")
                except Exception:
                    pass

                # 检查页面中是否有图片相关的元素
                try:
                    all_imgs = driver.find_elements(By.TAG_NAME, 'img')
                    print(f"📊 页面总共有 {len(all_imgs)} 个img元素")

                    # 显示前几个图片的信息
                    for i, img in enumerate(all_imgs[:5]):
                        src = img.get_attribute('src') or img.get_attribute('data-src') or 'No src'
                        print(f"  图片{i+1}: {src[:100]}...")
                except Exception:
                    pass

                page_source = driver.page_source[:2000]
                print(f"页面源代码片段: {page_source}")
                driver.quit()
                return False
                
                # 从每个slide索引中提取图片URL（每次动态重新定位，避免stale）
                img_urls = []
                for index in sorted_indices:
                    print(f"🔍 处理slide #{index}...")
                    
                    # 动态定位当前索引的slide
                    try:
                        slide = driver.find_element(By.CSS_SELECTOR, f'.swiper-slide[data-swiper-slide-index="{index}"]')
                    except Exception as _e:
                        print(f"⚠️ slide #{index} 未能定位（可能已被DOM更新），跳过。")
                        continue
                    
                    # 在当前slide中查找图片
                    img_selectors = [
                        '.note-slider-img',
                        '.img-container img',
                        'img'
                    ]
                    
                    img_url = None
                    for img_sel in img_selectors:
                        try:
                            img_element = slide.find_element(By.CSS_SELECTOR, img_sel)
                            img_url = img_element.get_attribute('src')
                            if not img_url:
                                img_url = img_element.get_attribute('data-src') or img_element.get_attribute('data-original')
                            if img_url:
                                print(f"✅ 在slide #{index}中找到图片: {img_sel}")
                                break
                        except Exception:
                            continue
                    
                    if img_url:
                        img_urls.append(img_url)
                        print(f"📌 slide #{index}图片URL: {img_url}")


            # 智能轮播补齐流程
            print("🔄 启动智能轮播补齐流程...")
            try:
                # 多种方式获取总图片数
                total_count = ImageTools._get_total_image_count(driver)
                print(f"🧮 预估总图片数: {total_count}")

                # 如果已收集的图片数少于预估总数，启动补齐流程
                if total_count is None or len(img_urls) < total_count:
                    print("➡️ 开始轮播补齐...")

                    # 尝试多种轮播触发方式
                    carousel_triggered = ImageTools._trigger_carousel_navigation(driver, img_urls, unique_urls, total_count)

                    if not carousel_triggered:
                        print("🔄 尝试滚动触发懒加载...")
                        ImageTools._trigger_scroll_lazy_loading(driver, img_urls, unique_urls)

                else:
                    print("✅ 已收集到足够数量的图片，跳过补齐流程")

            except Exception as e:
                print(f"⚠️ 轮播补齐流程出现问题: {str(e)}")

            # 最终检查：再次扫描页面确保没有遗漏
            print("🔍 最终扫描确保没有遗漏...")
            try:
                final_images = driver.find_elements(By.CSS_SELECTOR, 'img[src*="sns-webpic"], img[data-src*="sns-webpic"]')
                for img in final_images:
                    img_url = img.get_attribute('src') or img.get_attribute('data-src')
                    if img_url and img_url not in unique_urls:
                        unique_urls.add(img_url)
                        img_urls.append(img_url)
                        print(f"🔍 最终扫描发现遗漏图片: {img_url}")
            except Exception:
                pass

            print(f"📊 去重与补齐后共有 {len(img_urls)} 张图片待下载")

            success_count = 0
            for index, img_url in enumerate(img_urls):
                print(f"\n📥 正在处理第 {index+1}/{len(img_urls)} 张图片...")
                print(f"🔗 图片URL: {img_url}")
                
                try:
                    print("⬇️ 正在下载...")
                    
                    # 设置请求头，模拟浏览器行为
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
                        'Referer': url,
                        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Sec-Fetch-Dest': 'image',
                        'Sec-Fetch-Mode': 'no-cors',
                        'Sec-Fetch-Site': 'cross-site'
                    }
                    
                    response = requests.get(img_url, stream=True, timeout=30, headers=headers)
                    
                    if response.status_code == 200:
                        # 检查内容类型
                        content_type = response.headers.get('content-type', '')
                        if not content_type.startswith('image/'):
                            print(f"⚠️ 响应内容类型不是图片: {content_type}")
                            continue
                        
                        # 从URL/内容类型推断文件扩展名
                        allowed_ext = {"jpg", "jpeg", "png", "webp", "gif"}
                        ext_from_url = 'jpg'
                        last_seg = img_url.split('/')[-1]
                        if '.' in last_seg:
                            ext_from_url = last_seg.split('.')[-1].split('?')[0].split('!')[0].lower()
                        if ext_from_url not in allowed_ext:
                            # 基于内容类型
                            if 'jpeg' in content_type:
                                ext_from_url = 'jpg'
                            elif 'png' in content_type:
                                ext_from_url = 'png'
                            elif 'webp' in content_type:
                                ext_from_url = 'webp'
                            elif 'gif' in content_type:
                                ext_from_url = 'gif'
                            else:
                                ext_from_url = 'jpg'
                        
                        file_path = os.path.join(output_dir, f"image_{index+1}.{ext_from_url}")
                        
                        # 获取文件大小用于显示进度
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded_size = 0
                        
                        with open(file_path, 'wb') as f:
                            for chunk in response.iter_content(1024):
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                                    if total_size > 0:
                                        progress = (downloaded_size / total_size) * 100
                                        print(f"📊 下载进度: {progress:.1f}%", end='\r')
                        
                        print(f"\n✅ 图片 #{index+1} 下载成功！保存到: {file_path}")
                        try:
                            print(f"✂️ 正在裁剪图片: {file_path}")
                            img = Image.open(file_path)
                            width, height = img.size
                            pixels_to_cut = 50
                            if height > pixels_to_cut:
                                crop_area = (0, 0, width, height - pixels_to_cut)
                                img_cropped = img.crop(crop_area)
                                img.close()  # Explicitly close the image file
                                img_cropped.save(file_path)  # Now save the cropped image
                                print(f"✅ 图片裁剪成功")
                            else:
                                img.close()  # Close the image even if not cropped
                                print(f"⚠️ 图片高度 ({height}px) 小于裁剪像素 ({pixels_to_cut}px)，跳过裁剪。")
                        except Exception as crop_error:
                            print(f"❌ 裁剪图片时发生错误: {str(crop_error)}")
                        success_count += 1
                    else:
                        print(f"❌ 下载失败，HTTP状态码: {response.status_code}")
                        print(f"📄 响应内容: {response.text[:200]}")
                        
                except Exception as download_error:
                    print(f"❌ 下载图片时发生错误: {str(download_error)}")
            
            driver.quit()
            print(f"\n🎉 任务完成！成功下载 {success_count}/{len(img_urls)} 张图片")
            print(f"📂 所有图片已保存到: {output_dir}")
            
            # 如果下载成功且有图片，则进行图片识别并重命名文件夹
            if success_count > 0 and img_urls:
                print("\n🔍 开始分析第一张图片生成暧昧文件夹名...")
                try:
                    # 加载配置获取API密钥
                    config = ImageTools._load_config()
                    api_key = config.get("siliconflow", {}).get("api_key")
                    
                    if api_key:
                        # 使用第一张图片的URL进行识别
                        first_image_url = img_urls[0]
                        keywords = ImageTools.get_image_analysis_keywords(first_image_url, api_key)
                        
                        if keywords and not keywords.startswith("❌"):
                            # 生成暧昧文件夹名
                            romantic_name = ImageTools.generate_romantic_folder_name(keywords)
                            
                            # 构建新的文件夹路径
                            parent_dir = os.path.dirname(output_dir)
                            new_output_dir = os.path.join(parent_dir, romantic_name)
                            
                            # 重命名文件夹
                            if os.path.exists(output_dir) and not os.path.exists(new_output_dir):
                                os.rename(output_dir, new_output_dir)
                                print(f"✨ 文件夹已重命名为: {new_output_dir}")
                                
                                # 更新返回信息中的路径
                                output_dir = new_output_dir
                                
                                # 保存AI描述到文本文件
                                try:
                                    # 使用清理后的文件夹名作为文本文件名
                                    text_filename = f"{romantic_name}.txt"
                                    text_file_path = os.path.join(output_dir, text_filename)
                                    
                                    with open(text_file_path, 'w', encoding='utf-8') as f:
                                        f.write(f"AI图片分析结果\n")
                                        f.write(f"=" * 30 + "\n\n")
                                        f.write(f"标题: {romantic_name}\n\n")
                                        f.write(f"AI描述:\n{keywords}\n\n")
                                        f.write(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                                    
                                    print(f"📄 AI描述已保存到: {text_file_path}")
                                except Exception as text_error:
                                    print(f"⚠️ 保存AI描述文件失败: {text_error}")
                            else:
                                print(f"⚠️ 文件夹重命名失败，目标路径可能已存在: {new_output_dir}")
                        else:
                            print(f"⚠️ 图片识别失败: {keywords}")
                    else:
                        print("⚠️ 未配置API密钥，跳过图片识别和文件夹重命名")
                        
                except Exception as e:
                    print(f"⚠️ 图片识别或文件夹重命名过程中出现错误: {e}")
            
            print(f"📂 最终保存路径: {output_dir}")
            return success_count > 0
            
        except Exception as e:
            print(f"💥 处理URL时发生严重错误: {str(e)}")
            if 'driver' in locals() and driver:
                print("🔧 正在清理浏览器资源...")
                driver.quit()
            return False

    @staticmethod
    def cut_bottom(local_path: str, pixels: int = 50) -> bool:
        try:
            processed_files = []
            # 创建一个新的文件夹来存放处理后的图片
            output_dir = os.path.join(local_path, "processed")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            for filename in os.listdir(local_path):
                if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                    file_path = os.path.join(local_path, filename)
                    with Image.open(file_path) as img:
                        # 裁剪图片
                        width, height = img.size
                        crop_area = (0, 0, width, height - pixels)
                        img_cropped = img.crop(crop_area)

                        # 获取新的文件名
                        current_date = datetime.now().strftime("%Y%m%d")
                        original_name = os.path.splitext(filename)[0][:8]
                        file_extension = os.path.splitext(filename)[1]
                        new_height = height - pixels
                        new_filename = f"{current_date}_{original_name}_{new_height}px_{len(processed_files) + 1}{file_extension}"

                        # 保存新图片到processed文件夹
                        new_file_path = os.path.join(output_dir, new_filename)
                        img_cropped.save(new_file_path)
                        processed_files.append(new_filename)

            print(f"成功处理的文件: {', '.join(processed_files)}")
            print(f"处理后的文件保存在: {output_dir}")
            return True
        except Exception as e:
            print(f"处理图片时发生错误: {str(e)}")
            return False

    @staticmethod
    def get_image_analysis_keywords(image_url: str, api_key: str) -> str:
        """
        Analyzes an image from a URL using the SiliconFlow API and returns descriptive keywords.

        :param image_url: The URL of the image to analyze.
        :param api_key: Your SiliconFlow API key.
        :return: A string of keywords describing the image, or an error message.
        """
        try:
            print(f"🖼️ Analyzing image from URL: {image_url}")

            # 1. Download the image
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = response.content

            # 2. Encode the image in base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "Qwen/Qwen2.5-VL-32B-Instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请分析这张图片，用中文给出文章标题描述，要求：1.描述画面主要内容 2.适合用作图集名称 3.带有一点暧昧色彩。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 200
            }

            # 3. Call the SiliconFlow API
            print("🧠 使用GLM-4.1V-9B-Thinking模型分析图片...")
            api_url = "https://api.siliconflow.cn/v1/chat/completions"
            response = requests.post(api_url, headers=headers, json=payload)
            
            # 调试响应
            print(f"📊 响应状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ 响应内容: {response.text}")
                
            response.raise_for_status()

            # 4. Extract the keywords from the response
            result = response.json()
            keywords = result['choices'][0]['message']['content']
            
            print(f"✅ 图片分析成功。关键词: {keywords}")
            return keywords

        except requests.exceptions.RequestException as e:
            error_message = f"❌ 图片下载或处理失败: {e}"
            print(error_message)
            return error_message
        except Exception as e:
            error_message = f"❌ 发生未知错误: {e}"
            print(error_message)
            return error_message

    @staticmethod
    def generate_romantic_folder_name(keywords: str) -> str:
        """
        根据图片识别的关键词生成一个带有暧昧色彩的文件夹名称
        
        :param keywords: 图片识别的关键词
        :return: 生成的暧昧文件夹名称
        """
        try:
            import re
            
            # 尝试从AI返回中提取标题
            # 查找被引号包围的标题
            title_patterns = [
                r'[*"「]([^*"」]{8,})[*"」]',  # 匹配**"标题"**或「标题」
                r'标题[：:](.{8,}?)(?:\n|\*|$)',  # 匹配"标题："后的内容
                r'[：:](.{8,30}?)(?:\n|$)',  # 匹配冒号后的内容
            ]
            
            clean_name = None
            for pattern in title_patterns:
                match = re.search(pattern, keywords)
                if match:
                    clean_name = match.group(1).strip()
                    break
            
            # 如果没有匹配到标题，使用前面的部分
            if not clean_name:
                # 截取第一行或前50个字符
                first_line = keywords.split('\n')[0]
                clean_name = first_line[:50] if len(first_line) > 50 else first_line
            
            # 清理文件名不能包含的特殊字符
            clean_name = re.sub(r'[<>:"/\\|?*#]', '', clean_name)
            clean_name = re.sub(r'[*]{2,}', '', clean_name)  # 移除多个星号
            clean_name = clean_name.strip()
            
            # 确保名称不为空且合理长度
            if not clean_name or len(clean_name) < 3:
                clean_name = f"AI识别图片_{datetime.now().strftime('%H%M%S')}"
            elif len(clean_name) > 50:
                clean_name = clean_name[:50]
            
            print(f"🌟 生成文件夹名: {clean_name}")
            return clean_name
            
        except Exception as e:
            print(f"❌ 生成文件夹名失败: {e}")
            # 如果生成失败，返回一个默认的浪漫名称
            return f"神秘的邂逅_{datetime.now().strftime('%H%M%S')}"
    
    @staticmethod
    def _load_config(config_path: str = "config.json") -> dict:
        """
        加载配置文件
        
        :param config_path: 配置文件路径
        :return: 配置字典
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config
            else:
                print(f"⚠️ 配置文件不存在: {config_path}")
                return {}
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            return {}