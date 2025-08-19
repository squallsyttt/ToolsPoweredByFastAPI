# 配置文件说明

## 概述

本项目使用 `config.json` 文件来统一管理所有配置参数，包括API密钥、模型参数、故事生成参数等。

## 配置文件结构

### 完整配置示例

```json
{
  "siliconflow": {
    "api_key": "",
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

## 配置参数详解

### siliconflow 硅基流动API配置

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `api_key` | string | 是 | "" | 硅基流动API密钥 |
| `base_url` | string | 否 | "https://api.siliconflow.cn/v1/chat/completions" | API基础URL |
| `default_model` | string | 否 | "Qwen/Qwen2.5-72B-Instruct" | 默认使用的模型 |
| `timeout` | number | 否 | 60 | 请求超时时间（秒） |
| `max_tokens` | number | 否 | 2000 | 最大生成token数 |
| `temperature` | number | 否 | 0.8 | 控制生成的随机性（0-1） |
| `top_p` | number | 否 | 0.9 | 核心采样参数（0-1） |

### story 故事生成配置

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `target_length` | number | 否 | 1200 | 目标故事字数 |
| `keyword_count_min` | number | 否 | 3 | 最少选择关键词数量 |
| `keyword_count_max` | number | 否 | 5 | 最多选择关键词数量 |
| `output_dir` | string | 否 | "resource" | 故事保存目录 |

## 配置文件管理

### 1. 初始设置

```bash
# 复制配置模板
cp config.json.example config.json

# 编辑配置文件
nano config.json  # 或使用你喜欢的编辑器
```

### 2. 安全注意事项

- ⚠️ **不要提交包含真实API密钥的config.json到版本控制系统**
- 项目已在.gitignore中排除config.json文件
- 如需分享配置，请使用config.json.example模板

### 3. 环境变量支持

除了配置文件，也可以使用环境变量：

```bash
export SILICONFLOW_API_KEY="your-api-key-here"
```

配置文件优先级高于环境变量。

## 配置验证

启动服务时会自动验证配置：

- ✅ 配置文件加载成功
- ⚠️ 配置文件不存在或格式错误时使用默认配置
- ❌ API密钥未配置时会显示警告

## 高级配置

### 模型选择

支持的模型列表（请参考硅基流动官方文档）：
- `Qwen/Qwen2.5-72B-Instruct` (推荐)
- `Qwen/Qwen2.5-32B-Instruct`
- `Qwen/Qwen2.5-14B-Instruct`
- `Qwen/Qwen2.5-7B-Instruct`

### 生成参数调优

- **temperature**: 值越高生成越有创意，但可能不够连贯
- **top_p**: 控制词汇选择的多样性
- **max_tokens**: 控制最大输出长度

### 自定义输出目录

可以设置自定义的故事保存路径：

```json
{
  "story": {
    "output_dir": "/path/to/your/stories"
  }
}
```

## 故障排除

### 常见问题

1. **API密钥错误**
   ```
   ❌ API请求失败: 401 Unauthorized
   ```
   解决：检查config.json中的api_key是否正确

2. **配置文件格式错误**
   ```
   ❌ 配置文件加载失败: JSON decode error
   ```
   解决：检查JSON格式是否正确，可使用JSON验证工具

3. **网络连接问题**
   ```
   ❌ API请求失败: Connection timeout
   ```
   解决：检查网络连接，可适当增加timeout值

### 重置配置

如需重置配置，删除config.json文件重新复制模板：

```bash
rm config.json
cp config.json.example config.json
```