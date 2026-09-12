"""
Naver Shopping Insight API Module (NCP NAVER API HUB & Open API)
Fetches shopping click trends, category popularity, and demographic distributions.
"""
import json
import requests
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

SHOPPING_CATEGORY_NCP_URL = "https://naverapihub.apigw.ntruss.com/shopping/v1/categories"
SHOPPING_GENDER_NCP_URL = "https://naverapihub.apigw.ntruss.com/shopping/v1/category/gender"
SHOPPING_AGE_NCP_URL = "https://naverapihub.apigw.ntruss.com/shopping/v1/category/age"

# 대표 네이버 쇼핑 카테고리 ID 매핑 (50000000: 패션의류, 50000001: 패션잡화, 50000002: 화장품/미용, 50000003: 디지털/가전, 50000004: 가구/인테리어, 50000005: 출산/육아, 50000006: 식품, 50000007: 스포츠/레저, 50000008: 생활/건강)
DEFAULT_SHOPPING_CATEGORIES = [
    {"name": "디지털/가전", "param": ["50000003"]},
    {"name": "생활/건강", "param": ["50000008"]},
    {"name": "패션의류", "param": ["50000000"]},
    {"name": "식품", "param": ["50000006"]},
    {"name": "화장품/미용", "param": ["50000002"]},
]

def get_shopping_category_trend(
    client_id: str,
    client_secret: str,
    start_date: str,
    end_date: str,
    time_unit: str = "date",
    category_list: List[Dict[str, Any]] = None,
    device: Optional[str] = None,
    gender: Optional[str] = None
) -> Dict[str, Any]:
    """네이버 쇼핑 카테고리별 클릭 추이 조회"""
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id.strip(),
        "X-NCP-APIGW-API-KEY": client_secret.strip(),
        "Content-Type": "application/json",
    }
    
    categories = category_list or DEFAULT_SHOPPING_CATEGORIES[:3]
    
    body: Dict[str, Any] = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "category": categories
    }
    if device in ["pc", "mo"]:
        body["device"] = device
    if gender in ["m", "f"]:
        body["gender"] = gender
        
    try:
        res = requests.post(
            SHOPPING_CATEGORY_NCP_URL,
            headers=headers,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            timeout=10
        )
        if res.status_code == 200:
            res_json = res.json()
            rows = []
            for item in res_json.get("results", []):
                title = item.get("title")
                for pt in item.get("data", []):
                    rows.append({
                        "period": pd.to_datetime(pt.get("period")),
                        "category": title,
                        "ratio": float(pt.get("ratio", 0))
                    })
            df = pd.DataFrame(rows)
            return {"success": True, "df": df, "raw": res_json, "error": None}
        else:
            return {"success": False, "df": pd.DataFrame(), "error": f"쇼핑 API 오류 ({res.status_code}): {res.text}"}
    except Exception as e:
        return {"success": False, "df": pd.DataFrame(), "error": str(e)}


def generate_mock_shopping_data(start_date: str, end_date: str) -> pd.DataFrame:
    """쇼핑 인사이트 모의 데이터 생성기"""
    dates = pd.date_range(start_date, end_date, freq="D")
    categories = ["디지털/가전", "생활/건강", "패션의류", "식품"]
    rows = []
    np.random.seed(42)
    for cat_idx, cat in enumerate(categories):
        base = 30 + cat_idx * 15
        wave = 15 * np.sin(np.linspace(0, 10, len(dates)) + cat_idx)
        noise = np.random.normal(0, 5, len(dates))
        ratios = np.clip(base + wave + noise, 5, 100)
        for d, r in zip(dates, ratios):
            rows.append({"period": d, "category": cat, "ratio": round(float(r), 2)})
    return pd.DataFrame(rows)
