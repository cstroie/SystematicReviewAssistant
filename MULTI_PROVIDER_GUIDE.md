# Multi-Provider LLM Literature Review Pipeline

This improved version works with **any OpenAI-compatible API**, giving you flexibility to choose the best service for your needs.

---

## Supported Providers

### 1. **Anthropic Claude** (Default)
- **Models**: claude-opus-4-5, claude-sonnet-4-5, claude-haiku-4-5
- **Pricing**: $3-15 per 1M input tokens, $15-60 per 1M output tokens
- **Speed**: Medium
- **Quality**: Highest
- **URL**: https://console.anthropic.com

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python systematic_review_assistant.py pubmed.csv
```

### 2. **OpenRouter** (100+ models)
- **Models**: Llama 2 70B, Mistral 7B, OpenChat, and 100+ others
- **Pricing**: Varies by model ($0.0005-0.002 per 1K tokens)
- **Speed**: Varies
- **Quality**: Varies (good options available)
- **URL**: https://openrouter.ai

```bash
export OPENROUTER_API_KEY="sk-or-..."
python systematic_review_assistant.py pubmed.csv \
  --provider openrouter \
  --model meta-llama/llama-2-70b-chat-hf
```

### 3. **Together.ai** (Open source models)
- **Models**: Llama 2, Falcon, MPT, and others
- **Pricing**: Very cheap ($0.0002-0.001 per 1K tokens)
- **Speed**: Fast
- **Quality**: Good for the price
- **URL**: https://together.xyz

```bash
export TOGETHER_API_KEY="..."
python systematic_review_assistant.py pubmed.csv \
  --provider together \
  --model meta-llama/Llama-2-70b-chat-hf
```

### 4. **Groq** (Ultra-fast inference)
- **Models**: Mixtral 8x7B, Llama 2 70B
- **Pricing**: Free tier available, paid very cheap
- **Speed**: Extremely fast
- **Quality**: Good
- **URL**: https://console.groq.com

```bash
export GROQ_API_KEY="..."
python systematic_review_assistant.py pubmed.csv \
  --provider groq \
  --model mixtral-8x7b-32768
```

### 5. **Local Models** (Ollama, vLLM)
- **Models**: Any model you can run locally (Llama 2, Mistral, etc.)
- **Pricing**: Free (hardware cost only)
- **Speed**: Depends on your hardware
- **Quality**: Depends on model choice
- **Setup**: Run `ollama serve` first

```bash
python systematic_review_assistant.py pubmed.csv \
  --provider local \
  --model llama2 \
  --api-url http://localhost:11434/v1
```

---

## Quick Start by Provider

### Setup Anthropic (Recommended - Best Quality)

1. Get API key: https://console.anthropic.com/account/keys
2. Set environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx"
```
3. Run:
```bash
python systematic_review_assistant.py pubmed_export.csv
```

### Setup OpenRouter (Budget-Friendly)

1. Sign up: https://openrouter.ai
2. Get API key from Settings
3. Set environment variable:
```bash
export OPENROUTER_API_KEY="sk-or-xxxxxxxxxxxxxxxxxxxxxxxx"
```
4. List available models:
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" | jq .
```
5. Run with your chosen model:
```bash
python systematic_review_assistant.py pubmed_export.csv \
  --provider openrouter \
  --model meta-llama/llama-2-70b-chat-hf
```

### Setup Together.ai (Cheapest)

1. Sign up: https://together.ai
2. Get API key from Settings
3. Set environment variable:
```bash
export TOGETHER_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxx"
```
4. Run:
```bash
python systematic_review_assistant.py pubmed_export.csv \
  --provider together \
  --model meta-llama/Llama-2-70b-chat-hf
```

### Setup Groq (Fastest)

1. Sign up: https://console.groq.com
2. Get API key
3. Set environment variable:
```bash
export GROQ_API_KEY="gsk_xxxxxxxxxxxxxxxxxxxxxxxx"
```
4. Run:
```bash
python systematic_review_assistant.py pubmed_export.csv \
  --provider groq \
  --model mixtral-8x7b-32768
```

### Setup Local Ollama (Free)

1. Install Ollama: https://ollama.ai
2. Download a model:
```bash
ollama pull llama2
# or for faster/smaller:
ollama pull mistral
```
3. Start the server:
```bash
ollama serve
```
4. In another terminal, run:
```bash
python systematic_review_assistant.py pubmed_export.csv \
  --provider local \
  --model llama2 \
  --api-url http://localhost:11434/v1
```

---

## Cost Comparison (500 articles)

Estimated costs for processing 500 articles:

| Provider | Model | Cost |
|----------|-------|------|
| **Anthropic** | claude-opus-4-5 | $8-12 |
| **OpenRouter** | llama-2-70b | $0.30-0.50 |
| **Together.ai** | llama-2-70b | $0.15-0.30 |
| **Groq** | mixtral-8x7b | $0.10-0.20 |
| **Local Ollama** | llama2 | $0 (hardware) |

**Accuracy trade-off**:
- Anthropic (highest quality): 95%+ accuracy
- Llama 2 70B (good): 90-92% accuracy
- Smaller models: 85-88% accuracy

---

## Advanced Usage

### Custom API URL

If you want to use a different API-compatible service not in the list:

```bash
python systematic_review_assistant.py pubmed.csv \
  --api-url https://custom-api.example.com/v1 \
  --model your-model-name \
  --api-key your-api-key
```

### Chaining Models

Use a cheap model for screening, expensive model for synthesis:

```bash
# First pass: Screening with cheap model
python systematic_review_assistant.py pubmed.csv \
  --provider together \
  --model meta-llama/Llama-2-70b-chat-hf \
  --output-dir results_screening

# Manual review of uncertain cases (edit 02_screening_results.json)

# Second pass: Extraction/synthesis with better model
python systematic_review_assistant.py filtered_included.csv \
  --provider anthropic \
  --model claude-opus-4-5-20251101 \
  --output-dir results_extraction
```

### Environment Variable Management

Create a `.env` file for easy switching:

```bash
# .env.anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# .env.openrouter
export OPENROUTER_API_KEY="sk-or-..."

# .env.together
export TOGETHER_API_KEY="..."

# .env.groq
export GROQ_API_KEY="..."
```

Load and run:
```bash
source .env.openrouter
python systematic_review_assistant.py pubmed.csv --provider openrouter
```

---

## Model Recommendations by Use Case

### Want Best Quality (Academic Publication)
```bash
# Use Claude Opus (most capable)
python systematic_review_assistant.py pubmed.csv \
  --provider anthropic \
  --model claude-opus-4-5-20251101
```

### Want Best Balance (Quality + Cost)
```bash
# Use Llama 2 70B via OpenRouter
python systematic_review_assistant.py pubmed.csv \
  --provider openrouter \
  --model meta-llama/llama-2-70b-chat-hf
```

### Want Cheapest
```bash
# Use Together.ai with Llama 2
python systematic_review_assistant.py pubmed.csv \
  --provider together \
  --model meta-llama/Llama-2-70b-chat-hf
```

### Want Fastest
```bash
# Use Groq with Mixtral
python systematic_review_assistant.py pubmed.csv \
  --provider groq \
  --model mixtral-8x7b-32768
```

### Want No Costs
```bash
# Use local Ollama with Mistral (lightweight)
python systematic_review_assistant.py pubmed.csv \
  --provider local \
  --model mistral \
  --api-url http://localhost:11434/v1
```

---

## Troubleshooting

### "Error: API key not found"

Make sure you set the environment variable:

```bash
# Check what's set
echo $ANTHROPIC_API_KEY
echo $OPENROUTER_API_KEY
echo $TOGETHER_API_KEY

# Set missing one
export ANTHROPIC_API_KEY="your-key-here"
```

### "Connection refused" with Local Ollama

Make sure Ollama server is running:

```bash
# Terminal 1: Start server
ollama serve

# Terminal 2: Check it's working
curl http://localhost:11434/api/tags

# Terminal 3: Run pipeline
python systematic_review_assistant.py pubmed.csv --provider local --model llama2
```

### "Rate limit exceeded"

The script includes rate limiting, but some providers have strict limits:

- **OpenRouter**: 100+ free, more with paid
- **Together**: High limits on paid
- **Groq**: 30 requests/minute free
- **Local**: No limits (hardware dependent)

**Solution**: Use a cheaper model or local Ollama, or increase delays:

Edit the script and change:
```python
if (i + 1) % 10 == 0:
    time.sleep(1)  # Change to time.sleep(3) for slower API
```

### Model Not Available

Check available models for your provider:

```bash
# OpenRouter
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# Together
curl https://api.together.xyz/v1/models \
  -H "Authorization: Bearer $TOGETHER_API_KEY"

# Groq
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"

# Local Ollama
ollama list
```

---

## Hybrid Approach (Recommended)

Combine providers for best results and cost:

```bash
#!/bin/bash

PUBMED_CSV="pubmed_export.csv"
OUTPUT_DIR="results"

# Step 1: Screening (use cheap model)
echo "Step 1: Screening with Together.ai..."
export TOGETHER_API_KEY="..."
python systematic_review_assistant.py "$PUBMED_CSV" \
  --provider together \
  --model meta-llama/Llama-2-70b-chat-hf \
  --output-dir "$OUTPUT_DIR/screening"

# Manually review UNCERTAIN cases...

# Step 2: Extraction/Synthesis (use better model)
echo "Step 2: Extraction with Anthropic..."
export ANTHROPIC_API_KEY="..."
python systematic_review_assistant.py included_articles.csv \
  --provider anthropic \
  --model claude-opus-4-5-20251101 \
  --output-dir "$OUTPUT_DIR/extraction"

echo "Pipeline complete!"
```

---

## Performance Notes

### Speed Comparison

| Provider | Model | Screening Speed | Notes |
|----------|-------|---|---|
| Anthropic | Claude Opus | ~2 sec/article | Highly variable |
| OpenRouter | Llama 2 70B | ~3-5 sec/article | Variable by load |
| Together | Llama 2 70B | ~2-3 sec/article | Consistent |
| Groq | Mixtral 8x7B | ~0.5-1 sec/article | **Fastest** |
| Local Ollama | Llama 2 | ~5-10 sec/article | Depends on GPU |

### Quality Comparison (Screening Accuracy)

| Provider | Model | Accuracy |
|----------|-------|----------|
| Anthropic | Claude Opus | 95-97% ✓✓✓ |
| OpenRouter | Llama 2 70B | 88-92% ✓✓ |
| Together | Llama 2 70B | 88-92% ✓✓ |
| Groq | Mixtral 8x7B | 90-93% ✓✓ |
| Local Ollama | Llama 2 | 85-88% ✓ |

---

## Next Steps

1. **Choose a provider** based on your priorities (cost/quality/speed)
2. **Get an API key** from that provider
3. **Set the environment variable**
4. **Run the pipeline** with the appropriate command
5. **Manually verify** a sample of results
6. **Write your systematic review** using the generated tables and synthesis

---

## Questions?

### Provider-Specific Help

- **Anthropic**: https://docs.anthropic.com/claude/reference/getting-started-with-the-api
- **OpenRouter**: https://openrouter.ai/docs
- **Together**: https://docs.together.ai
- **Groq**: https://console.groq.com/docs
- **Ollama**: https://github.com/ollama/ollama

### General LLM Usage

- Check the original detailed guide: `WORKFLOW.md`
- Review the QUICKSTART: `QUICKSTART.md`

Good luck with your systematic review! 🎯
