#!/usr/bin/env python3
"""
浏览器诊断工具
用于检查Chrome浏览器和ChromeDriver的版本匹配情况
"""

import subprocess
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time


def get_chrome_version():
    """获取Chrome浏览器版本"""
    try:
        # macOS
        result = subprocess.run([
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    try:
        # 尝试其他路径
        result = subprocess.run(['google-chrome', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    try:
        result = subprocess.run(['chromium-browser', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    return "未找到Chrome浏览器"


def get_chromedriver_version():
    """获取ChromeDriver版本"""
    try:
        result = subprocess.run(['chromedriver', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    return "未找到ChromeDriver"


def test_browser_startup():
    """测试浏览器启动速度"""
    print("🧪 测试浏览器启动速度...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    try:
        start_time = time.time()
        driver = webdriver.Chrome(options=chrome_options)
        startup_time = time.time() - start_time
        
        print(f"✅ 浏览器启动成功，耗时: {startup_time:.2f}秒")
        
        # 测试页面访问
        start_time = time.time()
        driver.get("https://www.baidu.com")
        page_load_time = time.time() - start_time
        print(f"✅ 页面访问成功，耗时: {page_load_time:.2f}秒")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ 浏览器测试失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("🔍 Chrome浏览器诊断工具")
    print("=" * 50)
    
    # 检查Chrome版本
    chrome_version = get_chrome_version()
    print(f"Chrome版本: {chrome_version}")
    
    # 检查ChromeDriver版本
    chromedriver_version = get_chromedriver_version()
    print(f"ChromeDriver版本: {chromedriver_version}")
    
    print("\n" + "=" * 50)
    
    # 版本匹配检查
    if "未找到" in chrome_version or "未找到" in chromedriver_version:
        print("❌ 检测到缺失组件，请安装Chrome浏览器和ChromeDriver")
        print("\n💡 安装建议:")
        print("1. 安装Chrome浏览器: https://www.google.com/chrome/")
        print("2. 安装ChromeDriver: brew install chromedriver (macOS)")
        print("   或从 https://chromedriver.chromium.org/ 下载")
    else:
        # 提取版本号进行比较
        try:
            chrome_major = chrome_version.split()[2].split('.')[0]
            driver_major = chromedriver_version.split()[1].split('.')[0]
            
            if chrome_major == driver_major:
                print("✅ Chrome和ChromeDriver版本匹配")
            else:
                print(f"⚠️ 版本不匹配! Chrome主版本: {chrome_major}, ChromeDriver主版本: {driver_major}")
                print("💡 建议更新ChromeDriver到匹配版本")
        except:
            print("⚠️ 无法解析版本号，请手动检查版本匹配")
    
    print("\n" + "=" * 50)
    
    # 测试浏览器启动
    test_browser_startup()
    
    print("\n🎯 诊断完成!")


if __name__ == "__main__":
    main()
