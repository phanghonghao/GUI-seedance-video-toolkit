#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智谱AI GLM LLM 连通性测试
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_client import OpenAIClient

import os

# 智谱AI凭据 — 从环境变量读取，请在运行前设置
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY", "")
ZHIPU_BASE_URL = os.environ.get("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/")

if not ZHIPU_API_KEY:
    print("=" * 60)
    print("请先设置智谱AI API密钥：")
    print("  set ZHIPU_API_KEY=your-api-key-here")
    print("  python tests/test_zhipu_llm.py")
    print("=" * 60)
    sys.exit(1)

results = []


def test_connection():
    """测试连接"""
    print("\n" + "=" * 60)
    print("测试1: API连接")
    print("=" * 60)

    client = OpenAIClient(
        api_key=ZHIPU_API_KEY,
        base_url=ZHIPU_BASE_URL,
        model="glm-4.7"
    )

    success, msg = client.test_connection()
    if success:
        print(f"  [PASS] {msg}")
    else:
        print(f"  [FAIL] {msg}")

    results.append(("连接", success, msg))
    return success, client


def test_chat_completion(client):
    """测试场景生成对话"""
    print("\n" + "=" * 60)
    print("测试2: 场景生成对话 (chat_completion)")
    print("=" * 60)

    messages = [
        {"role": "system", "content": "你是一个专业的视频场景规划师。"},
        {"role": "user", "content": "请为一个智能手表产品介绍视频规划3个场景，每个场景用一句话描述。"}
    ]

    try:
        response = client.chat_completion(messages=messages, model="glm-4.7")

        content = response.get("content", "")
        model = response.get("model", "")
        usage = response.get("usage", {})

        if content:
            print(f"  [PASS] 对话成功")
            print(f"  模型: {model}")
            print(f"  Token使用: {usage.get('total_tokens', 0)}")
            print(f"  回复内容:")
            for line in content.split("\n"):
                print(f"    {line}")
            results.append(("场景生成", True, f"回复{len(content)}字"))
            return True
        else:
            print(f"  [FAIL] API返回空内容")
            results.append(("场景生成", False, "返回空内容"))
            return False

    except Exception as e:
        print(f"  [FAIL] {e}")
        results.append(("场景生成", False, str(e)))
        return False


def main():
    print("智谱AI GLM LLM 连通性测试")
    print("=" * 60)

    # 测试连接
    success, client = test_connection()
    if not success:
        print("\n连接失败，跳过后续测试")
    else:
        # 测试对话
        test_chat_completion(client)

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
