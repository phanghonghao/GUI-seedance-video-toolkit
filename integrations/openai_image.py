from __future__ import annotations

import base64
import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from core.config_loader import env_or_value, load_json_config


@dataclass(slots=True)
class OpenAIImageClient:
    api_key: str
    base_url: str
    model: str

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    @classmethod
    def from_environment(cls) -> "OpenAIImageClient":
        config_path = Path(__file__).resolve().parent.parent / "config" / "providers.json"
        provider_config = load_json_config(config_path, default={}).get("image", {})
        env_map = provider_config.get("env", {})
        return cls(
            api_key=str(env_or_value(env_map.get("api_key", "VIDEO_FULL_IMAGE_API_KEY"), provider_config.get("api_key", ""))).strip(),
            base_url=str(env_or_value(env_map.get("base_url", "VIDEO_FULL_IMAGE_API_BASE"), provider_config.get("base_url", ""))).strip().rstrip("/"),
            model=str(env_or_value(env_map.get("model", "VIDEO_FULL_IMAGE_MODEL"), provider_config.get("model", "gpt-image-1"))).strip(),
        )

    def generate_text_to_image(self, prompt: str, output_path: Path) -> None:
        config_path = Path(__file__).resolve().parent.parent / "config" / "providers.json"
        provider_config = load_json_config(config_path, default={}).get("image", {})
        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": provider_config.get("size", "1536x1024"),
        }
        self._request_image(payload, output_path)

    def generate_image_to_image(self, prompt: str, source_image: Path, output_path: Path) -> None:
        config_path = Path(__file__).resolve().parent.parent / "config" / "providers.json"
        provider_config = load_json_config(config_path, default={}).get("image", {})
        image_b64 = base64.b64encode(source_image.read_bytes()).decode("utf-8")
        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": provider_config.get("size", "1536x1024"),
            "image": image_b64,
        }
        self._request_image(payload, output_path)

    def _request_image(self, payload: dict, output_path: Path) -> None:
        request = urllib.request.Request(
            url=f"{self.base_url}/images/generations",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
        item = (data.get("data") or [{}])[0]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if item.get("b64_json"):
            output_path.write_bytes(base64.b64decode(item["b64_json"]))
            return
        if item.get("url"):
            with urllib.request.urlopen(item["url"], timeout=180) as image_response:
                output_path.write_bytes(image_response.read())
            return
        raise RuntimeError("Image provider did not return b64_json or url.")
