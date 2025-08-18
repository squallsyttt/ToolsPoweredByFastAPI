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
import base64
import io


class ImageTools:
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
            print(f"🚀 开始处理URL: {url}")
            
            # 设置Chrome选项
            print("⚙️ 正在配置浏览器选项...")
            chrome_options = Options()

            # 基础无头模式配置
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            # 性能优化参数
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

            # 窗口大小设置
            chrome_options.add_argument("--window-size=1920,1080")

            # 更新User-Agent到较新版本
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            # 设置页面加载策略
            chrome_options.page_load_strategy = 'eager'  # 不等待所有资源加载完成

            # 禁用图片加载以提升速度（如果不需要图片预览的话）
            # chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})

            # 初始化WebDriver
            print("🌐 正在启动浏览器...")
            try:
                # 设置启动超时时间
                import signal
                def timeout_handler(signum, frame):
                    raise TimeoutError("浏览器启动超时")

                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(30)  # 30秒超时

                driver = webdriver.Chrome(options=chrome_options)
                signal.alarm(0)  # 取消超时
                print("✅ 浏览器启动成功")

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

                # 检查是否被重定向到登录页面
                current_url = driver.current_url
                if 'login' in current_url.lower() or 'signin' in current_url.lower():
                    print(f"⚠️ 页面被重定向到登录页面: {current_url}")
                    print("💡 建议：")
                    print("   1. 检查URL中的token是否有效")
                    print("   2. 尝试在浏览器中手动访问该URL")
                    print("   3. 可能需要更新token或使用其他访问方式")
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
                "model": "Qwen/Qwen-VL-Max",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please analyze this image and provide a list of descriptive keywords, separated by commas."
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
                "max_tokens": 300
            }

            # 3. Call the SiliconFlow API
            print("🧠 Calling SiliconFlow API for image analysis...")
            api_url = "https://api.siliconflow.cn/v1/chat/completions"
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()

            # 4. Extract the keywords from the response
            result = response.json()
            keywords = result['choices'][0]['message']['content']
            
            print(f"✅ Analysis successful. Keywords: {keywords}")
            return keywords

        except requests.exceptions.RequestException as e:
            error_message = f"❌ Error downloading or processing the image: {e}"
            print(error_message)
            return error_message
        except Exception as e:
            error_message = f"❌ An unexpected error occurred: {e}"
            print(error_message)
            return error_message