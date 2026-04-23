#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doubao API 连通性测试
测试并行科技的豆包文生图/文生视频API
"""

import sys
import time
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_client import OpenAIClient

import os

# 并行科技凭据 — 从环境变量读取，请在运行前设置
PARATERA_API_KEY = os.environ.get("PARATERA_API_KEY", "")
PARATERA_BASE_URL = os.environ.get("PARATERA_BASE_URL", "https://llmapi.paratera.com/v1/")

if not PARATERA_API_KEY:
    print("=" * 60)
    print("请先设置并行科技API密钥：")
    print("  set PARATERA_API_KEY=your-api-key-here")
    print("  python tests/test_doubao_api.py")
    print("=" * 60)
    sys.exit(1)

results = []


def test_image_generation():
    """测试文生图API"""
    print("\n" + "=" * 60)
    print("测试1: 文生图 (Doubao-Seedream-3.0-T2I)")
    print("=" * 60)

    client = OpenAIClient(
        api_key=PARATERA_API_KEY,
        base_url=PARATERA_BASE_URL,
        model="Doubao-Seedream-3.0-T2I"
    )

    success, message, data = client.test_image_generation("一只橙色小猫在草地上玩耍")

    if success:
        print(f"  [PASS] {message}")
        if data.get("images"):
            print(f"  图片URL: {data['images'][0][:80]}...")
    else:
        print(f"  [FAIL] {message}")

    results.append(("文生图", success, message))
    return success


def test_video_generation():
    """测试文生视频API"""
    print("\n" + "=" * 60)
    print("测试2: 文生视频 (Doubao-Seedance-1.0-Pro)")
    print("=" * 60)

    client = OpenAIClient(
        api_key=PARATERA_API_KEY,
        base_url=PARATERA_BASE_URL,
        model="Doubao-Seedance-1.0-Pro"
    )

    success, message, data = client.test_video_generation("海浪拍打金色沙滩")

    if success:
        print(f"  [PASS] {message}")
        task_id = data.get("task_id", "")
        print(f"  任务ID: {task_id}")

        # 轮询任务状态（可选，最长60秒）
        if task_id:
            print("\n  轮询视频任务状态...")
            max_wait = 60
            wait_time = 0
            while wait_time < max_wait:
                time.sleep(5)
                wait_time += 5
                try:
                    status_resp = client.query_video_task(task_id)
                    items = status_resp.get("items") or status_resp.get("data") or []
                    if items:
                        status = items[0].get("status", "")
                        print(f"    [{wait_time}s] 状态: {status}")
                        if status == "succeeded":
                            video_url = (items[0].get("content") or {}).get("video_url", "")
                            print(f"    视频URL: {video_url[:80]}...")
                            results.append(("视频轮询", True, f"视频生成成功"))
                            return True
                        elif status == "failed":
                            print(f"    [FAIL] 视频生成失败")
                            results.append(("视频轮询", False, "视频生成失败"))
                            return False
                    else:
                        print(f"    [{wait_time}s] 等待中...")
                except Exception as e:
                    print(f"    [{wait_time}s] 查询异常: {e}")
            print(f"  [WARN] 轮询超时({max_wait}s)，但任务创建成功")
            results.append(("视频轮询", False, f"轮询超时{max_wait}s"))
    else:
        print(f"  [FAIL] {message}")
        results.append(("视频轮询", False, "任务创建失败"))

    return success


def main():
    print("Doubao API 连通性测试")
    print("=" * 60)

    # 测试连接
    print("\n测试0: API连接")
    print("-" * 40)
    client = OpenAIClient(
        api_key=PARATERA_API_KEY,
        base_url=PARATERA_BASE_URL
    )
    success, msg = client.test_connection()
    if success:
        print(f"  [PASS] {msg}")
    else:
        print(f"  [FAIL] {msg}")
    results.append(("连接", success, msg))

    # 测试文生图
    test_image_generation()

    # 测试文生视频
    test_video_generation()

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(1 for _, s, _ in results if s)
    total = len(results)
    for name, success, msg in results:
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {name}: {msg}")

    print(f"\n结果: {passed}/{total} 通过")
    return passed == total


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
