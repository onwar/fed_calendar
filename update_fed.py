import requests
from datetime import datetime, timezone, timedelta
import uuid

def fetch_fed_dates():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.cmegroup.com/"
    }

    fallback_dates = [
        "2026-01-28", "2026-03-18", "2026-05-06", "2026-06-17",
        "2026-07-29", "2026-09-16", "2026-11-04", "2026-12-16"
    ]

    url = "https://www.cmegroup.com/content/cmegroup/en/markets/interest-rates/cme-fedwatch-tool/_jcr_content/par/columncontrol/col1/fedwatchtool.json"

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            meetings = [m['date'] for m in data.get('meetings', [])]
            return meetings if meetings else fallback_dates
    except Exception as e:
        print(f"抓取失败，使用兜底数据: {e}")

    return fallback_dates

def format_dt(dt):
    return dt.strftime("%Y%m%dT%H%M%SZ")

def generate_ics(dates):
    now = format_dt(datetime.now(timezone.utc))
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//fed_calendar_bot//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:美联储议息会议",
        "X-WR-CALDESC:自动同步 CME FedWatch 利率决议日程",
    ]

    for d_str in dates:
        dt_start = datetime.strptime(d_str, "%Y-%m-%d").replace(
            hour=19, minute=0, second=0, tzinfo=timezone.utc
        )
        dt_end = dt_start + timedelta(minutes=30)
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uuid.uuid4()}@fed_calendar",
            f"DTSTAMP:{now}",
            f"DTSTART:{format_dt(dt_start)}",
            f"DTEND:{format_dt(dt_end)}",
            "SUMMARY:美联储利率决议 (FOMC Decision)",
            f"DESCRIPTION:数据源: CME FedWatch Tool\\n自动同步时间: {datetime.now().strftime('%Y-%m-%d')}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")

    with open("fed_meetings.ics", "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\r\n".join(lines) + "\r\n")

if __name__ == "__main__":
    dates = fetch_fed_dates()
    generate_ics(dates)
    print(f"成功更新 {len(dates)} 个日程节点，日历名称：美联储议息会议。")
