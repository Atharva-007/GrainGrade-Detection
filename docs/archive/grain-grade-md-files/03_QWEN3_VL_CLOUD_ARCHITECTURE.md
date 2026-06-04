# Qwen3-VL Cloud Architecture

## Objective

Move the vision model from local-only Qwen3-VL through Ollama to configurable cloud Qwen3-VL while preserving the same grading behavior.

The improved design keeps local OpenCV and rule logic fast, then sends only the compressed image crop, proxy signals, and compact RAG context to the cloud model.

## Provider Model

Supported providers:

- `dashscope`: recommended default for Qwen3-VL cloud.
- `siliconflow`: retained because the repository already used a SiliconFlow-style OpenAI-compatible path.
- `custom`: any OpenAI-compatible `/chat/completions` endpoint.
- `ollama`: local fallback and development mode.

Environment variables:

```bash
QWEN_VL_PROVIDER=dashscope
QWEN_VL_MODEL=qwen3-vl-plus
QWEN_VL_API_KEY=...
QWEN_VL_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_VL_TIMEOUT_SECONDS=75
```

Provider-specific fallback keys:

- DashScope: `DASHSCOPE_API_KEY`, `DASHSCOPE_BASE_URL`
- SiliconFlow: `SILICONFLOW_API_KEY`, `SILICONFLOW_BASE_URL`

## Cloud Request Shape

Use OpenAI-compatible chat completions:

```json
{
  "model": "qwen3-vl-plus",
  "messages": [
    {
      "role": "system",
      "content": "Return only the final JSON object. Do not include markdown, notes, or prose."
    },
    {
      "role": "user",
      "content": [
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,..."
          }
        },
        {
          "type": "text",
          "text": "Grade this finger millet batch..."
        }
      ]
    }
  ],
  "max_tokens": 260,
  "temperature": 0.3,
  "top_p": 0.8,
  "stream": false
}
```

The pipeline should parse:

- `message.content`
- text blocks inside list content
- `message.reasoning_content`
- `message.reasoning`
- `message.thinking`

This is necessary because some Qwen providers may expose reasoning text differently.

## Latency Strategy

1. Run OpenCV proxies locally first.
2. If the proxy fast path detects an obviously bad lot, return without cloud VLM.
3. Crop to the calibrated sample field when available.
4. Resize/compress the image before upload.
5. Retrieve only top rule chunks.
6. Use strict JSON output and short prompts.
7. Apply deterministic rules locally after model output.

## Failure Strategy

If cloud Qwen fails:

1. Try JSON repair using the same configured provider when possible.
2. If repair fails, recover hints from text.
3. If no usable response exists, use deterministic proxy/rule fallback.
4. Mark output as fallback through `model_version` and `signal_highlights`.
5. Require manual review for low-confidence or fallback decisions.

## Security

- Never commit API keys.
- Load keys from `.env` or environment variables.
- Keep `.env` ignored.
- Avoid logging base64 image payloads.
- Store only necessary audit metadata in result objects.

## Why Not Put Everything In The Cloud

Do not move all processing into Qwen3-VL. Local deterministic processing is required because it:

- reduces latency and token cost
- gives explainable features
- supports fallback
- makes decisions auditable
- prevents VLM-only hallucinated grading

## Deployment Modes

### Development Cloud Mode

```bash
QWEN_VL_PROVIDER=dashscope
QWEN_VL_MODEL=qwen3-vl-plus
streamlit run app.py
```

### Local Development Mode

```bash
QWEN_VL_PROVIDER=ollama
QWEN_VL_MODEL=qwen3-vl:8b
ollama serve
streamlit run app.py
```

### Custom Provider Mode

```bash
QWEN_VL_PROVIDER=custom
QWEN_VL_MODEL=your-model-name
QWEN_VL_BASE_URL=https://your-openai-compatible-host/v1
QWEN_VL_API_KEY=...
```

## Verification

Use mocked API tests first. Real cloud tests should only run manually when an API key is present.

Manual smoke test:

1. Set provider env vars.
2. Run Streamlit.
3. Upload a known ragi image.
4. Confirm the runtime chip says cloud ready.
5. Confirm final result has `model_version` like `dashscope/qwen3-vl-plus`.
6. Temporarily break the key and confirm deterministic fallback behavior.

