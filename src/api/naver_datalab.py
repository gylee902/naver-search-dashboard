"""Naver DataLab & NCP NAVER API HUB Search Trend API Module"""
import json
import requests
import pandas as pd
from typing import Dict, Any, List, Optional

# NCP NAVER API HUB 공식 엔드포인트
DATALAB_TREND_NCP_URL = "https://naverapihub.apigw.ntruss.com/search-trend/v1/search"
# 네이버 개발자센터 엔드포인트
DATALAB_TREND_OPENAPI_URL = "https://openapi.naver.com/v1/datalab/search"

def get_datalab_trend(
    client_id: str,
    client_secret: str,
    start_date: str,
    end_date: str,
    time_unit: str,
    keywords_list: List[str],
    auth_type: str = "ncp",
    device: Optional[str] = None,
    gender: Optional[str] = None,
    ages: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    네이버 데이터랩 통합 검색어 트렌드 API 호출 (NCP API HUB 및 오픈API 자동 지원)
    """
    cid = client_id.strip()
    sec = client_secret.strip()
    
    keyword_groups = []
    for kw in keywords_list[:5]:
        kw_clean = kw.strip()
        if kw_clean:
            keyword_groups.append({
                "groupName": kw_clean,
                "keywords": [kw_clean]
            })
            
    if not keyword_groups:
        return {"success": False, "raw": None, "df": None, "error": "유효한 검색어가 없습니다."}
        
    body: Dict[str, Any] = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": keyword_groups,
    }
    
    if device and device in ["pc", "mo"]:
        body["device"] = device
    if gender and gender in ["m", "f"]:
        body["gender"] = gender
    if ages and len(ages) > 0:
        body["ages"] = ages
        
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")

    # 1. NCP API Gateway 방식 시도
    if auth_type == "ncp":
        headers_ncp = {
            "X-NCP-APIGW-API-KEY-ID": cid,
            "X-NCP-APIGW-API-KEY": sec,
            "Content-Type": "application/json",
        }
        try:
            res = requests.post(DATALAB_TREND_NCP_URL, headers=headers_ncp, data=payload, timeout=10)
            if res.status_code == 200:
                res_json = res.json()
                return {"success": True, "raw": res_json, "df": parse_datalab_to_df(res_json), "error": None}
        except Exception:
            pass

    # 2. 네이버 개발자센터 오픈 API 방식 시도
    headers_openapi = {
        "X-Naver-Client-Id": cid,
        "X-Naver-Client-Secret": sec,
        "Content-Type": "application/json",
    }
    try:
        res = requests.post(DATALAB_TREND_OPENAPI_URL, headers=headers_openapi, data=payload, timeout=10)
        if res.status_code == 200:
            res_json = res.json()
            return {"success": True, "raw": res_json, "df": parse_datalab_to_df(res_json), "error": None}
        else:
            return {
                "success": False,
                "raw": None,
                "df": None,
                "error": f"데이터랩 API 오류 ({res.status_code}): {res.text}"
            }
    except Exception as e:
        return {"success": False, "raw": None, "df": None, "error": str(e)}


def parse_datalab_to_df(datalab_json: Dict[str, Any]) -> pd.DataFrame:
    """데이터랩 JSON 응답을 Pandas DataFrame으로 변환"""
    rows = []
    results = datalab_json.get("results", [])
    
    for item in results:
        title = item.get("title")
        for point in item.get("data", []):
            period = point.get("period")
            ratio = point.get("ratio")
            rows.append({
                "period": period,
                "keyword": title,
                "ratio": float(ratio)
            })
            
    if not rows:
        return pd.DataFrame(columns=["period", "keyword", "ratio"])
        
    df = pd.DataFrame(rows)
    df["period"] = pd.to_datetime(df["period"])
    return df
