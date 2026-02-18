import os
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


class GroqClient:
    def __init__(self):
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.timeout_s = float(os.getenv("GROQ_TIMEOUT_S", "60"))
        self.max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "350"))
        self.temperature = float(os.getenv("GROQ_TEMPERATURE", "0.3"))
        self.executor = ThreadPoolExecutor(max_workers=2)

    def _get_api_key(self) -> str:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            return api_key

        # Some dev setups (IDE/uvicorn reload) may not inherit newly set shell env vars.
        # As a fallback, try loading backend/.env at runtime.
        if load_dotenv is not None:
            try:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                env_path = os.path.join(base_dir, ".env")
                load_dotenv(dotenv_path=env_path, override=False)
                api_key = os.getenv("GROQ_API_KEY")
                if api_key:
                    return api_key
            except Exception:
                pass

        raise RuntimeError("GROQ_API_KEY is not set")

    def _chat_completions_sync(self, *, system_prompt: str, user_prompt: str) -> str:
        api_key = self._get_api_key()
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout_s)
        if resp.status_code >= 400:
            body_preview = resp.text
            try:
                data = resp.json()
                if isinstance(data, dict):
                    err = data.get("error")
                    if isinstance(err, dict) and err.get("message"):
                        body_preview = err.get("message")
                    elif data.get("message"):
                        body_preview = data.get("message")
            except Exception:
                pass

            raise RuntimeError(f"Groq HTTP {resp.status_code}: {body_preview}")

        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            return "I don't know."
        message = (choices[0].get("message") or {}).get("content")
        return (message or "I don't know.").strip()

    async def answer(self, *, system_prompt: str, user_prompt: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            lambda: self._chat_completions_sync(system_prompt=system_prompt, user_prompt=user_prompt),
        )


groq_client = GroqClient()
