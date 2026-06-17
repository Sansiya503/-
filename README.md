# Telegram Weather Agent

매일 날씨와 미세먼지/초미세먼지 정보를 Telegram으로 보내는 작은 Python 에이전트입니다.

## 1. Telegram 봇 만들기

1. Telegram에서 `@BotFather`를 엽니다.
2. `/newbot`을 보내고 안내대로 봇 이름을 정합니다.
3. 발급된 토큰을 `TELEGRAM_BOT_TOKEN` 값으로 사용합니다.
4. 새 봇에게 아무 메시지나 한 번 보냅니다.
5. 아래 주소를 브라우저에서 열어 `chat.id` 값을 찾습니다.

```text
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

## 2. 로컬에서 테스트하기

PowerShell에서 아래 값을 본인 정보로 바꿔 실행합니다.

```powershell
$env:TELEGRAM_BOT_TOKEN="123456:YOUR_TOKEN"
$env:TELEGRAM_CHAT_ID="123456789"
$env:LOCATION_NAME="서울"
$env:LATITUDE="37.5665"
$env:LONGITUDE="126.9780"
$env:TIMEZONE="Asia/Seoul"

python .\weather_agent.py --dry-run
python .\weather_agent.py
```

`--dry-run`은 API 호출 없이 예시 메시지만 출력합니다.

## 3. 매일 자동 실행하기

GitHub Actions, Windows 작업 스케줄러, cron, AWS Lambda, Cloudflare Workers 중 하나로 매일 실행하면 됩니다.

가장 간단한 배포 방식은 GitHub Actions입니다.

1. 이 폴더를 GitHub 저장소로 올립니다.
2. 저장소 `Settings > Secrets and variables > Actions`에 아래 secrets를 추가합니다.
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `LOCATION_NAME`
   - `LATITUDE`
   - `LONGITUDE`
   - `TIMEZONE`
3. `.github/workflows/daily-weather.yml` 워크플로가 매일 아침 8시에 실행됩니다.

## 데이터 출처

- 날씨: Open-Meteo Forecast API
- 미세먼지/초미세먼지: Open-Meteo Air Quality API

