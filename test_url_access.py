#!/usr/bin/env python3
"""
测试小红书URL访问情况
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def test_url_access(url):
    """测试URL访问情况"""
    print(f"🧪 测试URL访问: {url}")
    
    # 设置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        print("📡 正在访问页面...")
        driver.get(url)
        time.sleep(3)
        
        print(f"📄 页面标题: {driver.title}")
        print(f"🔗 当前URL: {driver.current_url}")
        
        # 检查是否重定向到登录页面
        if 'login' in driver.current_url.lower():
            print("❌ 页面被重定向到登录页面")
            return False
        
        # 检查页面中的关键元素
        try:
            swiper_elements = driver.find_elements_by_css_selector('.swiper-slide, [class*="swiper"]')
            print(f"🎠 找到 {len(swiper_elements)} 个轮播相关元素")
            
            img_elements = driver.find_elements_by_tag_name('img')
            print(f"🖼️ 找到 {len(img_elements)} 个图片元素")
            
            # 检查是否有小红书图片CDN的图片
            xhs_images = driver.find_elements_by_css_selector('img[src*="sns-webpic"], img[data-src*="sns-webpic"]')
            print(f"📸 找到 {len(xhs_images)} 个小红书CDN图片")
            
            if xhs_images:
                print("✅ 页面包含小红书图片内容")
                for i, img in enumerate(xhs_images[:3]):
                    src = img.get_attribute('src') or img.get_attribute('data-src')
                    print(f"  图片{i+1}: {src[:80]}...")
                return True
            else:
                print("⚠️ 页面不包含小红书图片内容")
                return False
                
        except Exception as e:
            print(f"❌ 检查页面元素时出错: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ 访问页面失败: {str(e)}")
        return False
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    # 测试URL
    test_url = "https://www.xiaohongshu.com/explore/68a0bc0e000000001d01f7cd?xsec_token=AB0pzB77ZydHAwaY50Jf7mCU250_TDRFJikRDqXIBD9Ik=&xsec_source=pc_collect"
    
    result = test_url_access(test_url)
    print(f"\n🎯 测试结果: {'成功' if result else '失败'}")
    
    if not result:
        print("\n💡 建议解决方案:")
        print("1. 检查URL中的token是否有效")
        print("2. 尝试获取新的访问链接")
        print("3. 考虑使用登录后的session")
        print("4. 检查是否触发了反爬虫机制")
