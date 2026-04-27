#!/usr/bin/env python3
"""CLI helper — send a push notification or schedule one.

Usage:
  python3 notify.py "消息内容"
  python3 notify.py "消息内容" --title "标题" --priority high
  python3 notify.py "消息内容" --schedule "2026-04-22T09:00:00"
  python3 notify.py "消息内容" --cron "0 9 * * 1-5"
"""
import argparse
import json
import os
import sys
import urllib.request

BASE_URL = os.getenv("MOBILE_SERVER_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "change-me-long-random-string")


def _post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def main():
    parser = argparse.ArgumentParser(description="发送手机推送通知")
    parser.add_argument("message", help="消息内容")
    parser.add_argument("--title", default="Claude 消息", help="通知标题")
    parser.add_argument("--priority", default="default", choices=["min", "low", "default", "high", "urgent"])
    parser.add_argument("--tags", default="", help="ntfy 标签，逗号分隔，如 bell,warning")
    parser.add_argument("--schedule", metavar="DATETIME", help="定时发送，ISO8601 格式")
    parser.add_argument("--cron", help="Cron 表达式，如 '0 9 * * 1-5'")
    args = parser.parse_args()

    tags = [t for t in args.tags.split(",") if t]

    if args.schedule or args.cron:
        payload = {"title": args.title, "message": args.message, "priority": args.priority, "tags": tags}
        if args.schedule:
            payload["run_at"] = args.schedule
        if args.cron:
            payload["cron"] = args.cron
        result = _post("/schedule", payload)
        print(f"已计划: job_id={result.get('job_id')}, run_at={result.get('run_at')}, cron={result.get('cron')}")
    else:
        payload = {"title": args.title, "message": args.message, "priority": args.priority, "tags": tags}
        result = _post("/notify", payload)
        print(f"已发送: {result.get('status')}")


if __name__ == "__main__":
    main()
