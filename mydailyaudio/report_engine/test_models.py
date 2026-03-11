#!/usr/bin/env python3
"""
批量评估 OpenRouter 免费模型性能
"""

import os
import time
import json
from openai import OpenAI
from datetime import datetime

# 你的 OpenRouter API Key
API_KEY = os.getenv("OPENROUTER_API_KEY") or "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"

# 模型列表
MODELS = [
    "z-ai/glm-4.5-air:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "arcee-ai/trinity-mini:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "openai/gpt-oss-120b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-coder:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
    "openai/gpt-oss-20b:free",
    "google/gemma-3-27b-it:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
    "qwen/qwen3-4b:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "google/gemma-3-4b-it:free",
    "google/gemma-3n-e4b-it:free",
    "google/gemma-3-12b-it:free",
    "google/gemma-3n-e2b-it:free",
    "nvidia/llama-nemotron-embed-vl-1b-v2:free",
]

PROMPT_TEMPLATE = """请将以下内容改写成一段简洁、易懂的中文（30-70字），要求：
- 忠实原意，不添加不存在的信息
- 用生活化语言，避免"修复""重构""增强"等黑话
- 如果原文提到用户的好处（更安全、更方便、省时），请保留
- 如果原文偏技术，请提炼一句通俗说明
- 不要主动加入"OpenClaw""ChatGPT"等工具名（除非原文出现）

{source_text}

请严格按 JSON 格式输出，只包含一个字段：{{"summary": "你的总结"}}

不要输出任何其他内容（包括思考过程、解释、markdown 标记）。"""

def test_model(model_name: str):
    client = OpenAI(api_key=API_KEY, base_url="https://openrouter.ai/api/v1")
    # 使用较长且真实的新闻内容，测试模型的实际摘要能力
    title = "Meta 发布四款新芯片用于 AI 和推荐系统，同时继续采购英伟达设备"
    content = """Meta 公司近日发布了四款全新芯片，专门用于人工智能和推荐系统。这些芯片是 Meta 自研硬件的最新成果，旨在降低对英伟达的依赖并提升效率。与此同时，Meta 仍将继续采购英伟达的设备，显示出其在 AI 硬件上的双轨策略——既自主创新，又保持外部合作。新芯片将首先应用于 Meta 的社交媒体平台和 VR 设备中，未来可能向第三方开放。"""
    source_text = f"标题：{title}\n原文：{content}"
    prompt = PROMPT_TEMPLATE.format(source_text=source_text)

    start = time.time()
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=2000,  # 与 ai-audio-daily 生产环境完全一致
            extra_headers={
                "HTTP-Referer": "https://github.com/urright/mydailyaudio",
                "X-Title": "MyDailyAudio"
            }
        )
        latency = time.time() - start
        msg = response.choices[0].message
        # 提取文本：优先 content，尝试解析 JSON
        text = msg.content
        if text:
            import json, re
            try:
                data = json.loads(text)
                if isinstance(data, dict) and data.get("summary"):
                    summary = data["summary"].strip()
                    if 5 < len(summary) < 300:
                        text = summary
                    else:
                        text = text.strip()
                else:
                    text = text.strip()
            except json.JSONDecodeError:
                # 尝试提取 JSON 块
                json_match = re.search(r'\{[^}]*"summary"\s*:.*?\}', text, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group())
                        if data.get("summary"):
                            text = data["summary"].strip()
                        else:
                            text = text.strip()
                    except Exception:
                        text = text.strip()
                else:
                    text = text.strip()
        else:
            # content 为空，尝试 reasoning
            try:
                dump = msg.model_dump()
                reasoning = dump.get('reasoning') or ''
                if reasoning:
                    # 尝试 JSON
                    json_match = re.search(r'\{[^}]*"summary"\s*:.*?\}', reasoning, re.DOTALL)
                    if json_match:
                        try:
                            data = json.loads(json_match.group())
                            if data.get("summary"):
                                text = data["summary"].strip()
                            else:
                                text = reasoning[-200:].strip()
                        except Exception:
                            text = reasoning[-200:].strip()
                    else:
                        # 回退：取最后一句
                        import re as re2
                        snippet = reasoning[-300:] if len(reasoning) > 300 else reasoning
                        sentences = re2.split(r'[。！？]+', snippet)
                        sentences = [s.strip() for s in sentences if 5 < len(s.strip()) < 300]
                        text = sentences[-1] if sentences else reasoning[-200:].strip()
            except Exception:
                text = ""

        return {
            "model": model_name,
            "status": "ok",
            "latency": round(latency, 2),
            "text": text[:200] if text else "",
            "tokens": getattr(response.usage, 'total_tokens', None) if hasattr(response, 'usage') else None,
            "finish_reason": response.choices[0].finish_reason
        }
    except Exception as e:
        return {
            "model": model_name,
            "status": "error",
            "error": str(e)[:200]
        }

def main():
    results = []
    print(f"⏳ 开始测试 {len(MODELS)} 个模型...")
    for i, model in enumerate(MODELS, 1):
        print(f"[{i}/{len(MODELS)}] 测试: {model}")
        res = test_model(model)
        results.append(res)
        # 避免限流：免费模型有严格速率限制，需要更长间隔
        time.sleep(5)  # 5 秒间隔（约 12 次/分钟，低于大多数限制）

    # 保存结果
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_file = f"model_eval_{timestamp}.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 测试完成，结果保存到: {out_file}")

    # 打印摘要
    print("\n📊 测试摘要:")
    for r in results:
        if r['status'] == 'ok':
            print(f"  ✅ {r['model']}: 延迟 {r['latency']}s, tokens {r.get('tokens','?')}, 文本长度 {len(r['text'])}")
        else:
            print(f"  ❌ {r['model']}: {r['error']}")

    # 综合评分：可用性 + 速度 + 摘要质量
    # 基础：无错误得 10 分
    # 延迟：<2s(10分), 2-4s(6分), 4-6s(3分), >6s(1分)
    # 文本长度：30-150字(10分)，过长或过短酌情扣分
    # finish_reason='stop' 表示正常结束(5分)
    print("\n🏆 初步排名（基于可用性、速度、质量）:")
    scored = []
    for r in results:
        if r['status'] != 'ok':
            score = 0
        else:
            score = 10  # 基础分
            # 延迟分
            lat = r['latency']
            if lat < 2:
                score += 10
            elif lat < 4:
                score += 6
            elif lat < 6:
                score += 3
            else:
                score += 1
            # 摘要长度分（30-150字为佳）
            text_len = len(r['text'])
            if 30 <= text_len <= 150:
                score += 10
            elif 20 <= text_len < 30:
                score += 5
            elif 150 < text_len <= 300:
                score += 5
            else:
                score += 0
            # 结束原因
            if r.get('finish_reason') == 'stop':
                score += 5
        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    for score, r in scored[:10]:
        print(f"  [{score}] {r['model']}")
        if r['status'] == 'ok':
            print(f"        延迟: {r['latency']}s, 长度: {len(r['text'])}, 摘要: {r['text'][:80]}...")

if __name__ == "__main__":
    main()