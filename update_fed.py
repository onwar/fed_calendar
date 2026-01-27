import requests
import json
from ics import Calendar, Event
from datetime import datetime
import pytz
import sys

def fetch_fed_dates():
    """
    获取美联储会议日期。逻辑：
    1. 优先抓取 CME 的动态数据接口
    2. 若失败，返回 2026 年已知的官方日程作为兜底
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
            meetings = [m['date'] for m in data.get('meetings', [])]
            return meetings if meetings else fallback_dates
    except Exception as e:
        print(f"抓取失败，使用兜底数据: {e}")
    
    return fallback_dates

def generate_ics(dates):
    cal = Calendar()
    
    # --- 核心新增：设置默认日历名称 ---
    # 使用 CaseInsensitiveDict 确保 X-WR-CALNAME 属性被正确添加
    cal.extra.append(requests.structures.CaseInsensitiveDict({"X-WR-CALNAME": "美联储议息会议"}))
    # 针对部分客户端添加描述属性
    cal.extra.append(requests.structures.CaseInsensitiveDict({"X-WR-CALDESC": "自动同步 CME FedWatch 利率决议日程"}))
    
    for d_str in dates:
        event = Event()
        event.name = "美联储利率决议 (FOMC Decision)"
        
        # 维持精确时间戳逻辑：UTC 19:00 (即北京时间次日凌晨 02:00/03:00)
        # 生成的格式为：DTSTART:20260128T190000Z
        dt = datetime.strptime(d_str, "%Y-%m-%d")
        event.begin = dt.replace(hour=19, minute=0, second=0, tzinfo=pytz.UTC)
        event.duration = {"minutes": 30}
        
        event.description = f"数据源: CME FedWatch Tool\n自动同步时间: {datetime.now().strftime('%Y-%m-%d')}"
        cal.events.add(event)
    
    with open("fed_meetings.ics", "w", encoding="utf-8") as f:
        # 使用 serialize_iter 确保所有 extra 属性被写入文件头部
        f.writelines(cal.serialize_iter())

if __name__ == "__main__":
    dates = fetch_fed_dates()
    generate_ics(dates)
    print(f"成功更新 {len(dates)} 个日程节点，日历名称已设为：美联储议息会议。")
