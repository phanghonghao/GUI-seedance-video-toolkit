# Seedream 文生图 API 示例
# 平台: 并行科技 llmapi.paratera.com
# 模型: Doubao-Seedream-3.0-T2I

## curl 示例

```bash
curl --request POST \
  --url https://llmapi.paratera.com/v1/images/generations \
  --header "Authorization: Bearer <你的API Key>" \
  --header "Content-Type: application/json" \
  --data '{
    "model": "Doubao-Seedream-3.0-T2I",
    "prompt": "想要图片的内容描述",
    "n": 1,
    "size": "1024x1024"
  }'
```

## 响应格式

```json
{
  "data": [
    {
      "url": "https://...",
      "b64_json": null
    }
  ]
}
```

## Python 示例

```python
import requests

API_KEY = "你的key"
BASE_URL = "https://llmapi.paratera.com/v1"

def generate_image(prompt, size="1024x1024"):
    url = f"{BASE_URL}/images/generations"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "Doubao-Seedream-3.0-T2I",
        "prompt": prompt,
        "n": 1,
        "size": size
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

if __name__ == "__main__":
    result = generate_image("一只可爱的猫咪在花园里玩耍")
    print(result)
```
