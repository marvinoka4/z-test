import json
import os
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


DEFAULT_PORT = int(os.getenv("NVIDIA_PROXY_PORT", "8000"))
DEFAULT_HOST = os.getenv("NVIDIA_PROXY_HOST", "127.0.0.1")


def get_first_env(*names):
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return None


def get_api_key():
    return get_first_env("NVIDIA_API_KEY", "NVIDIA_NIM_API_KEY", "NGC_API_KEY")


def get_model_candidates_from_env():
    raw = get_first_env("NVIDIA_MODELS", "NVIDIA_MODEL_LIST")
    if not raw:
        return []
    items = [part.strip() for part in raw.split(",") if part.strip()]
    return items


def fetch_live_models(api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(
        "https://integrate.api.nvidia.com/v1/models",
        headers=headers,
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return []

    items = data.get("data", []) if isinstance(data, dict) else []
    model_ids = []
    for item in items:
        if isinstance(item, dict) and item.get("id"):
            model_ids.append(item["id"])
    return model_ids


def resolve_model_candidates():
    env_models = get_model_candidates_from_env()
    if env_models:
        return env_models

    key = get_api_key()
    if key:
        live_models = fetch_live_models(key)
        if live_models:
            return live_models

    return [
        "meta/llama-3.1-8b-instruct",
        "meta/llama-3.1-70b-instruct",
        "mistralai/mixtral-8x7b-instruct-v0.1",
        "google/gemma-2-9b-it",
    ]


def build_nvidia_headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def call_nvidia_chat(model_name, payload, api_key):
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    request_payload = payload.copy()
    request_payload["model"] = model_name
    body = json.dumps(request_payload).encode("utf-8")
    headers = build_nvidia_headers(api_key)
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        return exc.code, err_body
    except Exception as exc:
        return None, str(exc)


def parse_json_body(raw_body):
    if not raw_body:
        return {}
    try:
        return json.loads(raw_body.decode("utf-8", errors="replace"))
    except Exception:
        return {}


class ProxyHandler(BaseHTTPRequestHandler):
    server_version = "NVIDIAFallbackProxy/1.0"

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health":
            self.send_json(200, {"status": "ok", "proxy": "nvidia-fallback"})
            return

        if parsed.path == "/v1/models":
            models = resolve_model_candidates()
            self.send_json(200, {"object": "list", "data": [{"id": m, "object": "model"} for m in models]})
            return

        self.send_json(404, {"error": {"message": "Not found", "type": "not_found"}})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path not in ("/v1/chat/completions", "/v1/completions"):
            self.send_json(404, {"error": {"message": "Route not found", "type": "not_found"}})
            return

        api_key = get_api_key()
        if not api_key:
            self.send_json(401, {"error": {"message": "NVIDIA_API_KEY is not set", "type": "authentication_error"}})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            payload = parse_json_body(raw)
        except Exception:
            self.send_json(400, {"error": {"message": "Invalid JSON payload", "type": "invalid_request"}})
            return

        requested_model = payload.get("model")
        model_candidates = []
        if requested_model:
            model_candidates.append(str(requested_model))

        for item in resolve_model_candidates():
            if item not in model_candidates:
                model_candidates.append(item)

        last_error = None
        for model_name in model_candidates:
            status, body_text = call_nvidia_chat(model_name, payload, api_key)
            if status is not None and 200 <= status < 300:
                try:
                    parsed_response = json.loads(body_text)
                except Exception:
                    parsed_response = {"raw": body_text}
                self.send_json(status, parsed_response)
                return

            last_error = {"model": model_name, "status": status, "body": body_text}
            try:
                error_json = json.loads(body_text)
                if isinstance(error_json, dict):
                    last_error = {"model": model_name, "status": status, "error": error_json}
            except Exception:
                pass

        self.send_json(502, {"error": {"message": "All NVIDIA model attempts failed", "type": "model_error", "details": last_error}})

    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    host = DEFAULT_HOST
    port = DEFAULT_PORT
    server = ThreadingHTTPServer((host, port), ProxyHandler)
    print(f"NVIDIA fallback proxy listening on http://{host}:{port}")
    print("Set NVIDIA_API_KEY or NVIDIA_NIM_API_KEY before using it.")
    print("Use a local VS Code provider pointed at http://127.0.0.1:8000/v1")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping NVIDIA fallback proxy")
        server.server_close()
