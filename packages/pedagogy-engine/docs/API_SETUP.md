# API Setup Guide

The generator supports both OpenAI and Anthropic APIs. You can use either one (or both).

## Current Configuration

Your `.env` file is currently set to:
- **Provider:** OpenAI
- **Model:** gpt-4o-mini
- **Temperature:** 0.7

## OpenAI Setup (Current)

### 1. Get API Key
- Sign up at https://platform.openai.com/
- Go to API Keys section
- Create new secret key
- Copy the key (starts with `sk-proj-...` or `sk-...`)

### 2. Configure .env
```bash
API_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-key-here
DEFAULT_MODEL=gpt-4o-mini
```

### 3. Available Models

| Model | Speed | Cost | Quality | Best For |
|-------|-------|------|---------|----------|
| **gpt-4o-mini** | Fast | Cheap | Good | Testing, iteration (RECOMMENDED) |
| **gpt-4o** | Medium | Medium | Excellent | Production |
| **gpt-4-turbo** | Medium | Medium | Excellent | Alternative to 4o |
| **o1-preview** | Slow | Expensive | Excellent | Complex reasoning |
| **o1-mini** | Medium | Medium | Very Good | Reasoning on budget |

**For this project, start with `gpt-4o-mini`** - it's cheap and good enough for initial iterations.

### 4. Pricing (as of Jan 2026)

- **gpt-4o-mini:** ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **gpt-4o:** ~$2.50 per 1M input tokens, ~$10 per 1M output tokens

**Cost per generation (estimated):**
- With 3 exemplars + prompt: ~2,500 input tokens
- Output: ~1,000 tokens
- **gpt-4o-mini:** ~$0.001 per generation (1/10th of a cent!)
- **gpt-4o:** ~$0.016 per generation (1.6 cents)

**You can generate 1,000 pedagogical intents for ~$1 with gpt-4o-mini!**

## Anthropic Setup (Alternative)

### 1. Get API Key
- Sign up at https://console.anthropic.com/
- Go to API Keys
- Create new key
- Copy the key (starts with `sk-ant-...`)

### 2. Configure .env
```bash
API_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
DEFAULT_MODEL=claude-sonnet-4
```

### 3. Available Models

| Model | Speed | Cost | Quality | Best For |
|-------|-------|------|---------|----------|
| **claude-sonnet-4** | Fast | Cheap | Very Good | Testing, iteration |
| **claude-opus-4-5** | Slow | Expensive | Excellent | Production, complex topics |
| **claude-sonnet-3-5-v2** | Fast | Cheap | Good | Budget option |

### 4. Pricing (as of Jan 2026)

- **claude-sonnet-4:** ~$3 per 1M input tokens, ~$15 per 1M output tokens
- **claude-opus-4-5:** ~$15 per 1M input tokens, ~$75 per 1M output tokens

**Cost per generation (estimated):**
- **claude-sonnet-4:** ~$0.023 per generation (2.3 cents)
- **claude-opus-4-5:** ~$0.113 per generation (11 cents)

## Switching Between Providers

### Method 1: Update .env file
```bash
# Switch to Anthropic
API_PROVIDER=anthropic
DEFAULT_MODEL=claude-sonnet-4

# Switch back to OpenAI
API_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini
```

### Method 2: Command line override
```bash
# Use OpenAI for this generation
python layer1/generator.py --topic "Backpropagation" --provider openai --model gpt-4o-mini

# Use Anthropic for this generation
python layer1/generator.py --topic "Backpropagation" --provider anthropic --model claude-opus-4-5
```

## Recommendations

### Phase 1: Testing (Week 1-2)
- **Use:** gpt-4o-mini (OpenAI)
- **Why:** Extremely cheap (~$0.001/generation), fast iteration
- **Goal:** Generate 50+ topics, find what works

### Phase 2: Quality Check (Week 3-4)
- **Use:** gpt-4o (OpenAI) or claude-sonnet-4 (Anthropic)
- **Why:** Better quality for review
- **Goal:** Generate 100+ topics for expert review

### Phase 3: Production (Month 2+)
- **Use:** Fine-tuned model (cheaper + better than prompting)
- **Fallback:** gpt-4o for novel topics
- **Why:** Cost-effective at scale

## Testing Your Setup

```bash
# Test OpenAI
python layer1/generator.py --topic "Test Topic" --provider openai --model gpt-4o-mini

# Test Anthropic (if you have API key)
python layer1/generator.py --topic "Test Topic" --provider anthropic --model claude-sonnet-4
```

## Troubleshooting

### "OpenAI package not installed"
```bash
pip install openai
```

### "Anthropic package not installed"
```bash
pip install anthropic
```

### "API key not found"
- Check that `.env` file exists (not `.env.example`)
- Check that API key is set: `OPENAI_API_KEY=sk-...` or `ANTHROPIC_API_KEY=sk-ant-...`
- No quotes around the key
- Restart your terminal/shell after editing `.env`

### "Rate limit exceeded"
- OpenAI: You might be on free tier - add payment method
- Anthropic: Similar - add payment method
- Or: Add delays between generations

### Response format issues
- OpenAI gpt-4o-mini should return JSON directly (we use `response_format`)
- If getting markdown wrapped JSON, the code handles this automatically
- Check that `response_format={"type": "json_object"}` is set for OpenAI GPT models

## Cost Monitoring

### OpenAI
- Dashboard: https://platform.openai.com/usage
- Set spending limits in settings
- Get email alerts at thresholds

### Anthropic
- Dashboard: https://console.anthropic.com/settings/usage
- View usage by day/week/month
- Set budget alerts

## API Best Practices

1. **Start cheap, scale up**: Use gpt-4o-mini until you need better quality
2. **Monitor costs**: Check dashboard weekly
3. **Set spending limits**: Prevent unexpected bills
4. **Cache exemplars**: We load once per generator instance (efficient)
5. **Batch when possible**: Generator supports batch mode
6. **Rate limits**: Respect API rate limits (code doesn't handle this yet - add if needed)

## Questions?

- OpenAI docs: https://platform.openai.com/docs
- Anthropic docs: https://docs.anthropic.com/
- Our generator code: [layer1/generator.py](../layer1/generator.py)
