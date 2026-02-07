# Direct HTTP API Version - No External Packages Required

This version uses **pure Python standard library** - no external LLM packages needed!

## Key Features

✅ **Zero external dependencies** - Uses only `urllib` from Python stdlib  
✅ **Direct HTTP API calls** - Works with any OpenAI-compatible API  
✅ **Built-in retry logic** - Automatic retries with exponential backoff  
✅ **Rate limit handling** - Detects and handles 429 errors gracefully  
✅ **Full provider support** - Anthropic, OpenRouter, Together, Groq, local Ollama  

## Installation

Only requirement: Python 3.6+

```bash
python --version  # Should be 3.6 or higher
```

Optional (for summary tables):
```bash
pip install pandas
```

That's it! No other packages needed.

## Setup by Provider

### Anthropic Claude (Recommended - Highest Quality)

```bash
# 1. Get API key from https://console.anthropic.com/account/keys
# 2. Set environment variable
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx"

# 3. Run pipeline
python cdss_lit_review_pipeline_v3.py pubmed_export.csv
```

### OpenRouter (Budget-Friendly - 100+ Models)

```bash
# 1. Sign up at https://openrouter.ai
# 2. Get API key from https://openrouter.ai/account/api-keys
# 3. Set environment variable
export OPENROUTER_API_KEY="sk-or-xxxxxxxxxxxxxxxxxxxxxxxx"

# 4. Run pipeline
python cdss_lit_review_pipeline_v3.py pubmed_export.csv \
  --provider openrouter \
  --model meta-llama/llama-2-70b-chat-hf

# 5. List available models
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Together.ai (Cheapest)

```bash
# 1. Sign up at https://together.ai
# 2. Get API key from https://api.together.xyz/signin
# 3. Set environment variable
export TOGETHER_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxx"

# 4. Run pipeline
python cdss_lit_review_pipeline_v3.py pubmed_export.csv \
  --provider together \
  --model meta-llama/Llama-2-70b-chat-hf
```

### Groq (Fastest)

```bash
# 1. Sign up at https://console.groq.com
# 2. Get API key
# 3. Set environment variable
export GROQ_API_KEY="gsk_xxxxxxxxxxxxxxxxxxxxxxxx"

# 4. Run pipeline
python cdss_lit_review_pipeline_v3.py pubmed_export.csv \
  --provider groq \
  --model mixtral-8x7b-32768
```

### Local Ollama (Free - No API Key)

```bash
# 1. Install Ollama from https://ollama.ai
# 2. Download a model
ollama pull llama2
# or smaller/faster:
ollama pull mistral

# 3. Start the server (Terminal 1)
ollama serve

# 4. In another terminal, run pipeline (Terminal 2)
python cdss_lit_review_pipeline_v3.py pubmed_export.csv \
  --provider local \
  --model llama2

# 5. List available local models
ollama list
```

## Full Command Examples

### See all available options
```bash
python cdss_lit_review_pipeline_v3.py
```

### Quick screening with fast API
```bash
export GROQ_API_KEY="..."
python cdss_lit_review_pipeline_v3.py pubmed.csv \
  --provider groq \
  --model mixtral-8x7b-32768 \
  --output-dir results/
```

### Use specific API endpoint
```bash
python cdss_lit_review_pipeline_v3.py pubmed.csv \
  --api-url https://custom-api.example.com/v1 \
  --api-key your-key \
  --model your-model
```

### Run quietly (no console output)
```bash
python cdss_lit_review_pipeline_v3.py pubmed.csv --quiet
```

## How the Direct API Works

Instead of using the OpenAI Python package, this script makes raw HTTP POST requests:

```python
# Example of what happens internally
import urllib.request
import json

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}'
}

body = {
    'model': 'meta-llama/llama-2-70b-chat-hf',
    'messages': [{'role': 'user', 'content': prompt}],
    'max_tokens': 4096
}

req = urllib.request.Request(
    'https://api.together.xyz/v1/chat/completions',
    data=json.dumps(body).encode('utf-8'),
    headers=headers,
    method='POST'
)

response = urllib.request.urlopen(req)
result = json.loads(response.read().decode('utf-8'))
```

## Error Handling

The script includes automatic retry logic:

- **Rate limiting (429)**: Waits and retries
- **Server errors (5xx)**: Waits and retries
- **Connection errors**: Retries with exponential backoff
- **Max retries**: 3 attempts before giving up

Example output when rate limited:
```
Rate limited. Waiting 5s before retry...
Rate limited. Waiting 10s before retry...
Rate limited. Waiting 15s before retry...
```

## Timeout Handling

Default timeout is 30 seconds per request. For slow APIs, increase it:

Edit the script:
```python
llm_client = DirectAPIClient(
    provider=args.provider,
    model=args.model,
    api_key=args.api_key,
    timeout=60  # Increase to 60 seconds
)
```

## Network Troubleshooting

### "Connection refused"

**For local Ollama**: Make sure server is running
```bash
# Terminal 1
ollama serve

# Terminal 2
curl http://localhost:11434/v1/models  # Check connection
```

### "HTTP 401 - Unauthorized"

**API key is missing or invalid**
```bash
# Check if env var is set
echo $ANTHROPIC_API_KEY

# Or pass explicitly
python cdss_lit_review_pipeline_v3.py pubmed.csv \
  --api-key sk-ant-...
```

### "HTTP 404 - Not Found"

**Model name is wrong**
```bash
# List available models for your provider
# See section above for each provider
```

### "HTTP 429 - Rate Limited"

**Script will auto-retry, but you can:**
- Use a cheaper provider temporarily
- Wait a few minutes
- Increase the delay between requests (edit script)

## Performance Tips

### For Screening Large Batches (500+ articles)
Use Groq (fastest):
```bash
python cdss_lit_review_pipeline_v3.py pubmed.csv \
  --provider groq \
  --model mixtral-8x7b-32768
```

### For Quality Critical Tasks
Use Anthropic Claude:
```bash
python cdss_lit_review_pipeline_v3.py pubmed.csv \
  --provider anthropic \
  --model claude-opus-4-5-20251101
```

### For Budget Constrained Projects
Use Together.ai or local Ollama:
```bash
# Together (very cheap)
python cdss_lit_review_pipeline_v3.py pubmed.csv \
  --provider together \
  --model meta-llama/Llama-2-70b-chat-hf

# OR Local Ollama (free)
python cdss_lit_review_pipeline_v3.py pubmed.csv \
  --provider local \
  --model mistral
```

## Logs and Debugging

All output saved to: `lit_review_output/processing_log.txt`

View logs in real-time:
```bash
tail -f lit_review_output/processing_log.txt
```

Check for errors:
```bash
grep ERROR lit_review_output/processing_log.txt
```

## API Request Format Reference

Each provider expects slightly different request formats. This script handles all of them:

### Anthropic Format
```json
{
  "model": "claude-opus-4-5-20251101",
  "max_tokens": 4096,
  "messages": [{"role": "user", "content": "..."}]
}
```
Headers: `x-api-key`, `anthropic-version`

### OpenAI-compatible Format (OpenRouter, Together, Groq)
```json
{
  "model": "meta-llama/llama-2-70b-chat-hf",
  "max_tokens": 4096,
  "temperature": 0.3,
  "messages": [{"role": "user", "content": "..."}]
}
```
Headers: `Authorization: Bearer {key}`

The script automatically formats requests correctly for each provider!

## Advanced: Custom API Endpoint

To use a different OpenAI-compatible service:

```bash
python cdss_lit_review_pipeline_v3.py pubmed.csv \
  --api-url https://your-api.com/v1 \
  --api-key your-key \
  --model your-model-name
```

Make sure the endpoint responds with standard OpenAI format:
```json
{
  "choices": [
    {
      "message": {
        "content": "response text here"
      }
    }
  ]
}
```

## Cost Comparison

For 500 articles with this version:

| Provider | Model | Est. Cost | Speed |
|----------|-------|-----------|-------|
| Anthropic | claude-opus-4-5 | $8-12 | Medium |
| OpenRouter | llama-2-70b | $0.30-0.50 | Varies |
| Together | llama-2-70b | $0.15-0.30 | Medium |
| Groq | mixtral-8x7b | $0.10-0.20 | **Fast** |
| Ollama | llama2 | $0 | Slow |

## Frequently Asked Questions

**Q: Do I need to install any packages?**
A: No! Only Python 3.6+ is required. `pandas` is optional for CSV export.

**Q: What Python versions work?**
A: 3.6+. Uses only standard library urllib and json modules.

**Q: Can I use multiple API keys?**
A: Yes, set different env vars and run multiple times with different --provider.

**Q: What if my provider isn't listed?**
A: Use `--api-url` flag to point to any OpenAI-compatible API endpoint.

**Q: How do I know if the API is working?**
A: Check the processing_log.txt file - it will show successful API calls.

**Q: Can I run this on a laptop?**
A: Yes! Uses minimal resources. No GPU needed.

**Q: Can I use this in a Docker container?**
A: Yes! Just need Python 3.6+ and internet connection.

## Next Steps

1. Choose a provider (Anthropic for quality, Groq for speed, Ollama for free)
2. Get an API key (if not using local Ollama)
3. Set the environment variable
4. Run the pipeline with your PubMed CSV
5. Check results in the output folder

Good luck! 🚀
