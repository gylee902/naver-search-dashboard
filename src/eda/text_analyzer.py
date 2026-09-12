"""Text Analysis & Co-occurrence Matrix Module"""
import re
import itertools
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Set
import pandas as pd

# 기본 불용어 목록
STOPWORDS = {
    "있다", "있는", "있으며", "있는지", "없다", "없는", "통해", "대한", "위해",
    "관련", "경우", "함께", "가장", "어떤", "많은", "이런", "저런", "모든",
    "수", "등", "및", "더", "그", "이", "저", "것", "들", "때", "중", "과", "와",
    "에서", "으로", "로", "을", "를", "은", "는", "이", "가", "에", "의", "도",
    "네이버", "제공", "블로그", "뉴스", "카페", "질문", "답변", "후기", "추천",
    "the", "and", "in", "to", "of", "for", "a", "is", "that", "on", "with", "com", "http", "https"
}

def clean_text_tokens(text: str, custom_stopwords: Set[str] = None) -> List[str]:
    """텍스트에서 한글/영문 2글자 이상의 토큰 추출 및 불용어 제거"""
    if not isinstance(text, str):
        return []
    
    cleaned = re.sub(r"[^가-힣a-zA-Z\s]", " ", text)
    tokens = [t.lower().strip() for t in cleaned.split() if len(t.strip()) >= 2]
    
    stop_set = set(STOPWORDS)
    if custom_stopwords:
        stop_set.update(custom_stopwords)
        
    filtered = [t for t in tokens if t not in stop_set]
    return filtered


def get_top_keywords_from_items(
    items: List[Dict[str, str]],
    top_n: int = 30,
    custom_stopwords: List[str] = None
) -> List[Tuple[str, int]]:
    """전체 아이템에서 상위 키워드 빈도 추출"""
    all_tokens = []
    stop_set = {w.strip().lower() for w in (custom_stopwords or [])}
    
    for item in items:
        title = item.get("title", "")
        desc = item.get("description", "")
        all_tokens.extend(clean_text_tokens(title, stop_set))
        all_tokens.extend(clean_text_tokens(desc, stop_set))
        
    counter = Counter(all_tokens)
    return counter.most_common(top_n)


def get_channel_keyword_distribution(
    items: List[Dict[str, str]],
    top_keywords: List[str]
) -> pd.DataFrame:
    """채널별 주요 키워드 출현 빈도 매트릭스 계산"""
    matrix = defaultdict(lambda: defaultdict(int))
    
    for itm in items:
        ch = itm.get("channel", "기타")
        tokens = set(clean_text_tokens(itm.get("title", "") + " " + itm.get("description", "")))
        for kw in top_keywords:
            if kw in tokens:
                matrix[ch][kw] += 1
                
    df = pd.DataFrame(matrix).fillna(0).T
    return df


def build_cooccurrence_graph(
    items: List[Dict[str, str]],
    top_n_keywords: int = 15,
    min_cooccurrence: int = 2,
    custom_stopwords: List[str] = None
) -> Dict[str, Any]:
    """동시출현(Co-occurrence) 네트워크 데이터 생성"""
    top_kws = [kw for kw, _ in get_top_keywords_from_items(items, top_n=top_n_keywords, custom_stopwords=custom_stopwords)]
    top_kws_set = set(top_kws)
    
    pair_counter = Counter()
    node_freq = Counter()
    
    stop_set = {w.strip().lower() for w in (custom_stopwords or [])}
    
    for itm in items:
        tokens = list(set(clean_text_tokens(itm.get("title", "") + " " + itm.get("description", ""), stop_set)))
        filtered_tokens = [t for t in tokens if t in top_kws_set]
        
        for t in filtered_tokens:
            node_freq[t] += 1
            
        for p1, p2 in itertools.combinations(sorted(filtered_tokens), 2):
            pair_counter[(p1, p2)] += 1
            
    edges = []
    for (src, tgt), weight in pair_counter.items():
        if weight >= min_cooccurrence:
            edges.append({"source": src, "target": tgt, "weight": weight})
            
    nodes = [{"id": kw, "label": kw, "size": node_freq.get(kw, 1)} for kw in top_kws if node_freq.get(kw, 0) > 0]
    
    return {"nodes": nodes, "edges": edges}


def compute_channel_stats(channel_results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """채널별 통계 요약"""
    data = []
    for ch_name, res in channel_results.items():
        if res.get("success") and res.get("data"):
            total_count = res["data"].get("total", 0)
            items_count = len(res["data"].get("items", []))
            data.append({"channel": ch_name, "total_count": total_count, "fetched_count": items_count})
        else:
            data.append({"channel": ch_name, "total_count": 0, "fetched_count": 0})
    return pd.DataFrame(data)
