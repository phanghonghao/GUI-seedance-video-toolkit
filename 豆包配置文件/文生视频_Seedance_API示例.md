# Seedance 文生视频 API 示例
# 平台: 并行科技 llmapi.paratera.com
# 模型: Doubao-Seedance-1.0-Pro

import requests

API_KEY = "你的key"
BASE_URL = "https://llmapi.paratera.com/v1"

def generate_video_from_text(prompt, ratio="16:9"):
    """
    通过文本生成视频
    :param prompt: 文本提示词
    :param ratio: 视频比例，默认为16:9
    :return: 响应结果（包含任务id）
    """
    url = f"{BASE_URL}/p001/contents/generations/tasks"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "Doubao-Seedance-1.0-Pro",
        "content": [
            {"type": "text", "text": f"{prompt} --ratio {ratio}"}
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def generate_video_from_image(prompt, image_url, ratio="adaptive", duration=5):
    """
    通过图片生成视频
    :param prompt: 文本提示词
    :param image_url: 图片URL
    :param ratio: 视频比例，默认为adaptive
    :param duration: 视频时长(秒)，默认为5
    :return: 响应结果（包含任务id）
    """
    url = f"{BASE_URL}/p001/contents/generations/tasks"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "Doubao-Seedance-1.0-Pro",
        "content": [
            {"type": "text", "text": f"{prompt} --ratio {ratio} --dur {duration}"},
            {"type": "image_url", "image_url": {"url": image_url}}
        ]
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def get_video_status(task_id):
    """
    查询视频生成状态
    :param task_id: 任务ID（从生成接口返回的 id 字段获取）
    :return: 响应结果，status 字段: running / succeeded / failed
    """
    url = f"{BASE_URL}/p001/contents/generations/tasks"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"filter.task_ids": task_id}
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 示例1: 文本生成视频
    text_response = generate_video_from_text(
        "多个镜头。汤姆猫正在追老鼠杰瑞，在花园的草地上"
    )
    print("文本生成视频响应:", text_response)

    # 示例2: 图片生成视频
    image_response = generate_video_from_image(
        prompt="一只大熊猫正安静的坐着",
        image_url="https://seopic.699pic.com/photo/50032/8264.jpg_wh1200.jpg"
    )
    print("图片生成视频响应:", image_response)

    # 示例3: 查询视频状态
    if "id" in text_response:
        status_response = get_video_status(text_response["id"])
        print("视频生成状态:", status_response)
