# 完善代码 18998
import os
from datetime import datetime
from PIL import Image
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class ImageTools:
    @staticmethod
    def get_img_via_url(url: str) -> bool:
        try:
            print(f"🚀 开始处理URL: {url}")
            
            # 设置Chrome选项
            print("⚙️ 正在配置浏览器选项...")
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36")

            # 初始化WebDriver
            print("🌐 正在启动浏览器...")
            driver = webdriver.Chrome(options=chrome_options)
            
            print("📡 正在访问页面...")
            driver.get(url)
            
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
            
            # 使用data-swiper-slide-index来准确定位真实的slide，避免duplicate干扰
            print("🎯 基于data-swiper-slide-index查找真实slide...")
            
            try:
                # 先找到所有有data-swiper-slide-index的slide
                slides_with_index = wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, '.swiper-slide[data-swiper-slide-index]')
                ))
                
                # 收集并排序去重后的真实索引，避免缓存DOM元素引用
                index_set = set()
                for slide in slides_with_index:
                    idx = slide.get_attribute('data-swiper-slide-index')
                    if idx is not None and idx.isdigit():
                        index_set.add(int(idx))
                sorted_indices = sorted(index_set)
                
                print(f"✅ 找到 {len(sorted_indices)} 个真实slide（index范围: {sorted_indices[0] if sorted_indices else 'N/A'}-{sorted_indices[-1] if sorted_indices else 'N/A'}）")
                
                if not sorted_indices:
                    print("❌ 未找到有效的slide元素")
                    print("📄 正在分析页面内容...")
                    print(f"页面标题: {driver.title}")
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
                    else:
                        print(f"⚠️ slide #{index}未找到有效图片URL")
                
                print(f"🎯 成功收集到 {len(img_urls)} 张图片URL")
                
                # 先按顺序去重，并初始化 unique_urls，防止后续补齐逻辑引用未定义变量
                seen = set()
                deduped = []
                for u in img_urls:
                    if u and u not in seen:
                        seen.add(u)
                        deduped.append(u)
                img_urls = deduped
                unique_urls = set(img_urls)
                print(f"🧹 基于slide-index初步去重后剩余 {len(img_urls)} 张图片")
                
            except Exception as e:
                print(f"❌ 基于slide-index查找失败: {str(e)}")
                print("📄 正在分析页面内容...")
                print(f"页面标题: {driver.title}")
                page_source = driver.page_source[:2000]
                print(f"页面源代码片段: {page_source}")
                driver.quit()
                return False

            # 若仍然只有1张，尝试点击轮播右箭头以触发懒加载，补齐图片URL
            try:
                # 读取分页总数（如 1/2）
                total_count = None
                try:
                    frac_el = driver.find_element(By.CSS_SELECTOR, '.fraction')
                    if frac_el and '/' in frac_el.text:
                        parts = frac_el.text.strip().split('/')
                        if len(parts) == 2 and parts[1].isdigit():
                            total_count = int(parts[1])
                            print(f"🧮 分页指示器显示共有 {total_count} 张图")
                except Exception:
                    pass

                if total_count is not None and len(img_urls) < total_count:
                    print("➡️ 启动轮播补齐流程...")
                    # 找到右箭头
                    next_btn = None
                    for sel in ['.arrow-controller.right .btn-wrapper', '.arrow-controller.right']:
                        try:
                            next_btn = driver.find_element(By.CSS_SELECTOR, sel)
                            if next_btn:
                                print(f"✅ 找到轮播右箭头: {sel}")
                                break
                        except Exception:
                            continue
                    # 循环点击，采集新URL
                    if next_btn:
                        max_steps = min(total_count * 2, 10)
                        for step in range(max_steps):
                            try:
                                driver.execute_script("arguments[0].click();", next_btn)
                            except Exception:
                                try:
                                    next_btn.click()
                                except Exception:
                                    print("⚠️ 右箭头点击失败，结束补齐流程")
                                    break
                            time.sleep(0.8)
                            try:
                                active_img = driver.find_element(By.CSS_SELECTOR, '.swiper-slide-active img.note-slider-img')
                            except Exception:
                                try:
                                    active_img = driver.find_element(By.CSS_SELECTOR, '.swiper-slide-active img')
                                except Exception:
                                    active_img = None
                            if active_img:
                                cur = active_img.get_attribute('src') or active_img.get_attribute('data-src') or active_img.get_attribute('data-original')
                                if cur and cur not in unique_urls:
                                    unique_urls.add(cur)
                                    img_urls.append(cur)
                                    print(f"➕ 轮播新增图片URL: {cur}")
                            if total_count and len(img_urls) >= total_count:
                                print("✅ 已采集到全部分页图片URL")
                                break
            except Exception as car_err:
                print(f"⚠️ 轮播补齐流程出现问题: {car_err}")

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