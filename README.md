# Model Validation and Selection Guide

This folder contains the application-pack materials for the PhD research narrative and CV. It does not contain any project code or API configuration files yet.

## What this folder includes

- `cv-phd-oriented.md` — CV draft for PhD applications
- `research-narrative.md` — research narrative / statement of direction
- `README.md` — instructions for validating installed model endpoints

## Why model selection matters

When several model endpoints are available, selection should be based on a few practical signals:

1. Connectivity: whether the model endpoint responds successfully
2. Latency: how quickly it returns output
3. Reliability: whether requests succeed consistently without authentication or rate-limit failures
4. Intended use: whether the model is suitable for the task you want to run
5. Cost and quota: whether the provider or account allows sustained use

In a multi-model environment, the model that is "functioning" is usually the one that:

- accepts your credentials,
- reaches the provider endpoint successfully,
- returns a valid response body,
- and does so consistently during repeated calls.

A model may appear installed but still be unusable if credentials are missing, the endpoint is blocked, the model name is wrong, or the account has no access.

## Quick validation steps

Run the following from a terminal in this folder or from any Python-enabled environment.

### 1) Set your API keys

On macOS/Linux:

```bash
export OPENAI_API_KEY="your-key"
export HF_API_TOKEN="your-hf-token"
```

On Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="your-key"
$env:HF_API_TOKEN="your-hf-token"
```

### 2) Install the minimal dependencies

```bash
pip install requests
```

### 3) Run a model connectivity check

```bash
python - <<'PY'
import os, json, requests

print('Checking environment...')
for key in ['OPENAI_API_KEY', 'HF_API_TOKEN', 'HUGGINGFACE_API_TOKEN']:
    print(f'{key}:', 'set' if os.getenv(key) else 'not set')

print('\nTesting OpenAI...')
key = os.getenv('OPENAI_API_KEY')
if key:
    headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
    for model in ['gpt-5-mini', 'gpt-4', 'gpt-3.5-turbo']:
        try:
            r = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json={
                    'model': model,
                    'messages': [{'role': 'user', 'content': 'Say hello in one word.'}],
                    'max_tokens': 5,
                },
                timeout=15,
            )
            print(model, r.status_code, r.text[:200])
        except Exception as e:
            print(model, 'ERROR', e)
else:
    print('No OpenAI API key found.')

print('\nTesting Hugging Face...')
token = os.getenv('HF_API_TOKEN') or os.getenv('HUGGINGFACE_API_TOKEN')
if token:
    headers = {'Authorization': f'Bearer {token}'}
    for model in ['meta-llama/Llama-2-7b-chat-hf', 'gpt2']:
        try:
            r = requests.post(
                f'https://api-inference.huggingface.co/models/{model}',
                headers=headers,
                json={'inputs': 'Hello there'},
                timeout=20,
            )
            print(model, r.status_code, str(r.text)[:200])
        except Exception as e:
            print(model, 'ERROR', e)
else:
    print('No Hugging Face token found.')
PY
```

## Interpreting the result

A model is considered functional when it does all of the following:

- the credentials are valid,
- the endpoint is reachable,
- the requested model name is authorized for the account,
- and a sample request succeeds with a valid response payload.

If several model providers are installed, the selection priority should usually be:

1. provider with valid credentials and successful live response
2. lowest latency that still meets quality requirements
3. best fit for the task and cost constraints
4. consistent availability over a short test period

## Practical note

This folder itself is not a code project and does not include source files for the model APIs. To verify live functionality, you need to run the checks from a machine or environment where the API keys are available.

## Next steps

- Use the same validation procedure for any additional models you installed.
- Record the model name, response status, and speed for each endpoint.
- Choose the one that is both successful and fit-for-purpose.
