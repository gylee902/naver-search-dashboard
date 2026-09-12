"""
Advanced Statistical Analysis & AI Summary Module for Channel EDA
Provides descriptive statistics, cross-tabulations, pivot tables, length binning, and AI-driven 3-line summaries.
"""
import re
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from collections import Counter
from src.eda.text_analyzer import clean_text_tokens
from src.eda.time_analyzer import parse_raw_date

def enrich_channel_dataframe(items: List[Dict[str, Any]]) -> pd.DataFrame:
    """채널 아이템 리스트를 계량 분석용 피처(길이, 단어수, 표준일자, 요일 등)로 보강한 DataFrame 반환"""
    if not items:
        return pd.DataFrame()
        
    records = []
    for itm in items:
        title = itm.get("title", "")
        desc = itm.get("description", "")
        source = itm.get("source", "-") or "-"
        if source == "-" and itm.get("link"):
            # 링크에서 도메인 추출
            m = re.search(r"https?://([^/]+)", itm.get("link", ""))
            source = m.group(1) if m else "-"
            
        raw_date = itm.get("date", "-")
        std_date = parse_raw_date(raw_date)
        
        day_of_week = "-"
        if std_date:
            try:
                dt = pd.to_datetime(std_date)
                day_of_week = ["월", "화", "수", "목", "금", "토", "일"][dt.weekday()]
            except Exception:
                pass
                
        title_len = len(title)
        desc_len = len(desc)
        title_words = len(title.split())
        desc_words = len(desc.split())
        total_words = title_words + desc_words
        
        records.append({
            "title": title,
            "description": desc,
            "source": source,
            "date": std_date if std_date else "-",
            "day_of_week": day_of_week,
            "link": itm.get("link", ""),
            "thumbnail": itm.get("thumbnail", ""),
            "title_len": title_len,
            "desc_len": desc_len,
            "total_len": title_len + desc_len,
            "title_words": title_words,
            "desc_words": desc_words,
            "total_words": total_words
        })
        
    df = pd.DataFrame(records)
    return df


def get_descriptive_stats_table(df: pd.DataFrame) -> pd.DataFrame:
    """1. 계량 텍스트 기술통계 요약표 (Descriptive Statistics)"""
    if df.empty:
        return pd.DataFrame()
        
    numeric_cols = ["title_len", "desc_len", "total_len", "title_words", "desc_words", "total_words"]
    available_cols = [c for c in numeric_cols if c in df.columns]
    if not available_cols:
        return pd.DataFrame()
    
    desc = df[available_cols].describe().T
    desc = desc.rename(columns={
        "count": "데이터 수",
        "mean": "평균",
        "std": "표준편차",
        "min": "최소값",
        "25%": "1사분위(25%)",
        "50%": "중앙값(50%)",
        "75%": "3사분위(75%)",
        "max": "최대값"
    })
    
    name_map = {
        "title_len": "제목 글자수",
        "desc_len": "본문요약 글자수",
        "total_len": "전체 글자수",
        "title_words": "제목 단어수",
        "desc_words": "본문요약 단어수",
        "total_words": "전체 단어수"
    }
    desc.index = [name_map.get(idx, idx) for idx in desc.index]
    return desc.round(2)


def get_crosstab_table(df: pd.DataFrame, top_n_sources: int = 7) -> pd.DataFrame:
    """2. 주요 출처 × 요일/일자 교차표 (Cross-tabulation Table)"""
    if df.empty or "source" not in df.columns:
        return pd.DataFrame()
        
    # 상위 출처 선별
    top_sources = df["source"].value_counts().head(top_n_sources).index.tolist()
    df_filtered = df[df["source"].isin(top_sources)].copy()
    
    if "day_of_week" in df_filtered.columns and (df_filtered["day_of_week"] != "-").any():
        col_target = "day_of_week"
        ct = pd.crosstab(df_filtered["source"], df_filtered[col_target], margins=True, margins_name="합계")
        days_order = [d for d in ["월", "화", "수", "목", "금", "토", "일", "합계"] if d in ct.columns]
        if days_order:
            ct = ct[days_order]
    elif "date" in df_filtered.columns and (df_filtered["date"] != "-").any():
        ct = pd.crosstab(df_filtered["source"], df_filtered["date"], margins=True, margins_name="합계")
    else:
        ct = df_filtered["source"].value_counts().to_frame()
        ct.columns = ["문서수"]
        
    return ct


def get_pivot_table(df: pd.DataFrame) -> pd.DataFrame:
    """3. 출처별/기간별 발행 통계 피봇테이블 (Pivot Table with Aggregations)"""
    if df.empty or "source" not in df.columns:
        return pd.DataFrame()
        
    top_sources = df["source"].value_counts().head(8).index.tolist()
    df_sub = df[df["source"].isin(top_sources)].copy()
    if df_sub.empty:
        return pd.DataFrame()
        
    agg_dict = {"title": "count"}
    if "total_len" in df_sub.columns:
        agg_dict["total_len"] = ["mean", "max"]
    if "total_words" in df_sub.columns:
        agg_dict["total_words"] = ["mean"]
        
    pivot = pd.pivot_table(
        df_sub,
        index="source",
        aggfunc=agg_dict
    )
    
    # 컬럼 플래트닝 및 한글화
    new_cols = []
    for col in pivot.columns:
        if isinstance(col, tuple):
            metric, stat = col[0], col[1]
            if metric == "title":
                new_cols.append("발행 문서수(건)")
            elif metric == "total_len" and stat == "mean":
                new_cols.append("평균 글자수(자)")
            elif metric == "total_len" and stat == "max":
                new_cols.append("최대 글자수(자)")
            elif metric == "total_words":
                new_cols.append("평균 단어수(개)")
            else:
                new_cols.append(f"{metric}_{stat}")
        else:
            new_cols.append(str(col))
    pivot.columns = new_cols
    return pivot.round(1)


def get_length_bins_table(df: pd.DataFrame) -> pd.DataFrame:
    """4. 텍스트 길이 구간(Binning)별 빈도 및 점유율 표 (Length Interval Distribution Table)"""
    if df.empty or "total_len" not in df.columns:
        return pd.DataFrame()
        
    bins = [0, 50, 100, 150, 200, 300, 500, 100000]
    labels = ["50자 이하", "51~100자", "101~150자", "151~200자", "201~300자", "301~500자", "500자 초과"]
    
    df_cut = pd.cut(df["total_len"], bins=bins, labels=labels, right=True)
    counts = df_cut.value_counts(sort=False)
    total_cnt = max(1, len(df))
    ratios = (counts / total_cnt * 100).round(1)
    
    bin_table = pd.DataFrame({
        "길이 구간": counts.index.astype(str),
        "문서 수(건)": counts.values,
        "점유율(%)": [f"{r}%" for r in ratios.values]
    })
    return bin_table[bin_table["문서 수(건)"] > 0].reset_index(drop=True)


def get_keyword_rank_table(df: pd.DataFrame, top_n: int = 15, custom_stopwords: List[str] = None) -> pd.DataFrame:
    """5. 핵심 키워드 출현 빈도 및 비중 순위표 (Keyword Rank & Ratio Table)"""
    if df.empty:
        return pd.DataFrame()
        
    all_tokens = []
    stop_set = {w.strip().lower() for w in (custom_stopwords or [])}
    
    for _, row in df.iterrows():
        t = str(row.get("title", ""))
        d = str(row.get("description", ""))
        all_tokens.extend(clean_text_tokens(t, stop_set))
        all_tokens.extend(clean_text_tokens(d, stop_set))
        
    if not all_tokens:
        return pd.DataFrame(columns=["순위", "키워드", "출현 빈도", "토큰 점유율(%)"])
        
    counter = Counter(all_tokens)
    total_token_count = len(all_tokens)
    
    rows = []
    for rank, (kw, freq) in enumerate(counter.most_common(top_n), 1):
        ratio = (freq / total_token_count * 100)
        rows.append({
            "순위": f"{rank}위",
            "키워드": kw,
            "출현 빈도(회)": freq,
            "토큰 점유율(%)": f"{ratio:.2f}%"
        })
        
    return pd.DataFrame(rows)


def generate_ai_channel_summary(
    channel_name: str,
    df: pd.DataFrame,
    total_index_count: int,
    top_keywords: List[Tuple[str, int]]
) -> List[str]:
    """
    수집된 채널별 정량적 데이터와 텍스트 특성을 기반으로 AI 3줄 핵심 인사이트 생성
    """
    if df.empty:
        return [
            f"1️⃣ **데이터 수집 현황**: '{channel_name}' 채널에서 수집된 유효 문서가 존재하지 않습니다.",
            f"2️⃣ **트렌드 분석**: 검색어 설정 또는 API 상태를 확인해 주세요.",
            f"3️⃣ **인사이트 제언**: 검색어를 보다 일반적인 키워드로 조정하거나 기간을 넓혀 재조회해 보세요."
        ]
        
    sample_count = len(df)
    avg_len = df["total_len"].mean() if "total_len" in df.columns else 0
    top_kw_names = [kw for kw, _ in top_keywords[:3]]
    top_kw_str = ", ".join([f"'{k}'" for k in top_kw_names]) if top_kw_names else "주요 키워드"
    
    # 1. 볼륨 & 발행 시계열 요약
    if "date" in df.columns and (df["date"] != "-").any():
        valid_dates = df[df["date"] != "-"]["date"]
        date_counts = valid_dates.value_counts()
        peak_date = date_counts.index[0] if not date_counts.empty else "최근"
        line1 = f"1️⃣ **발행 추세 & 볼륨**: 전체 약 **{total_index_count:,}건**의 인덱스 중 **{sample_count}건**을 분석한 결과, **{peak_date}** 전후로 게시물 발행 및 이슈 집중도가 가장 높게 나타났습니다."
    else:
        line1 = f"1️⃣ **발행 추세 & 볼륨**: 전체 약 **{total_index_count:,}건**의 관련 문서가 검색되었으며, 채널 내에서 활발한 정보 공유와 검색 인덱싱이 이루어지고 있습니다."
        
    # 2. 핵심 토픽 & 담론 요약
    line2 = f"2️⃣ **핵심 토픽 & 담론**: 텍스트 분석 결과 **{top_kw_str}** 키워드가 가장 높은 빈도로 등장하여 해당 채널 내 주요 담론과 논의의 중심축을 형성하고 있습니다."
    
    # 3. 정보량 & 출처 특성 요약
    if "source" in df.columns and (df["source"] != "-").any():
        top_src = df["source"].value_counts().index[0]
        top_src_cnt = df["source"].value_counts().iloc[0]
        line3 = f"3️⃣ **정보량 & 출처 특성**: 문서당 평균 **{avg_len:.0f}자**의 텍스트로 구성되어 있으며, 주요 출처 중 **'{top_src}'**({top_src_cnt}건)의 영향력과 발행 비중이 가장 두드러집니다."
    else:
        line3 = f"3️⃣ **정보량 & 텍스트 특성**: 문서당 평균 **{avg_len:.0f}자** 수준의 요약 텍스트를 포함하고 있어, 사용자들이 직관적이고 핵심 위주의 정보를 신속히 소비하는 패턴을 보입니다."
        
    return [line1, line2, line3]
