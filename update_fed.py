import requests
import json
from ics import Calendar, Event
from ics.grammar.parse import ContentLine # 导入用于处理自定义属性的类
保护
from datetime import datetime
import pytz
import sys

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

def generate_ics(dates):
    cal = Calendar()
    
    # --- 修复逻辑：使用 ContentLine 添加日历名称 ---
    # 这种方式绕过了 CaseInsensitiveDict 的 clone() 错误
    cal.extra.append(ContentLine(name="X-WR-CALNAME", value="美联储议息会议"))
    cal.extra.append(ContentLine(name="X-WR-CALDESC", value="自动同步 CME FedWatch 利率决议日程"))
    
    for d_str in dates:
        event = Event()
        event.name = "美联储利率决议 (FOMC Decision)"
        
        # 维持精确时间戳格式：DTSTART:20260128T190000Z
        dt = datetime.strptime(d_str, "%Y-%m-%d")
        event.begin = dt.replace(hour=19, minute=0, second=0, tzinfo=pytz.UTC)
        event.duration = {"minutes": 30}
        
        event.description = f"数据源: CME FedWatch Tool\n同步时间: {datetime.now().strftime('%Y-%m-%d')}"
        cal.events.add(event)
    
    with open("fed_meetings.ics", "w", encoding="utf-8") as f:
        f.writelines(cal.serialize_iter())

if __name__ == "__main__":
    dates = fetch_fed_dates()
    generate_ics(dates)
    print(f"成功更新 {len(dates)} 个日程，已修复 AttributeError 错误。")
