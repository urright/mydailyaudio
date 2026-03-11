#!/usr/bin/env python3
"""
Report Engine - 为单个 profile 生成日报
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime

from .collector import DataCollector
from .processor import ContentProcessor, OpenAIProvider, GroqProvider, OpenRouterProvider, OllamaProvider, HuggingFaceProvider, ArceeProvider, FallbackProvider
from .audio_generator import AudioGenerator
from .page_generator import PageGenerator
from .telegram_sender import TelegramSender

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def run_profile(profile, base_dir=None, repo_name="mydailyaudio", dry_run=False):
    """
    执行一个 profile 的完整日报生成流程。

    Args:
        profile: dict with keys:
            config_dir, output_dir, audio_subdir, url_path,
            telegram_bot_token, telegram_chat_id, name
        base_dir: mydailyaudio 根目录（默认当前目录）
        repo_name: GitHub repo name for URL construction
        dry_run: 如果 True，则不发送 Telegram

    Returns:
        dict with status, paths, message count, etc.
    """
    if base_dir is None:
        base_dir = Path.cwd()
    else:
        base_dir = Path(base_dir)

    config_dir = base_dir / profile['config_dir']
    output_dir = base_dir / profile['output_dir']
    audio_dir = output_dir / profile['audio_subdir']
    history_dir = base_dir / "history"
    ensure_dir(audio_dir)
    ensure_dir(history_dir)

    print(f"🚀 Running profile: {profile['name']}")
    print(f"📂 Config dir: {config_dir}")

    # 1. Collect
    collector = DataCollector(config_dir=str(config_dir))
    entries = collector.collect_all()
    if not entries:
        print("❌ No new entries collected")
        return {"status": "empty", "message": "No new entries"}

    # 2. Build provider list from profile config or environment
    # profile 可包含 'llm_providers': ['openai', 'groq', 'ollama', 'huggingface']
    # 顺序即为优先级
    def build_providers(profile):
        provider_map = {
            'openai': lambda: OpenAIProvider(),
            'groq': lambda: GroqProvider(),
            'openrouter': lambda: OpenRouterProvider(),
            'ollama': lambda: OllamaProvider(),
            'huggingface': lambda: HuggingFaceProvider(),
            'arcee': lambda: ArceeProvider(),
        }
        # 默认顺序
        default_order = ['openai', 'groq', 'ollama', 'huggingface']
        order = profile.get('llm_providers', default_order)
        providers = []
        for key in order:
            if key in provider_map:
                try:
                    providers.append(provider_map[key]())
                except Exception as e:
                    print(f"⚠️ 跳过提供商 {key}: {e}")
        if not providers:
            providers = [FallbackProvider()]
        return providers

    providers = build_providers(profile)
    processor = ContentProcessor(providers=providers)
    categorized = processor.process_all(entries)
    total_items = sum(len(v) for v in categorized.values())

    # 3. Audio
    date_str = datetime.now().strftime("%Y-%m-%d")
    audio_filename = f"{date_str}.mp3"
    audio_gen = AudioGenerator(output_dir=str(audio_dir))
    audio_file = audio_gen.generate_summary_audio(
        categorized,
        audio_filename=audio_filename
    )
    if not audio_file:
        return {"status": "error", "message": "Audio generation failed"}

    # 4. Save history
    history_file = history_dir / f"{date_str}_{profile['name']}.json"
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump({
            'profile': profile['name'],
            'date': date_str,
            'total_items': total_items,
            'categories': {k: len(v) for k, v in categorized.items()},
            'entries': categorized,
            'audio': audio_filename
        }, f, indent=2, ensure_ascii=False)
    print(f"✅ History saved: {history_file}")

    # 5. Generate detail page
    page_gen = PageGenerator(output_dir=str(output_dir))
    page_gen.generate_detail_page(
        categorized,
        date_str=date_str,
        audio_filename=audio_filename
    )

    # 6. Generate index page (homepage)
    pattern = f"*_{profile['name']}.json"
    history_files = sorted(history_dir.glob(pattern), reverse=True)[:30]
    days_metadata = []
    for hist_file in history_files:
        try:
            with open(hist_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            preview_items = []
            for cat, count in data['categories'].items():
                if count > 0:
                    cat_entries = data['entries'].get(cat, [])
                    if cat_entries:
                        preview_items.append(cat_entries[0]['short_summary'])
                    if len(preview_items) >= 3:
                        break
            days_metadata.append({
                'date': data['date'],
                'total_items': data['total_items'],
                'categories': data['categories'],
                'preview_items': preview_items[:3]
            })
        except Exception as e:
            print(f"⚠️ Failed to read history {hist_file}: {e}")
    page_gen.generate_index_page(days_metadata)
    print(f"✅ Homepage updated for profile {profile['name']}")

    # 7. Page URL
    url_path = profile.get('url_path', profile['output_dir'])
    if url_path.startswith('docs/'):
        url_path = url_path[5:]
    page_url = f"https://urright.github.io/{repo_name}/{url_path}/archive/{date_str}/"

    # 8. Telegram
    telegram_sent = False
    if not dry_run and profile.get('telegram_bot_token') and profile.get('telegram_chat_id'):
        telegram = TelegramSender(
            bot_token=profile['telegram_bot_token'],
            chat_id=profile['telegram_chat_id']
        )
        try:
            telegram.send_daily_report(
                page_url=page_url,
                audio_path=audio_file,
                total_items=total_items
            )
            telegram_sent = True
            print("✅ Telegram sent")
        except Exception as e:
            print(f"❌ Telegram failed: {e}")
    else:
        print("⚠️ Telegram not configured (or dry_run)")

    return {
        "status": "success",
        "profile": profile['name'],
        "date": date_str,
        "total_items": total_items,
        "audio_file": audio_file,
        "page_url": page_url,
        "telegram_sent": telegram_sent,
        "history_file": str(history_file)
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--audio-subdir", default="audio")
    parser.add_argument("--url-path", required=True)
    parser.add_argument("--telegram-bot-token", default=None)
    parser.add_argument("--telegram-chat-id", default=None)
    parser.add_argument("--profile-name", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    profile = {
        "name": args.profile_name,
        "config_dir": args.config_dir,
        "output_dir": args.output_dir,
        "audio_subdir": args.audio_subdir,
        "url_path": args.url_path,
        "telegram_bot_token": args.telegram_bot_token,
        "telegram_chat_id": args.telegram_chat_id,
    }

    result = run_profile(profile, dry_run=args.dry_run)
    print(json.dumps(result, indent=2, ensure_ascii=False))