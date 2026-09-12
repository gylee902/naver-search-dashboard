"""Naver Open API & NCP NAVER API HUB Search Module"""
import requests
from typing import Dict, Any, Optional

# 1. 네이버 클라우드 플랫폼 (NCP NAVER API HUB 공식 엔드포인트)
SEARCH_ENDPOINTS_NCP = {
    "뉴스": "https://naverapihub.apigw.ntruss.com/search/v1/news",
    "블로그": "https://naverapihub.apigw.ntruss.com/search/v1/blog",
    "웹문서": "https://naverapihub.apigw.ntruss.com/search/v1/webkr",
    "이미지": "https://naverapihub.apigw.ntruss.com/search/v1/image",
    "지식iN": "https://naverapihub.apigw.ntruss.com/search/v1/kin",
    "지역": "https://naverapihub.apigw.ntruss.com/search/v1/local",
    "카페글": "https://naverapihub.apigw.ntruss.com/search/v1/cafearticle",
    "백과사전": "https://naverapihub.apigw.ntruss.com/search/v1/encyc",
}

# 2. 네이버 개발자센터 (Open API 공식 엔드포인트)
SEARCH_ENDPOINTS_OPENAPI = {
    "뉴스": "https://openapi.naver.com/v1/search/news.json",
    "블로그": "https://openapi.naver.com/v1/search/blog.json",
    "웹문서": "https://openapi.naver.com/v1/search/webkr.json",
    "이미지": "https://openapi.naver.com/v1/search/image",
    "지식iN": "https://openapi.naver.com/v1/search/kin.json",
    "지역": "https://openapi.naver.com/v1/search/local.json",
    "카페글": "https://openapi.naver.com/v1/search/cafearticle.json",
    "백과사전": "https://openapi.naver.com/v1/search/encyc.json",
}

# 기본 별칭
SEARCH_ENDPOINTS = SEARCH_ENDPOINTS_NCP

__all__ = [
    "SEARCH_ENDPOINTS_NCP",
    "SEARCH_ENDPOINTS_OPENAPI",
    "SEARCH_ENDPOINTS",
    "search_naver_channel",
    "search_all_channels",
    "get_headers"
]

def get_headers(client_id: str, client_secret: str, auth_type: str = "ncp") -> Dict[str, str]:
    """인증 방식에 따른 요청 헤더 구성"""
    cid = client_id.strip()
    sec = client_secret.strip()
    if auth_type == "ncp":
        return {
            "X-NCP-APIGW-API-KEY-ID": cid,
            "X-NCP-APIGW-API-KEY": sec
        }
    else:
        return {
            "X-Naver-Client-Id": cid,
            "X-Naver-Client-Secret": sec
        }

def search_naver_channel(
    query: str,
    channel: str,
    client_id: str,
    client_secret: str,
    auth_type: str = "ncp",
    display: int = 20,
    start: int = 1,
    sort: str = "sim"
) -> Dict[str, Any]:
    """
    단일 채널 네이버 검색 API 호출
    """
    endpoints = SEARCH_ENDPOINTS_NCP if auth_type == "ncp" else SEARCH_ENDPOINTS_OPENAPI
    endpoint = endpoints.get(channel) or SEARCH_ENDPOINTS_NCP.get(channel)
    
    if not endpoint:
        raise ValueError(f"지원하지 않는 채널입니다: {channel}")
    
    headers = get_headers(client_id, client_secret, auth_type)
    
    params = {
        "query": query,
        "display": min(display, 100),
        "start": min(start, 1000),
        "sort": sort,
    }
    
    if channel in ["웹문서", "백과사전"]:
        if "sort" in params:
            del params["sort"]
            
    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=10)
        
        # NCP URL로 실패 시 표준 OpenAPI로 Fallback 시도
        if response.status_code in [401, 403, 404] and auth_type == "ncp":
            fb_endpoint = SEARCH_ENDPOINTS_OPENAPI.get(channel)
            fb_headers = {"X-Naver-Client-Id": client_id.strip(), "X-Naver-Client-Secret": client_secret.strip()}
            fb_res = requests.get(fb_endpoint, headers=fb_headers, params=params, timeout=10)
            if fb_res.status_code == 200:
                return {"success": True, "data": fb_res.json(), "error": None}

        if response.status_code == 200:
            return {"success": True, "data": response.json(), "error": None}
        else:
            return {
                "success": False,
                "data": None,
                "error": f"API 오류 ({response.status_code}): {response.text}"
            }
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


def search_all_channels(
    query: str,
    client_id: str,
    client_secret: str,
    auth_type: str = "ncp",
    display: int = 20,
    sort: str = "sim"
) -> Dict[str, Dict[str, Any]]:
    """
    8개 모든 채널에 대해 검색 수행 및 결과 집계
    """
    results = {}
    for channel_name in SEARCH_ENDPOINTS_NCP.keys():
        res = search_naver_channel(
            query=query,
            channel=channel_name,
            client_id=client_id,
            client_secret=client_secret,
            auth_type=auth_type,
            display=display,
            sort=sort
        )
        results[channel_name] = res
    return results
