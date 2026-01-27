import requests
import json
from ics import Calendar, Event
from datetime import datetime
import pytz
import sys

def fetch_fed_dates():
    """
    获取美联储会议日期。建议逻辑：
    1. 优先抓取 CME 的动态数据接口
    2. 若失败，返回 2026 年已知的官方日程作为兜底
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.cmegroup.com/"
    }
    
    # 2026 年已知官方初步日程 (UTC)
    fallback_dates = [
        "2026-01-28", "2026-03-18", "2026-05-06", "2026-06-17",
        "2026-07-29", "2026-09-16", "2026-11-04", "2026-12-16"
    ]
    
    url = "https://www.cmegroup.com/content/cmegroup/en/markets/interest-rates/cme-fedwatch-tool/_jcr_content/par/columncontrol/col1/fedwatchtool.json"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # 提取所有会议日期
            meetings = [m['date'] for m in data.get('meetings', [])]
            return meetings if meetings else fallback_dates
    except Exception as e:
        print(f"抓取失败，使用兜底数据: {e}")
    
    return fallback_dates

def generate_ics(dates):
    cal = Calendar()
    cal.extra.append(requests.structures.CaseInsensitiveDict({"X-WR-CALNAME": "美联储议息会议"}))
    # 美东 14:00 对应 UTC 19:00 (夏令时) 或 20:00 (冬令时)
    # ICS 订阅会自动根据用户本地时区转换，这里存入 UTC 时间
    for d_str in dates:
        event = Event()
        event.name = "美联储利率决议 (FOMC Decision)"
        
        # 统一设为决议公布点：UTC 19:00 (即北京时间次日凌晨 02:00/03:00)
        dt = datetime.strptime(d_str, "%Y-%m-%d")
        event.begin = dt.replace(hour=19, minute=0, tzinfo=pytz.UTC)
        event.duration = {"minutes": 30}
        event.description = "数据源: CME FedWatch Tool\n自动同步时间: " + datetime.now().strftime("%Y-%m-%d")
        cal.events.add(event)
    
    with open("fed_meetings.ics", "w", encoding="utf-8") as f:
        f.writelines(cal.serialize_iter())

if __name__ == "__main__":
    dates = fetch_fed_dates()
    generate_ics(dates)
    print(f"成功更新 {len(dates)} 个日程节点。")
