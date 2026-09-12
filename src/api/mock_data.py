"""Mock Data Generator for Naver Search & DataLab EDA"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List

def generate_mock_datalab_data(
    keywords_list: List[str],
    start_date: str,
    end_date: str,
    time_unit: str = "date"
) -> pd.DataFrame:
    """모의 데이터랩 시계열 데이터 생성"""
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    freq_map = {"date": "D", "week": "W-MON", "month": "MS"}
    freq = freq_map.get(time_unit, "D")
    
    date_range = pd.date_range(start=start, end=end, freq=freq)
    if len(date_range) == 0:
        date_range = [start]
        
    rows = []
    np.random.seed(42)
    
    for idx, kw in enumerate(keywords_list[:5]):
        base_trend = 30 + idx * 15
        volatility = np.random.uniform(5, 15)
        # Random walk with seasonal wave
        t = np.linspace(0, 10, len(date_range))
        wave = 15 * np.sin(t + idx * 1.5)
        noise = np.random.normal(0, volatility, len(date_range))
        ratios = base_trend + wave + noise
        ratios = np.clip(ratios, 5, 100)
        
        # Max scale to 100 for at least one point
        if idx == 0 and len(ratios) > 0:
            ratios = ratios / np.max(ratios) * 100
        else:
            ratios = ratios / (np.max(ratios) + 20) * 100
            
        for d, r in zip(date_range, ratios):
            rows.append({
                "period": d,
                "keyword": kw,
                "ratio": round(float(r), 2)
            })
            
    return pd.DataFrame(rows)


def generate_mock_search_results(keywords_list: List[str], display: int = 20) -> Dict[str, Dict[str, Any]]:
    """모의 8개 채널 검색 결과 생성"""
    primary_kw = keywords_list[0] if keywords_list else "네이버 트렌드"
    
    channels = ["뉴스", "블로그", "웹문서", "이미지", "지식iN", "지역", "카페글", "백과사전"]
    results = {}
    
    sample_news = [
        {"title": f"[단독] <b>{primary_kw}</b> 시장 급성장... 신규 비즈니스 모델 주목", "description": f"최근 <b>{primary_kw}</b>에 대한 소비자들의 관심이 집중되면서 관련 마켓 인사이트와 통계 분석 수요가 급증하고 있다.", "pubDate": "Wed, 09 Sep 2026 14:20:00 +0900", "link": "https://example.com/news/1", "source": "한국경제"},
        {"title": f"2026 하반기 <b>{primary_kw}</b> 트렌드 분석 보고서 발표", "description": f"전문가들은 <b>{primary_kw}</b>의 향후 발전 방향성과 데이터 기반 마케팅 전략 수립이 필수적이라고 조언했다.", "pubDate": "Wed, 09 Sep 2026 11:15:00 +0900", "link": "https://example.com/news/2", "source": "매일경제"},
        {"title": f"글로벌 빅테크 기업들, <b>{primary_kw}</b> 연계 혁신 플랫폼 대거 런칭", "description": f"AI 기술과 <b>{primary_kw}</b>의 결합을 통해 새로운 사용자 경험을 제공하려는 시도가 잇따르고 있다.", "pubDate": "Tue, 08 Sep 2026 09:30:00 +0900", "link": "https://example.com/news/3", "source": "조선일보"},
    ]
    
    sample_blog = [
        {"title": f"직접 체험해본 <b>{primary_kw}</b> 핵심 요약과 추천 팁!", "description": f"이번 주말에 <b>{primary_kw}</b> 관련 정보를 찾아보면서 알게 된 유용한 꿀팁들과 비교 장단점을 정리해드립니다.", "postdate": "20260908", "link": "https://blog.naver.com/sample1", "bloggername": "인사이트 연구소"},
        {"title": f"<b>{primary_kw}</b> 완전 정복: 초보자를 위한 단계별 가이드", "description": f"처음 접하시는 분들을 위해 <b>{primary_kw}</b>의 기본 개념부터 실전 활용 방법까지 상세하게 공유합니다.", "postdate": "20260907", "link": "https://blog.naver.com/sample2", "bloggername": "트렌드세터"},
    ]
    
    sample_cafe = [
        {"title": f"회원님들은 <b>{primary_kw}</b> 어떻게 생각하시나요?", "description": f"요즘 커뮤니티에서 <b>{primary_kw}</b> 이야기가 많은데 실제 이용 후기나 만족도가 궁금합니다.", "cafename": "스마트 컨슈머 카페", "link": "https://cafe.naver.com/sample1"},
        {"title": f"<b>{primary_kw}</b> 실사용 솔직 후기 및 Q&A", "description": f"한 달 동안 집중적으로 써보고 느낀 장점과 아쉬운 점들을 가감 없이 솔직하게 공유해봅니다.", "cafename": "얼리어답터 모임", "link": "https://cafe.naver.com/sample2"},
    ]
    
    sample_kin = [
        {"title": f"<b>{primary_kw}</b> 선택할 때 가장 중요한 기준이 무엇인가요?", "description": f"처음 구매/도입을 고려하고 있는데 <b>{primary_kw}</b> 관련해서 어떤 요소를 가장 먼저 살펴봐야 할지 조언 부탁드립니다.", "datetime": "2026-09-08", "link": "https://kin.naver.com/sample1"},
        {"title": f"<b>{primary_kw}</b> 장단점 비교 질문드립니다.", "description": f"비슷한 다른 선택지와 비교했을 때 <b>{primary_kw}</b>만의 뚜렷한 장점과 차별점이 무엇인지 알고 싶습니다.", "datetime": "2026-09-07", "link": "https://kin.naver.com/sample2"},
    ]
    
    sample_web = [
        {"title": f"공식 웹사이트 - <b>{primary_kw}</b> 포털 및 통합 자료실", "description": f"<b>{primary_kw}</b>에 대한 공식 문서, 최신 업데이트 소식, 리포트 및 안내 자료를 제공합니다.", "link": "https://naver.com"},
        {"title": f"<b>{primary_kw}</b> 위키백과 정보 및 표준 규격", "description": f"<b>{primary_kw}</b>의 역사와 기본 원리, 표준화 기술 규격에 관한 체계적인 정보를 정리한 웹페이지입니다.", "link": "https://wikipedia.org"},
    ]
    
    sample_local = [
        {"title": f"<b>{primary_kw}</b> 플래그십 스토어 서울본점", "description": "전시, 체험, 상담 서비스가 완비된 대표 쇼룸", "address": "서울특별시 강남구 테헤란로 123", "roadAddress": "서울특별시 강남구 테헤란로 123", "category": "쇼핑 > 전문매장", "link": "https://map.naver.com"},
        {"title": f"<b>{primary_kw}</b> 연구소 판교센터", "description": "R&D 및 파트너십 허브 센터", "address": "경기도 성남시 분당구 판교역로 456", "roadAddress": "경기도 성남시 분당구 판교역로 456", "category": "연구소", "link": "https://map.naver.com"},
    ]
    
    sample_encyc = [
        {"title": f"두산백과: <b>{primary_kw}</b>", "description": f"<b>{primary_kw}</b>의 학술적 정의, 발전 과정 및 현대 산업에서의 응용 분야에 대한 개요.", "link": "https://terms.naver.com"},
    ]
    
    sample_image = [
        {"title": f"<b>{primary_kw}</b> 트렌드 그래픽 1", "thumbnail": "https://via.placeholder.com/300x200?text=" + primary_kw, "link": "https://via.placeholder.com/600x400?text=" + primary_kw},
        {"title": f"<b>{primary_kw}</b> 인포그래픽 2", "thumbnail": "https://via.placeholder.com/300x200?text=" + primary_kw + "+Insight", "link": "https://via.placeholder.com/600x400?text=" + primary_kw + "+Insight"},
    ]
    
    mapping = {
        "뉴스": (sample_news, 128400),
        "블로그": (sample_blog, 542000),
        "카페글": (sample_cafe, 321500),
        "지식iN": (sample_kin, 98200),
        "웹문서": (sample_web, 1420000),
        "지역": (sample_local, 1250),
        "이미지": (sample_image, 784000),
        "백과사전": (sample_encyc, 450),
    }
    
    for ch in channels:
        items, total = mapping.get(ch, ([], 1000))
        results[ch] = {
            "success": True,
            "data": {
                "total": total,
                "start": 1,
                "display": len(items),
                "items": items
            },
            "error": None
        }
        
    return results
