"""Time Analysis Module for Publication Timelines"""
import re
from datetime import datetime
import pandas as pd
from typing import List, Dict, Any

def parse_raw_date(raw_date_str: str) -> str:
    """다양한 네이버 API 날짜 문자열을 YYYY-MM-DD 표준 문자열로 정규화"""
    if not raw_date_str or raw_date_str == "-":
        return None
        
    s = str(raw_date_str).strip()
    
    # 1. RFC 822 (뉴스: Wed, 09 Sep 2026 14:20:00 +0900)
    try:
        # e.g., 'Wed, 09 Sep 2026 ...'
        dt = pd.to_datetime(s)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
        
    # 2. YYYYMMDD (블로그/카페)
    if re.match(r"^\d{8}$", s):
        try:
            return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
        except Exception:
            pass
            
    # 3. YYYY.MM.DD or YYYY-MM-DD
    match = re.search(r"(\d{4})[.-](\d{1,2})[.-](\d{1,2})", s)
    if match:
        y, m, d = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"
        
    return None


def get_publication_timeline_df(items: List[Dict[str, Any]]) -> pd.DataFrame:
    """수집된 문서들의 발행일자별 채널별 빈도 집계 DataFrame 생성"""
    records = []
    for itm in items:
        raw_date = itm.get("date", "")
        parsed = parse_raw_date(raw_date)
        if parsed:
            records.append({
                "date": parsed,
                "channel": itm.get("channel", "기타")
            })
            
    if not records:
        return pd.DataFrame(columns=["date", "channel", "count"])
        
    df = pd.DataFrame(records)
    grouped = df.groupby(["date", "channel"]).size().reset_index(name="count")
    grouped["date"] = pd.to_datetime(grouped["date"])
    grouped = grouped.sort_values(by="date")
    return grouped
