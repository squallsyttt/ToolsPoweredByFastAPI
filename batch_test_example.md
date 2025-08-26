# 批量处理功能使用示例

## 🎯 新功能特点

### ✅ 已实现的批量功能：
1. **单接口批量处理**：一个接口同时处理多个URL
2. **智能Cookie管理**：15分钟内复用同一Cookie，高效批处理
3. **串行处理**：按顺序处理每个URL，保证稳定性
4. **详细结果反馈**：每个URL的处理状态和结果
5. **错误容忍**：某个URL失败不影响其他URL的处理

### 📋 参数说明：
- `urls`: 小红书链接（单个或多个URL用逗号分隔）
- `headless`: 是否无头浏览器模式（默认true，后台运行）
- `max_concurrent`: 最大并发数（默认1，串行处理）

## 📝 使用示例

### 1. 单个URL处理
```http
GET http://127.0.0.1:8000/tools/getImgViaPlaywright?urls=https://www.xiaohongshu.com/explore/6724e85a000000001b0138c8
```

### 2. 批量处理（2个URL）
```http
GET http://127.0.0.1:8000/tools/getImgViaPlaywright?urls=https://www.xiaohongshu.com/explore/6724e85a000000001b0138c8,https://www.xiaohongshu.com/explore/68a9d11e000000001d0151a3
```

### 3. 批量处理（3个URL）
```http
GET http://127.0.0.1:8000/tools/getImgViaPlaywright?urls=https://www.xiaohongshu.com/explore/6724e85a000000001b0138c8,https://www.xiaohongshu.com/explore/68a9d11e000000001d0151a3,https://www.xiaohongshu.com/explore/68a289b1000000001c034a5f
```

## 📊 返回结果格式

```json
{
  "status": "completed",
  "message": "批量处理完成，成功2个，失败1个",
  "summary": {
    "total_urls": 3,
    "success_count": 2,
    "error_count": 1,
    "initial_cookie_status": "Cookie有效（剩余12.5分钟）",
    "final_cookie_status": "Cookie仍然有效（剩余11.2分钟）",
    "browser_mode": "headless"
  },
  "results": [
    {
      "url": "https://www.xiaohongshu.com/explore/6724e85a000000001b0138c8",
      "status": "success",
      "message": "第1个URL处理成功",
      "index": 1
    },
    {
      "url": "https://www.xiaohongshu.com/explore/68a9d11e000000001d0151a3",
      "status": "success", 
      "message": "第2个URL处理成功",
      "index": 2
    },
    {
      "url": "https://www.xiaohongshu.com/explore/invalid-url",
      "status": "error",
      "message": "第3个URL处理失败",
      "index": 3,
      "hint": "请检查URL是否正确"
    }
  ]
}
```

## 💡 使用技巧

### 1. 最佳实践
- **Cookie有效期内批处理**：在15分钟Cookie有效期内完成所有URL处理
- **合理数量**：建议单次批处理不超过10个URL
- **URL格式**：确保URL格式正确，包含必要的token参数

### 2. 性能优化
- **第一次需要登录**：首个URL可能需要登录，后续URL复用Cookie
- **串行处理**：当前采用串行处理，保证稳定性（未来可能支持并发）
- **错误处理**：单个URL失败不影响其他URL的处理

### 3. 监控和调试
- **使用可见浏览器调试**：添加`&headless=false`参数查看处理过程
- **检查Cookie状态**：使用`/tools/cookieStatus`接口监控Cookie状态
- **日志信息**：服务器日志会显示详细的处理进度

## 🔧 故障排查

### 常见问题：
1. **URL格式错误**：确保URL完整且正确编码
2. **Cookie过期**：超过15分钟需要重新登录
3. **网络问题**：检查网络连接和小红书网站状态
4. **批量过多**：单次处理太多URL可能导致超时

### 解决方案：
- 分批处理大量URL
- 定期检查Cookie状态
- 使用可见浏览器模式调试问题