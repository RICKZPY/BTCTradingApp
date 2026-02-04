# Migration Guide: From OpenAI-Only to Model-Agnostic AI

This guide helps you migrate from the OpenAI-specific `NewsAnalyzer` to the new model-agnostic `ModelAgnosticNewsAnalyzer`.

## What Changed

### Before (OpenAI-Only)
```python
from news_analysis.analyzer import NewsAnalyzer

# Only supported OpenAI
analyzer = NewsAnalyzer(api_key="sk-...")
```

### After (Model-Agnostic)
```python
from news_analysis.ai_analyzer import ModelAgnosticNewsAnalyzer

# Supports multiple providers
analyzer = ModelAgnosticNewsAnalyzer(
    provider_type="openai",  # or "anthropic", "google"
    model="gpt-4",
    api_key="sk-..."
)
```

## Configuration Changes

### Environment Variables

Add these new environment variables to your `.env` file:

```bash
# Primary AI Provider Configuration
AI_PROVIDER=openai
AI_MODEL=gpt-4
AI_TEMPERATURE=0.3
AI_MAX_TOKENS=1000
AI_FALLBACK_PROVIDER=anthropic
AI_FALLBACK_MODEL=claude-3-sonnet-20240229

# OpenAI Configuration (existing)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_BASE_URL=
OPENAI_ORGANIZATION=

# Anthropic Configuration (new)
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_BASE_URL=
ANTHROPIC_VERSION=2023-06-01

# Google AI Configuration (new)
GOOGLE_API_KEY=your-google-ai-api-key
GOOGLE_BASE_URL=
```

### Config.py Updates

The `APISettings` class now includes:

```python
class APISettings(BaseSettings):
    # AI Providers - Primary
    ai_provider: str = "openai"
    ai_model: str = "gpt-4"
    
    # OpenAI
    openai_api_key: str = ""
    openai_base_url: Optional[str] = None
    openai_organization: Optional[str] = None
    
    # Anthropic
    anthropic_api_key: str = ""
    anthropic_base_url: Optional[str] = None
    anthropic_version: str = "2023-06-01"
    
    # Google AI
    google_api_key: str = ""
    google_base_url: Optional[str] = None
    
    # AI Configuration
    ai_temperature: float = 0.3
    ai_max_tokens: int = 1000
    ai_fallback_provider: Optional[str] = None
    ai_fallback_model: Optional[str] = None
```

## Code Migration Examples

### Basic Usage Migration

**Before:**
```python
from news_analysis.analyzer import NewsAnalyzer

analyzer = NewsAnalyzer()
analyzed_item = await analyzer.analyze_news_item(news_item)
```

**After:**
```python
from news_analysis.ai_analyzer import ModelAgnosticNewsAnalyzer

# Uses configuration from settings by default
analyzer = ModelAgnosticNewsAnalyzer()
analyzed_item = await analyzer.analyze_news_item(news_item)
```

### Custom Provider Usage

**New capability:**
```python
# Use Anthropic Claude
analyzer = ModelAgnosticNewsAnalyzer(
    provider_type="anthropic",
    model="claude-3-opus-20240229",
    api_key="your-anthropic-key"
)

# Use Google Gemini
analyzer = ModelAgnosticNewsAnalyzer(
    provider_type="google",
    model="gemini-1.5-pro",
    api_key="your-google-key"
)
```

### Fallback Configuration

**New capability:**
```python
# Primary provider with fallback
analyzer = ModelAgnosticNewsAnalyzer(
    provider_type="openai",
    model="gpt-4",
    fallback_provider="anthropic"
)
```

### Batch Analysis Migration

**Before:**
```python
analyzed_items = await analyzer.analyze_batch(news_items)
```

**After:**
```python
# Same interface, but now supports multiple providers
analyzed_items = await analyzer.analyze_batch(news_items)
```

## New Features

### 1. Provider Information
```python
# Get current provider configuration
info = analyzer.get_provider_info()
print(f"Using: {info['primary_provider']} with {info['primary_model']}")
```

### 2. Connection Testing
```python
# Test provider connections
results = await analyzer.test_providers()
print(f"Primary provider working: {results['primary']}")
```

### 3. Cost Tracking
```python
# AI responses now include cost information
response = await analyzer.analyze_sentiment("Bitcoin news...")
# Cost is automatically tracked in the response metadata
```

### 4. Enhanced Market Summary
```python
summary = await analyzer.generate_market_summary(news_items)
# Now includes provider information
print(f"Analysis by: {summary['ai_provider']} ({summary['ai_model']})")
```

## Supported Providers and Models

### OpenAI
- `gpt-4`
- `gpt-4-turbo`
- `gpt-3.5-turbo`
- `gpt-3.5-turbo-16k`

### Anthropic
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`
- `claude-2.1`
- `claude-2.0`

### Google AI
- `gemini-pro`
- `gemini-1.5-pro`
- `gemini-1.5-flash`
- `gemini-pro-vision`

## Migration Checklist

- [ ] Update environment variables in `.env`
- [ ] Install any additional dependencies (already included in requirements.txt)
- [ ] Update import statements from `analyzer` to `ai_analyzer`
- [ ] Update class name from `NewsAnalyzer` to `ModelAgnosticNewsAnalyzer`
- [ ] Test with your current OpenAI setup (should work without changes)
- [ ] Optionally configure fallback providers
- [ ] Test new provider options if desired

## Backward Compatibility

The new `ModelAgnosticNewsAnalyzer` is designed to be backward compatible:

1. **Default behavior**: Uses OpenAI by default (same as before)
2. **Same interface**: All public methods have the same signatures
3. **Same output format**: Analysis results are identical
4. **Configuration**: Reads from the same settings if no explicit configuration provided

## Performance Considerations

### Cost Optimization
- Different providers have different pricing models
- Use the cost estimation features to optimize your usage
- Consider using cheaper models for less critical analysis

### Fallback Strategy
- Configure fallback providers to improve reliability
- Fallback providers activate automatically if primary fails
- No code changes needed to benefit from fallback

### Caching
- Analysis results are cached with provider-specific keys
- Switching providers won't invalidate existing cache
- Cache keys include provider and model information

## Troubleshooting

### Common Issues

1. **Missing API Key Error**
   ```
   AIProviderError: No API key configured for provider 'anthropic'
   ```
   **Solution**: Add the required API key to your `.env` file

2. **Unsupported Model Error**
   ```
   AIProviderError: Model 'gpt-5' not supported by openai
   ```
   **Solution**: Use a supported model from the list above

3. **Provider Connection Failed**
   ```
   Primary provider test failed: Network error
   ```
   **Solution**: Check your internet connection and API key validity

### Testing Your Setup

Run the example script to test your configuration:

```bash
cd backend
python news_analysis/example_ai_usage.py
```

This will show you which providers are working and help identify configuration issues.

## Getting Help

If you encounter issues during migration:

1. Check the example files in `news_analysis/example_ai_usage.py`
2. Run the test suite: `python -m pytest tests/test_ai_providers.py`
3. Review the logs for detailed error messages
4. Ensure all required API keys are properly configured

The migration should be seamless for existing OpenAI users, with the added benefit of supporting multiple AI providers and improved reliability through fallback mechanisms.