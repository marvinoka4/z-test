import os, sys, json, requests, time

def try_openai():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        print("OPENAI_API_KEY: not set")
        return
    print("OPENAI_API_KEY: present (will attempt test calls)")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    models = ["gpt-5-mini","gpt-4","gpt-3.5-turbo"]
    for m in models:
        try:
            resp = requests.post("https://api.openai.com/v1/chat/completions",
                headers=headers,
                json={"model": m, "messages":[{"role":"user","content":"hello"}], "max_tokens":1}, timeout=10)
            print(f"OpenAI model {m}: status {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            print(f"OpenAI model {m}: error {e}")

def try_hf():
    token = os.getenv("HF_API_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
    if not token:
        print("HF_API_TOKEN: not set")
        return
    print("HF_API_TOKEN: present (will attempt test calls)")
    models = ["gpt-neo-2.7B","meta-llama/Llama-2-7b-chat-hf"]
    for m in models:
        url = f"https://api-inference.huggingface.co/models/{m}"
        try:
            resp = requests.post(url, headers={"Authorization": f"Bearer {token}"}, json={"inputs":"Hello"}, timeout=15)
            print(f"HF model {m}: status {resp.status_code} - {str(resp.json())[:200]}")
        except Exception as e:
            print(f"HF model {m}: error {e}")

if __name__ == "__main__":
    print("Environment vars (present/absent):")
    for k in ["OPENAI_API_KEY","HF_API_TOKEN","HUGGINGFACE_API_TOKEN"]:
        print(f" - {k}: {'set' if os.getenv(k) else 'not set'}")
    print()
    try_openai()
    print()
    try_hf()
