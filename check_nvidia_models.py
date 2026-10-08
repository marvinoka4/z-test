import json
import os
import urllib.error
import urllib.request


def get_nvidia_key() -> str | None:
    for name in [
        "NVIDIA_API_KEY",
        "NVIDIA_NIM_API_KEY",
        "NGC_API_KEY",
    ]:
        value = os.getenv(name)
        if value:
            return value
    return None


def http_json(method: str, url: str, headers: dict, payload: dict | None = None):
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, body


def test_nvidia_models(key: str):
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    print("Testing NVIDIA model listing...")
    try:
        status, body = http_json("GET", "https://integrate.api.nvidia.com/v1/models", headers)
        print(f"GET /v1/models -> status {status}")
        print(body[:500])
        candidates = json.loads(body).get("data", [])
        model_ids = [item.get("id") for item in candidates if isinstance(item, dict) and item.get("id")]
    except Exception as exc:
        print(f"GET /v1/models -> error: {exc}")
        model_ids = []

    if not model_ids:
        print("No model list was available from /v1/models; stopping.")
        return

    print("\nTesting available models from the live list:")
    for model_name in model_ids[:5]:
        print(f"\nTesting model: {model_name}")
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Say hello in one word."}],
            "max_tokens": 8,
            "temperature": 0.1,
        }
        try:
            status, body = http_json(
                "POST",
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers,
                payload,
            )
            print(f"POST /v1/chat/completions -> status {status}")
            print(body[:500])
        except urllib.error.HTTPError as exc:
            print(f"POST /v1/chat/completions -> status {exc.code}")
            print(exc.read().decode("utf-8", errors="replace")[:500])
        except Exception as exc:
            print(f"POST /v1/chat/completions -> error: {exc}")


if __name__ == "__main__":
    print("Environment vars (present/absent):")
    for key in ["NVIDIA_API_KEY", "NVIDIA_NIM_API_KEY", "NGC_API_KEY"]:
        print(f" - {key}: {'set' if os.getenv(key) else 'not set'}")
    print()

    api_key = get_nvidia_key()
    if not api_key:
        print("NVIDIA API key is not set. Set NVIDIA_API_KEY or NVIDIA_NIM_API_KEY before running this check.")
        raise SystemExit(0)

    test_nvidia_models(api_key)
