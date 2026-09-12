import re
import html
from typing import Any, Dict, List

def clean_html(raw_text: str) -> str:
    """HTML 태그 제거 및 HTML 엔티티(&quot;, &lt;, &gt;, &amp; 등) 디코딩"""
    if not isinstance(raw_text, str):
        return ""
    # Remove bold tags and any html tags
    clean = re.sub(r"<[^>]+>", "", raw_text)
    # Unescape HTML entities
    clean = html.unescape(clean)
    return clean.strip()

def format_number(val: Any) -> str:
    """숫자를 3자리 콤마 포맷으로 변환"""
    try:
        return f"{int(val):,}"
    except (ValueError, TypeError):
        return str(val)

def extract_channel_items(raw_response: Dict[str, Any], channel_name: str) -> List[Dict[str, Any]]:
    """API 응답 아이템을 정제하여 리스트 형태로 반환"""
    items = raw_response.get("items", [])
    cleaned_items = []
    
    for item in items:
        cleaned = {
            "channel": channel_name,
            "title": clean_html(item.get("title", "")),
            "link": item.get("link", "") or item.get("originallink", ""),
            "description": clean_html(item.get("description", "")),
        }
        
        # 채널별 특화 필드
        if "pubDate" in item:
            cleaned["date"] = item.get("pubDate", "")
        elif "postdate" in item:
            cleaned["date"] = item.get("postdate", "")
        elif "datetime" in item:
            cleaned["date"] = item.get("datetime", "")
        else:
            cleaned["date"] = "-"
            
        if "bloggername" in item:
            cleaned["source"] = item.get("bloggername", "")
        elif "cafename" in item:
            cleaned["source"] = item.get("cafename", "")
        elif "category" in item:
            cleaned["source"] = item.get("category", "")
        elif "address" in item or "roadAddress" in item:
            cleaned["source"] = item.get("roadAddress", item.get("address", ""))
        else:
            cleaned["source"] = "-"

        if "thumbnail" in item:
            cleaned["thumbnail"] = item.get("thumbnail", "")
        elif "image" in item:
            cleaned["thumbnail"] = item.get("image", "")
        else:
            cleaned["thumbnail"] = ""

        cleaned_items.append(cleaned)
        
    return cleaned_items
