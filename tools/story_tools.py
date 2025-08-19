import os
import json
import random
from datetime import datetime
import requests
from typing import List, Dict


class StoryTools:
    """故事生成工具类，用于调用硅基流动API生成暧昧小故事"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化故事工具
        
        :param config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.api_key = self.config.get("siliconflow", {}).get("api_key")
        self.api_url = self.config.get("siliconflow", {}).get("base_url", "https://api.siliconflow.cn/v1/chat/completions")
        self.default_model = self.config.get("siliconflow", {}).get("default_model", "Qwen/Qwen2.5-72B-Instruct")
        self.timeout = self.config.get("siliconflow", {}).get("timeout", 60)
        self.max_tokens = self.config.get("siliconflow", {}).get("max_tokens", 2000)
        self.temperature = self.config.get("siliconflow", {}).get("temperature", 0.8)
        self.top_p = self.config.get("siliconflow", {}).get("top_p", 0.9)
        
        # 故事配置
        self.target_length = self.config.get("story", {}).get("target_length", 1200)
        self.keyword_count_min = self.config.get("story", {}).get("keyword_count_min", 3)
        self.keyword_count_max = self.config.get("story", {}).get("keyword_count_max", 5)
        self.output_dir = self.config.get("story", {}).get("output_dir", "resource")
        # 检查API key是否配置
        if not self.api_key:
            print("⚠️ 警告：未配置硅基流动API密钥，请在config.json中设置api_key")
        
        self.word_bank = [
            # 浪漫场景
            "月光", "微风", "花香", "夜晚", "咖啡厅", "图书馆", "雨夜", "阳台", 
            "海边", "星空", "公园", "长椅", "秋千", "樱花", "夕阳", "街角", "小巷",
            "酒店", "民宿", "温泉", "海滩", "游泳池", "私人影院", "按摩店", "SPA",
            
            # 青春校园
            "青春", "校园", "制服", "课堂", "操场", "天台", "楼梯", "走廊",
            "电梯", "宿舍", "更衣室", "体育馆", "音乐教室", "实验室", "保健室",
            
            # 暧昧动作
            "温柔", "眼眸", "拥抱", "手牵手", "心跳", "脸红", "亲吻", "抚摸",
            "依偎", "拉手", "贴近", "耳语", "注视", "触碰", "轻抚", "拥吻",
            "紧贴", "相视", "轻吻", "搂抱", "缠绵", "拥紧",
            
            # 情感状态
            "偶遇", "重逢", "告白", "心动", "甜蜜", "暧昧", "思念", "等待",
            "迷恋", "沉醉", "陶醉", "痴迷", "渴望", "悸动", "冲动", "欲望",
            "诱惑", "魅惑", "勾引", "撩拨", "挑逗", "暗示", "暧昧", "纠缠",
            
            # 身体部位
            "红唇", "香肩", "纤腰", "玉腿", "酥胸", "香颈", "柳腰", "凤眸",
            "素手", "玉足", "香唇", "粉颊", "皓齿", "柔荑",
            
            # 服装饰品
            "睡衣", "内衣", "丝袜", "高跟鞋", "薄纱", "蕾丝", "吊带", "短裙",
            "紧身", "透明", "性感", "诱人", "撩人", "妩媚",
            
            # 场景道具
            "床榻", "沙发", "浴室", "镜子", "窗帘", "烛光", "香薰", "红酒",
            "玫瑰", "巧克力", "项链", "戒指", "丝巾", "按摩油",
            
            # 时间氛围
            "深夜", "黎明", "黄昏", "午后", "静夜", "晨曦", "薄暮", "夜色",
            "灯火阑珊", "月黑风高", "春宵", "良夜", "孤夜"
        ]
    
    def _load_config(self, config_path: str) -> Dict:
        """
        加载配置文件
        
        :param config_path: 配置文件路径
        :return: 配置字典
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ 配置文件加载成功: {config_path}")
                return config
            else:
                print(f"⚠️ 配置文件不存在: {config_path}，使用默认配置")
                return {}
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}，使用默认配置")
            return {}
    
    def get_random_prompt(self) -> str:
        """
        从词库中随机选择几个词生成提示词
        
        :return: 生成的提示词
        """
        selected_words = random.sample(self.word_bank, random.randint(self.keyword_count_min, self.keyword_count_max))
        keywords_str = ', '.join(selected_words)
        base_prompt = f"请以「{keywords_str}」为关键词，创作一个{self.target_length}字左右的暧昧擦边小故事。故事要求：1. 情节自然流畅，有起承转合 2. 人物描写细腻，心理活动丰富 3. 营造浪漫暧昧的氛围 4. 内容健康向上，但充满张力 5. 文笔优美，富有感染力"
        return base_prompt
    
    def call_siliconflow_api(self, prompt: str, model: str = None) -> str:
        """
        调用硅基流动API生成文本
        
        :param prompt: 输入提示词
        :param model: 使用的模型名称，如果不指定则使用配置中的默认模型
        :return: 生成的故事内容
        """
        try:
            if not self.api_key:
                return "❌ API密钥未配置，请在config.json中设置api_key"
            
            model = model or self.default_model
            print(f"🤖 正在调用硅基流动API...")
            print(f"📝 使用模型: {model}")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            story_content = result['choices'][0]['message']['content']
            
            print(f"✅ API调用成功，生成了{len(story_content)}字的故事")
            return story_content
            
        except requests.exceptions.RequestException as e:
            error_message = f"❌ API请求失败: {e}"
            print(error_message)
            return error_message
        except Exception as e:
            error_message = f"❌ 发生未知错误: {e}"
            print(error_message)
            return error_message
    
    def save_story_to_file(self, story_content: str, keywords: List[str] = None) -> str:
        """
        将故事保存到文件
        
        :param story_content: 故事内容
        :param keywords: 关键词列表
        :return: 保存的文件路径
        """
        try:
            # 创建以当前日期命名的文件夹
            current_date = datetime.now().strftime("%Y%m%d")
            output_dir = os.path.join(self.output_dir, f"story_{current_date}")
            
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"📁 创建文件夹: {output_dir}")
            
            # 生成文件名
            current_time = datetime.now().strftime("%H%M%S")
            keywords_str = "_".join(keywords) if keywords else "random"
            filename = f"story_{current_date}_{current_time}_{keywords_str[:30]}.txt"
            filepath = os.path.join(output_dir, filename)
            
            # 准备文件内容
            file_content = f"""故事生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
关键词: {', '.join(keywords) if keywords else '随机生成'}
字数: {len(story_content)}
目标字数: {self.target_length}

================== 故事内容 ==================

{story_content}

================== 故事结束 ==================
"""
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            print(f"💾 故事已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            error_message = f"❌ 保存文件失败: {e}"
            print(error_message)
            return error_message
    
    def generate_daily_story(self) -> Dict[str, str]:
        """
        生成每日暧昧小故事
        
        :return: 包含故事信息的字典
        """
        try:
            print("🌟 开始生成每日暧昧小故事...")
            
            # 生成随机提示词
            prompt = self.get_random_prompt()
            keywords = [word for word in self.word_bank if word in prompt]
            
            print(f"🎲 随机关键词: {', '.join(keywords)}")
            print(f"📝 生成的提示词: {prompt}")
            
            # 调用API生成故事
            story_content = self.call_siliconflow_api(prompt)
            
            if story_content and not story_content.startswith("❌"):
                # 保存故事到文件
                filepath = self.save_story_to_file(story_content, keywords)
                
                return {
                    "status": "success",
                    "story_content": story_content,
                    "keywords": keywords,
                    "filepath": filepath,
                    "word_count": len(story_content),
                    "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                return {
                    "status": "error",
                    "error_message": story_content,
                    "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"生成故事时发生错误: {e}",
                "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def add_words_to_bank(self, new_words: List[str]) -> bool:
        """
        向词库添加新词汇
        
        :param new_words: 新词汇列表
        :return: 是否添加成功
        """
        try:
            for word in new_words:
                if word not in self.word_bank:
                    self.word_bank.append(word)
            print(f"✅ 成功添加 {len(new_words)} 个新词汇到词库")
            return True
        except Exception as e:
            print(f"❌ 添加词汇失败: {e}")
            return False
    
    def get_word_bank(self) -> List[str]:
        """
        获取当前词库
        
        :return: 词库列表
        """
        return self.word_bank.copy()