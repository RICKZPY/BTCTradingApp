# Model-Agnostic AI Provider System

这个模块提供了一个model-agnostic的AI提供商系统，支持多个AI服务提供商，包括国际和中国的主流AI服务。

## 特性

### 支持的AI提供商

#### 国际提供商
- **OpenAI**: GPT-4, GPT-3.5-turbo等模型
- **Anthropic**: Claude-3系列模型
- **Google AI**: Gemini系列模型

#### 中国提供商
- **Deepseek**: 深度求索的高性价比模型
- **Doubao (豆包)**: 字节跳动的AI模型服务

### 核心功能
- 统一的API接口，支持不同的AI提供商
- 自动故障转移和备用提供商支持
- 成本估算和使用情况跟踪
- 连接测试和健康检查
- 灵活的配置管理
- 支持中国大陆网络环境

## 快速开始

### 1. 配置API密钥

在你的`.env`文件中添加以下配置：

```bash
# 主要AI提供商配置
AI_PROVIDER=openai
AI_MODEL=gpt-4
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=1000
AI_FALLBACK_PROVIDER=deepseek
AI_FALLBACK_MODEL=deepseek-chat

# OpenAI配置
OPENAI_API_KEY=sk-your-openai-api-key

# Anthropic配置
ANTHROPIC_API_KEY=your-anthropic-api-key

# Google AI配置
GOOGLE_API_KEY=your-google-ai-api-key

# Deepseek配置 (中国)
DEEPSEEK_API_KEY=your-deepseek-api-key

# Doubao配置 (字节跳动豆包)
DOUBAO_API_KEY=your-doubao-api-key
```

### 2. 基本使用

```python
from ai_providers.factory import AIProviderFactory

# 创建Deepseek提供商
provider = AIProviderFactory.create_provider(
    provider_type="deepseek",
    api_key="your-api-key",
    model="deepseek-chat"
)

# 创建豆包提供商
provider = AIProviderFactory.create_provider(
    provider_type="doubao",
    api_key="your-api-key",
    model="doubao-lite-4k"
)

# 生成文本
response = await provider.generate_completion(
    prompt="分析这条新闻的情绪",
    system_prompt="你是一个金融分析师",
    temperature=0.3,
    max_tokens=500
)

print(f"回复: {response.content}")
print(f"成本: ${response.cost:.4f}")
```

### 3. 使用配置文件

```python
config = {
    "provider": "anthropic",
    "api_key": "your-anthropic-key",
    "model": "claude-3-sonnet-20240229"
}

provider = AIProviderFactory.create_from_config(config)
```

## 在新闻分析中的使用

### Model-Agnostic新闻分析器

```python
from news_analysis.ai_analyzer import ModelAgnosticNewsAnalyzer

# 使用默认配置（从settings读取）
analyzer = ModelAgnosticNewsAnalyzer()

# 或指定特定提供商
analyzer = ModelAgnosticNewsAnalyzer(
    provider_type="anthropic",
    model="claude-3-opus-20240229",
    fallback_provider="openai"
)

# 分析新闻
analyzed_item = await analyzer.analyze_news_item(news_item)
```

## 支持的模型

### OpenAI
- `gpt-4` - 最强大的模型，适合复杂分析
- `gpt-4-turbo` - 更快更便宜的GPT-4版本
- `gpt-3.5-turbo` - 快速且经济的选择

### Anthropic
- `claude-3-opus-20240229` - 最强大的Claude模型
- `claude-3-sonnet-20240229` - 平衡性能和成本
- `claude-3-haiku-20240307` - 最快最便宜的选择

### Google AI
- `gemini-1.5-pro` - 最新的高性能模型
- `gemini-pro` - 标准的Gemini模型
- `gemini-1.5-flash` - 快速响应的轻量级模型

### Deepseek (深度求索)
- `deepseek-chat` - 通用对话模型，性价比极高
- `deepseek-coder` - 专门用于代码生成和分析
- `deepseek-v2` - 第二代模型，性能更强
- `deepseek-v2.5` - 最新版本，综合能力提升

### Doubao (豆包 - 字节跳动)
- `doubao-lite-4k` - 轻量级模型，4K上下文
- `doubao-lite-32k` - 轻量级模型，32K上下文
- `doubao-lite-128k` - 轻量级模型，128K上下文
- `doubao-pro-4k` - 专业版模型，4K上下文
- `doubao-pro-32k` - 专业版模型，32K上下文
- `doubao-pro-128k` - 专业版模型，128K上下文
- `doubao-pro-256k` - 专业版模型，256K上下文

## 成本比较

基于1000个输入token + 1000个输出token的估算成本：

| 提供商 | 模型 | 成本 (USD) | 备注 |
|--------|------|-----------|------|
| Deepseek | deepseek-chat | $0.0003 | 🇨🇳 极高性价比 |
| Google | gemini-pro | $0.002 | 国际服务 |
| OpenAI | gpt-3.5-turbo | $0.0035 | 国际服务 |
| Doubao | doubao-lite-4k | $0.0009 | 🇨🇳 字节跳动 |
| Doubao | doubao-pro-4k | $0.0028 | 🇨🇳 专业版 |
| Anthropic | claude-3-sonnet | $0.018 | 国际服务 |
| OpenAI | gpt-4 | $0.090 | 国际服务 |
| Anthropic | claude-3-opus | $0.090 | 国际服务 |

**中国用户推荐**: Deepseek和豆包提供了极具竞争力的价格，同时在中国大陆有更好的网络连接。

## 故障转移和可靠性

系统支持自动故障转移，特别适合中国用户的网络环境：

```python
# 推荐配置：中国提供商作为主力，国际提供商作为备用
analyzer = ModelAgnosticNewsAnalyzer(
    provider_type="deepseek",
    model="deepseek-chat",
    fallback_provider="doubao",  # 同样是中国提供商，网络稳定
    fallback_model="doubao-lite-4k"
)

# 或者混合配置：国际+中国
analyzer = ModelAgnosticNewsAnalyzer(
    provider_type="openai",
    model="gpt-4",
    fallback_provider="deepseek",  # 中国提供商作为备用
    fallback_model="deepseek-chat"
)
```

当主提供商失败时，系统会自动切换到备用提供商，确保服务的连续性。

## 测试连接

```python
# 测试单个提供商
success = await AIProviderFactory.test_provider_connection(
    provider_type="openai",
    api_key="your-key",
    model="gpt-4"
)

# 测试分析器的所有提供商
results = await analyzer.test_providers()
print(f"主提供商: {results['primary']}")
print(f"备用提供商: {results['fallback']}")
```

## 迁移指南

如果你之前使用的是OpenAI专用的`NewsAnalyzer`，请参考 `news_analysis/MIGRATION_GUIDE.md` 获取详细的迁移指南。

## 错误处理

系统提供了详细的错误处理：

```python
from ai_providers.base import AIProviderError

try:
    provider = AIProviderFactory.create_provider(
        provider_type="invalid",
        api_key="test",
        model="test"
    )
except AIProviderError as e:
    print(f"提供商错误: {e.message}")
    print(f"提供商: {e.provider}")
    print(f"错误代码: {e.error_code}")
```

## 开发和测试

运行测试套件：

```bash
# 测试AI提供商系统
python -m pytest tests/test_ai_providers.py -v

# 运行系统测试
python test_ai_system.py
```

## 扩展支持

要添加新的AI提供商：

1. 继承`AIProvider`基类
2. 实现所有抽象方法
3. 在`AIProviderFactory`中注册新提供商
4. 添加相应的测试

## 最佳实践

1. **成本优化**: 根据任务复杂度选择合适的模型
2. **可靠性**: 配置备用提供商以提高系统可用性
3. **监控**: 使用成本跟踪功能监控API使用情况
4. **缓存**: 利用现有的缓存机制减少重复调用
5. **错误处理**: 实现适当的错误处理和重试逻辑

## 配置示例

完整的`.env`配置示例：

```bash
# AI提供商配置
AI_PROVIDER=deepseek
AI_MODEL=deepseek-chat
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=1000
AI_FALLBACK_PROVIDER=doubao
AI_FALLBACK_MODEL=doubao-lite-4k

# API密钥
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
DEEPSEEK_API_KEY=your-deepseek-key
DOUBAO_API_KEY=your-doubao-key

# 可选配置
OPENAI_ORGANIZATION=your-org-id
ANTHROPIC_VERSION=2023-06-01
DOUBAO_REGION=cn-beijing
```

### 中国用户特别说明

1. **网络连接**: Deepseek和豆包在中国大陆有更稳定的网络连接
2. **成本优势**: 中国提供商通常比国际提供商便宜很多
3. **语言支持**: 对中文内容的理解和生成更加准确
4. **合规性**: 符合中国相关法规要求

### 获取API密钥

- **Deepseek**: 访问 [https://platform.deepseek.com](https://platform.deepseek.com)
- **豆包**: 访问 [https://console.volcengine.com/ark](https://console.volcengine.com/ark)
- **OpenAI**: 访问 [https://platform.openai.com](https://platform.openai.com)
- **Anthropic**: 访问 [https://console.anthropic.com](https://console.anthropic.com)
- **Google AI**: 访问 [https://makersuite.google.com](https://makersuite.google.com)

这个系统为比特币交易系统提供了灵活、可靠且经济高效的AI分析能力。