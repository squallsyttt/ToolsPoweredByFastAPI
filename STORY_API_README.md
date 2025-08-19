# 硅基流动API故事生成功能使用说明

## 功能概述

本项目已成功集成硅基流动API，提供以下功能：

1. **对话接口测试** - 测试硅基流动API的基本对话功能
2. **每日暧昧小故事生成** - 基于随机词库生成可配置字数的暧昧小故事
3. **文件自动保存** - 生成的故事自动保存到配置目录下按日期分类的文件夹中
4. **配置文件管理** - 统一的配置文件管理API密钥和各项参数

## 配置文件设置

### 1. 复制配置模板

```bash
cp config.json.example config.json
```

### 2. 编辑配置文件

在 `config.json` 中设置你的API密钥和其他参数：

```json
{
  "siliconflow": {
    "api_key": "YOUR_SILICONFLOW_API_KEY_HERE",
    "base_url": "https://api.siliconflow.cn/v1/chat/completions",
    "default_model": "Qwen/Qwen2.5-72B-Instruct",
    "timeout": 60,
    "max_tokens": 2000,
    "temperature": 0.8,
    "top_p": 0.9
  },
  "story": {
    "target_length": 1200,
    "keyword_count_min": 3,
    "keyword_count_max": 5,
    "output_dir": "resource"
  }
}
```

**配置说明：**
- `api_key`: 硅基流动API密钥（必需）
- `base_url`: API基础URL
- `default_model`: 默认使用的模型
- `timeout`: 请求超时时间（秒）
- `max_tokens`: 最大生成token数
- `temperature`: 控制生成的随机性（0-1）
- `top_p`: 核心采样参数（0-1）
- `target_length`: 目标故事字数
- `keyword_count_min/max`: 随机选择关键词的数量范围
- `output_dir`: 故事保存目录

## API端点

### 1. 测试硅基流动API对话接口

```
GET /tools/testSiliconFlowAPI
```

**参数：**
- `prompt` (可选): 测试提示词，默认为"你好，请介绍一下你自己"

**示例：**
```
GET http://127.0.0.1:8000/tools/testSiliconFlowAPI?prompt=你好
```

### 2. 生成每日暧昧小故事

```
GET /tools/generateDailyStory
```

**参数：** 无需参数，所有配置通过config.json获取

**示例：**
```
GET http://127.0.0.1:8000/tools/generateDailyStory
```

## 使用步骤

### 1. 获取API密钥

1. 访问 [硅基流动官网](https://docs.siliconflow.cn/)
2. 注册账号并获取API密钥

### 2. 配置API密钥

编辑 `config.json` 文件，填入你的API密钥：
```json
{
  "siliconflow": {
    "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  }
}
```

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://127.0.0.1:8000` 启动

### 4. 测试API

使用提供的 `test_main.http` 文件中的测试用例直接测试，无需额外配置API密钥。

### 4. 查看生成的故事

生成的故事将保存在以下路径：
```
resource/story_YYYYMMDD/story_YYYYMMDD_HHMMSS_keywords.txt
```

## 词库内容

当前内置词库包含以下类型的词汇：
- **环境类**: 月光、微风、花香、夜晚、咖啡厅、图书馆等
- **情感类**: 温柔、眼眸、拥抱、心跳、脸红等  
- **场景类**: 青春、校园、制服、课堂、操场等
- **动作类**: 偶遇、重逢、告白、心动、甜蜜等

## 自定义扩展

如需添加新的词汇到词库，可以通过 `StoryTools` 类的 `add_words_to_bank()` 方法进行扩展。

## 注意事项

1. 确保API密钥有效且有足够的调用额度
2. 生成的故事内容健康向上，符合平台规范
3. 每次生成的故事都会自动保存，避免重复生成相同内容
4. API调用可能需要一定时间，请耐心等待

## 故事生成逻辑

1. 从词库中随机选择3-5个关键词
2. 构建包含这些关键词的详细提示词
3. 调用硅基流动API生成约1200字的故事
4. 自动保存到按日期分类的文件夹中

生成的故事将包含完整的元数据信息，包括生成时间、关键词、字数等。