from __future__ import annotations

import base64
import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from core.config_loader import env_or_value, load_json_config


@dataclass(slots=True)
class GenericTaskVideoClient:
    api_key: str
    task_url: str
    status_url: str
    model: str

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.task_url and self.status_url and self.model)

    @classmethod
    def from_environment(cls) -> "GenericTaskVideoClient":
        config_path = Path(__file__).resolve().parent.parent / "config" / "providers.json"
        provider_config = load_json_config(config_path, default={}).get("video", {})
        env_map = provider_config.get("env", {})
        task_url = str(env_or_value(env_map.get("task_url", "VIDEO_FULL_VIDEO_TASK_URL"), provider_config.get("task_url", ""))).strip()
        status_url = str(env_or_value(env_map.get("status_url", "VIDEO_FULL_VIDEO_STATUS_URL"), provider_config.get("status_url", task_url))).strip()
        return cls(
            api_key=str(env_or_value(env_map.get("api_key", "VIDEO_FULL_VIDEO_API_KEY"), provider_config.get("api_key", ""))).strip(),
            task_url=task_url,
            status_url=status_url,
            model=str(env_or_value(env_map.get("model", "VIDEO_FULL_VIDEO_MODEL"), provider_config.get("model", "generic-video-model"))).strip(),
        )

    def generate_text_to_video(self, prompt: str, output_path: Path) -> None:
        content = [{"type": "text", "text": prompt}]
        self._submit_poll_download(content, output_path)

    def generate_image_to_video(self, prompt: str, source_image: Path, output_path: Path) -> None:
        image_b64 = base64.b64encode(source_image.read_bytes()).decode("utf-8")
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
        ]
        self._submit_poll_download(content, output_path)

    def _submit_poll_download(self, content: list[dict], output_path: Path) -> None:
        payload = {"model": self.model, "content": content}
        submit_request = urllib.request.Request(
            url=self.task_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        with urllib.request.urlopen(submit_request, timeout=180) as response:
            submit_data = json.loads(response.read().decode("utf-8"))
        task_id = submit_data.get("id") or submit_data.get("task_id")
        if not task_id:
            raise RuntimeError("Video provider did not return a task id.")

        video_url = self._poll_for_video_url(task_id)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(video_url, timeout=600) as response:
            output_path.write_bytes(response.read())

    def _poll_for_video_url(self, task_id: str) -> str:
        config_path = Path(__file__).resolve().parent.parent / "config" / "providers.json"
        provider_config = load_json_config(config_path, default={}).get("video", {})
        max_polls = int(provider_config.get("max_polls", 60))
        poll_seconds = int(provider_config.get("poll_seconds", 5))
        for _ in range(max_polls):
            query = urllib.parse.urlencode({"filter.task_ids": task_id})
            url = self.status_url
            connector = "&" if "?" in url else "?"
            request = urllib.request.Request(
                url=f"{url}{connector}{query}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                method="GET",
            )
            with urllib.request.urlopen(request, timeout=180) as response:
                status_data = json.loads(response.read().decode("utf-8"))
            items = status_data.get("items") or status_data.get("data") or []
            if items:
                item = items[0]
                status = item.get("status", "")
                if status == "succeeded":
                    video_url = (item.get("content") or {}).get("video_url") or item.get("video_url")
                    if video_url:
                        return video_url
                if status == "failed":
                    raise RuntimeError(f"Video task failed: {item}")
            time.sleep(poll_seconds)
        raise TimeoutError(f"Video task timed out: {task_id}")
