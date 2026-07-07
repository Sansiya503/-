#!/usr/bin/env python3
"""Send a daily bedtime reminder to Telegram."""

from __future__ import annotations

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from weather_agent import DEFAULT_TIMEZONE, env, env_int, send_telegram


DEFAULT_BEDTIME_HOUR = 23
DEFAULT_BEDTIME_MINUTE = 55
DEFAULT_BEDTIME_MESSAGE = "산시야님, 곧 12시입니다. 주무실 시간입니다."


def is_allowed_reminder_time(now: datetime, hour: int, minute: int) -> bool:
    if hour < 0 or hour > 23:
        raise ValueError("hour must be between 0 and 23")

    if minute < 0 or minute > 59:
        raise ValueError("minute must be between 0 and 59")

    return now.hour == hour and now.minute == minute


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a bedtime reminder to Telegram.")
    parser.add_argument("--dry-run", action="store_true", help="Print the reminder without sending it.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Send even when the current time is outside the bedtime reminder minute.",
    )
    parser.add_argument("--message", help="Override the reminder message.")
    args = parser.parse_args()

    timezone = env("TIMEZONE", DEFAULT_TIMEZONE)
    reminder_hour = env_int("BEDTIME_HOUR", DEFAULT_BEDTIME_HOUR)
    reminder_minute = env_int("BEDTIME_MINUTE", DEFAULT_BEDTIME_MINUTE)
    message = args.message or env("BEDTIME_MESSAGE", DEFAULT_BEDTIME_MESSAGE)

    if args.dry_run:
        print(message)
        return 0

    now = datetime.now(ZoneInfo(timezone))
    if not args.force and not is_allowed_reminder_time(now, reminder_hour, reminder_minute):
        print(
            "Skipped Telegram bedtime reminder: "
            f"current time {now:%Y-%m-%d %H:%M:%S %Z} is not "
            f"{reminder_hour:02d}:{reminder_minute:02d}."
        )
        return 0

    token = env("TELEGRAM_BOT_TOKEN")
    chat_id = env("TELEGRAM_CHAT_ID")

    send_telegram(token, chat_id, message)
    print("Telegram bedtime reminder sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
