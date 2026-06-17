#!/usr/bin/env python3
"""Send a daily weather and fine dust summary to Telegram."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "Asia/Seoul"


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urlencode(params, doseq=True)
    request = Request(f"{url}?{query}", headers={"User-Agent": "telegram-weather-agent/1.0"})

    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach {url}: {exc.reason}") from exc


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "telegram-weather-agent/1.0"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from Telegram: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach Telegram: {exc.reason}") from exc


def dust_grade(kind: str, value: float | None) -> str:
    if value is None:
        return "정보 없음"

    if kind == "pm10":
        if value <= 30:
            return "좋음"
        if value <= 80:
            return "보통"
        if value <= 150:
            return "나쁨"
        return "매우 나쁨"

    if value <= 15:
        return "좋음"
    if value <= 35:
        return "보통"
    if value <= 75:
        return "나쁨"
    return "매우 나쁨"


def nearest_hour_value(times: list[str], values: list[float | None], now: datetime) -> float | None:
    if not times or not values:
        return None

    target = now.replace(minute=0, second=0, microsecond=0).replace(tzinfo=None)
    try:
        index = times.index(target.isoformat(timespec="minutes"))
    except ValueError:
        index = min(range(len(times)), key=lambda i: abs(datetime.fromisoformat(times[i]).replace(tzinfo=None) - target))
    return values[index]


def today_max(values: list[float | None]) -> float | None:
    numbers = [value for value in values if value is not None]
    return max(numbers) if numbers else None


def format_number(value: float | int | None, suffix: str = "") -> str:
    if value is None:
        return "정보 없음"
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.1f}{suffix}"
    return f"{int(value)}{suffix}"


def build_message(location: str, latitude: str, longitude: str, timezone: str) -> str:
    now = datetime.now(ZoneInfo(timezone))

    forecast = get_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
            ],
            "timezone": timezone,
            "forecast_days": 1,
        },
    )

    air = get_json(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ["pm10", "pm2_5"],
            "timezone": timezone,
            "forecast_days": 1,
        },
    )

    daily = forecast.get("daily", {})
    hourly_air = air.get("hourly", {})
    pm10_now = nearest_hour_value(hourly_air.get("time", []), hourly_air.get("pm10", []), now)
    pm25_now = nearest_hour_value(hourly_air.get("time", []), hourly_air.get("pm2_5", []), now)
    pm10_peak = today_max(hourly_air.get("pm10", []))
    pm25_peak = today_max(hourly_air.get("pm2_5", []))

    temp_min = daily.get("temperature_2m_min", [None])[0]
    temp_max = daily.get("temperature_2m_max", [None])[0]
    rain_probability = daily.get("precipitation_probability_max", [None])[0]

    return "\n".join(
        [
            f"{now:%Y-%m-%d} {location} 날씨",
            "",
            f"기온: {format_number(temp_min, '도')} ~ {format_number(temp_max, '도')}",
            f"강수확률: 최대 {format_number(rain_probability, '%')}",
            "",
            f"미세먼지 PM10: {format_number(pm10_now, '㎍/㎥')} ({dust_grade('pm10', pm10_now)})",
            f"초미세먼지 PM2.5: {format_number(pm25_now, '㎍/㎥')} ({dust_grade('pm25', pm25_now)})",
            f"오늘 예상 최고 PM10/PM2.5: {format_number(pm10_peak, '㎍/㎥')} / {format_number(pm25_peak, '㎍/㎥')}",
        ]
    )


def send_telegram(token: str, chat_id: str, text: str) -> None:
    response = post_json(
        f"https://api.telegram.org/bot{token}/sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        },
    )
    if not response.get("ok"):
        raise RuntimeError(f"Telegram rejected the message: {response}")


def sample_message(location: str) -> str:
    return "\n".join(
        [
            f"{datetime.now(ZoneInfo(DEFAULT_TIMEZONE)):%Y-%m-%d} {location} 날씨",
            "",
            "기온: 18도 ~ 27도",
            "강수확률: 최대 40%",
            "",
            "미세먼지 PM10: 42㎍/㎥ (보통)",
            "초미세먼지 PM2.5: 18㎍/㎥ (보통)",
            "오늘 예상 최고 PM10/PM2.5: 55㎍/㎥ / 24㎍/㎥",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Send daily weather and fine dust information to Telegram.")
    parser.add_argument("--dry-run", action="store_true", help="Print a sample message without calling APIs.")
    args = parser.parse_args()

    location = env("LOCATION_NAME", "서울")

    if args.dry_run:
        print(sample_message(location))
        return 0

    latitude = env("LATITUDE")
    longitude = env("LONGITUDE")
    timezone = env("TIMEZONE", DEFAULT_TIMEZONE)
    token = env("TELEGRAM_BOT_TOKEN")
    chat_id = env("TELEGRAM_CHAT_ID")

    message = build_message(location, latitude, longitude, timezone)
    send_telegram(token, chat_id, message)
    print("Telegram weather message sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
