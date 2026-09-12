"""
Plotly-based Visualization Module for Naver Market Insight & Channel EDA
Provides comprehensive charts without pie charts as per user requirements.
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import networkx as nx
from typing import List, Tuple, Dict, Any
import os
import platform
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# 모던 테마 색상 팔레트
COLOR_PALETTE = [
    "#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#06b6d4",
    "#ec4899", "#6366f1", "#14b8a6", "#f43f5e", "#64748b"
]

def get_korean_font_path() -> str | None:
    """크로스 플랫폼(Linux, Windows, macOS) 한글 폰트 경로 자동 탐색"""
    candidates = [
        # Linux (Streamlit Cloud / Debian / Ubuntu)
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumSquareR.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/baekmuk/gulim.ttf",
        # Windows
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "malgun.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "gulim.ttc"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "batang.ttc"),
        # macOS
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/Library/Fonts/NanumGothic.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
            
    try:
        for font in fm.fontManager.ttflist:
            if any(k in font.name.lower() for k in ["nanum", "malgun", "gothic", "noto sans cjk", "apple"]):
                return font.fname
    except Exception:
        pass
    return None

# Matplotlib 한글 폰트 및 마이너스 기호 설정
plt.rcParams['axes.unicode_minus'] = False
_korean_font = get_korean_font_path()
if _korean_font:
    try:
        fm.fontManager.addfont(_korean_font)
        _font_prop = fm.FontProperties(fname=_korean_font)
        plt.rcParams['font.family'] = _font_prop.get_name()
    except Exception:
        pass


# ----------------- 1. 공통 / 종합 시각화 (파이차트 제외) -----------------

def plot_datalab_trend(df_datalab: pd.DataFrame, time_unit: str = "date") -> go.Figure:
    """데이터랩 검색어 트렌드 시계열 라인 차트"""
    if df_datalab.empty:
        fig = go.Figure()
        fig.update_layout(title="트렌드 데이터가 없습니다.")
        return fig
        
    fig = px.line(
        df_datalab,
        x="period",
        y="ratio",
        color="keyword",
        markers=True,
        title="📈 네이버 통합 검색어 트렌드 비교 (상대 검색 비율 0~100)",
        labels={"period": "조회 기간", "ratio": "상대 검색비율 (%)", "keyword": "검색어"},
        color_discrete_sequence=COLOR_PALETTE
    )
    
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", range=[0, 105]),
        font=dict(family="Pretendard, -apple-system, sans-serif")
    )
    return fig


def plot_channel_bar_comparison(df_stats: pd.DataFrame) -> go.Figure:
    """채널별 총 검색건수 수평 바 차트 (파이차트 대체)"""
    if df_stats.empty:
        return go.Figure()
        
    df_sorted = df_stats.sort_values(by="total_count", ascending=True)
    
    fig = px.bar(
        df_sorted,
        x="total_count",
        y="channel",
        orientation="h",
        text="total_count",
        title="📊 8대 채널별 총 검색 문서 건수 비교",
        labels={"total_count": "총 검색건수", "channel": "채널"},
        color="channel",
        color_discrete_sequence=COLOR_PALETTE
    )
    
    fig.update_traces(texttemplate="%{text:,.0f}건", textposition="outside")
    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        margin=dict(l=40, r=60, t=50, b=40),
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        font=dict(family="Pretendard, -apple-system, sans-serif")
    )
    return fig


# ----------------- 2. 채널별 심층 EDA 차트 5종 (파이차트 제외) -----------------

def plot_channel_timeline_ma(df: pd.DataFrame) -> go.Figure:
    """[그래프 1] 시계열 발행 추이 및 3일 이동평균선 영역/라인 차트"""
    if df.empty or "date" not in df.columns or (df["date"] == "-").all():
        fig = go.Figure()
        fig.update_layout(title="유효한 발행 일자 데이터가 없습니다.", template="plotly_white")
        return fig
        
    valid_df = df[df["date"] != "-"].copy()
    timeline = valid_df.groupby("date").size().reset_index(name="count")
    timeline["date"] = pd.to_datetime(timeline["date"])
    timeline = timeline.sort_values(by="date")
    
    # 3일 이동평균 계산
    timeline["ma3"] = timeline["count"].rolling(window=3, min_periods=1).mean().round(1)
    
    fig = go.Figure()
    # 영역/바 차트
    fig.add_trace(go.Bar(
        x=timeline["date"],
        y=timeline["count"],
        name="일일 발행건수",
        marker_color="#93c5fd",
        opacity=0.75
    ))
    # 이동평균 라인
    fig.add_trace(go.Scatter(
        x=timeline["date"],
        y=timeline["ma3"],
        name="3일 이동평균 (추세선)",
        mode="lines+markers",
        line=dict(color="#1d4ed8", width=3)
    ))
    
    fig.update_layout(
        title="📈 [Chart 1] 일자별 문서 발행 추이 및 이동평균 추세선",
        xaxis_title="발행일자",
        yaxis_title="발행 건수",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        font=dict(family="Pretendard, -apple-system, sans-serif")
    )
    return fig


def plot_top_sources_bar(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """[그래프 2] 상위 출처/언론사/작성자 TOP 10 수평 막대 차트"""
    if df.empty or "source" not in df.columns or (df["source"] == "-").all():
        fig = go.Figure()
        fig.update_layout(title="출처 정보가 충분하지 않습니다.", template="plotly_white")
        return fig
        
    valid_df = df[df["source"] != "-"].copy()
    src_counts = valid_df["source"].value_counts().head(top_n).reset_index()
    src_counts.columns = ["source", "count"]
    src_counts = src_counts.sort_values(by="count", ascending=True)
    
    fig = px.bar(
        src_counts,
        x="count",
        y="source",
        orientation="h",
        text="count",
        title=f"🏆 [Chart 2] 주요 출처 / 언론사 / 작성자 TOP {top_n}",
        labels={"count": "문서 수", "source": "출처"},
        color="count",
        color_continuous_scale="Blues"
    )
    
    fig.update_traces(texttemplate="%{text}건", textposition="outside")
    fig.update_layout(
        template="plotly_white",
        coloraxis_showscale=False,
        margin=dict(l=40, r=50, t=50, b=40),
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        font=dict(family="Pretendard, -apple-system, sans-serif")
    )
    return fig


def plot_text_length_boxplot(df: pd.DataFrame) -> go.Figure:
    """[그래프 3] 제목 및 본문 요약문 텍스트 길이 분포 박스플롯"""
    if df.empty or "title_len" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="길이 데이터가 없습니다.", template="plotly_white")
        return fig
        
    fig = go.Figure()
    fig.add_trace(go.Box(
        y=df["title_len"],
        name="제목 글자수",
        boxmean=True,
        marker_color="#3b82f6"
    ))
    fig.add_trace(go.Box(
        y=df["desc_len"],
        name="본문요약 글자수",
        boxmean=True,
        marker_color="#10b981"
    ))
    fig.add_trace(go.Box(
        y=df["total_len"],
        name="전체 글자수 합계",
        boxmean=True,
        marker_color="#8b5cf6"
    ))
    
    fig.update_layout(
        title="📦 [Chart 3] 텍스트 길이(글자수) 분포 박스플롯 (Box Plot)",
        yaxis_title="글자수 (Characters)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        font=dict(family="Pretendard, -apple-system, sans-serif")
    )
    return fig


def plot_words_vs_chars_scatter(df: pd.DataFrame) -> go.Figure:
    """[그래프 4] 글자수 vs 단어수 분포 상관관계 산점도 & 회귀선"""
    if df.empty or "total_words" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="단어수 데이터가 없습니다.", template="plotly_white")
        return fig
        
    try:
        fig = px.scatter(
            df,
            x="total_words",
            y="total_len",
            hover_data=["title", "source"],
            title="📉 [Chart 4] 단어 수 vs 글자 수 상관관계 산점도 (Scatter Plot with Trendline)",
            labels={"total_words": "전체 단어 수 (Words)", "total_len": "전체 글자 수 (Characters)"},
            color="title_words",
            color_continuous_scale="Viridis",
            trendline="ols"
        )
    except Exception:
        fig = px.scatter(
            df,
            x="total_words",
            y="total_len",
            hover_data=["title", "source"],
            title="📉 [Chart 4] 단어 수 vs 글자 수 상관관계 산점도 (Scatter Plot)",
            labels={"total_words": "전체 단어 수 (Words)", "total_len": "전체 글자 수 (Characters)"},
            color="title_words",
            color_continuous_scale="Viridis"
        )
    
    fig.update_traces(marker=dict(size=9, opacity=0.8, line=dict(width=1, color="white")))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        font=dict(family="Pretendard, -apple-system, sans-serif")
    )
    return fig


def plot_channel_top_keywords(keywords_freq: List[Tuple[str, int]], top_n: int = 15) -> go.Figure:
    """[그래프 5] 상위 15개 핵심 연관 키워드 그라디언트 바 차트"""
    if not keywords_freq:
        fig = go.Figure()
        fig.update_layout(title="키워드 빈도 데이터가 없습니다.", template="plotly_white")
        return fig
        
    df_kw = pd.DataFrame(keywords_freq, columns=["keyword", "frequency"]).head(top_n)
    df_kw = df_kw.sort_values(by="frequency", ascending=True)
    
    fig = px.bar(
        df_kw,
        x="frequency",
        y="keyword",
        orientation="h",
        text="frequency",
        title=f"🔥 [Chart 5] 주요 연관 키워드 TOP {top_n} 출현 빈도",
        labels={"frequency": "출현 빈도(회)", "keyword": "키워드"},
        color="frequency",
        color_continuous_scale="Teal"
    )
    
    fig.update_traces(texttemplate="%{text}회", textposition="outside")
    fig.update_layout(
        template="plotly_white",
        coloraxis_showscale=False,
        margin=dict(l=40, r=50, t=50, b=40),
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        font=dict(family="Pretendard, -apple-system, sans-serif")
    )
    return fig


def plot_day_of_week_distribution(df: pd.DataFrame) -> go.Figure:
    """[보너스 그래프] 요일별 발행 집중도 바 차트"""
    if df.empty or "day_of_week" not in df.columns or (df["day_of_week"] == "-").all():
        return go.Figure()
        
    valid_df = df[df["day_of_week"] != "-"].copy()
    day_order = ["월", "화", "수", "목", "금", "토", "일"]
    counts = valid_df["day_of_week"].value_counts().reindex(day_order, fill_value=0).reset_index()
    counts.columns = ["day_of_week", "count"]
    
    fig = px.bar(
        counts,
        x="day_of_week",
        y="count",
        text="count",
        title="📅 요일별 문서 발행 집중도 분포",
        labels={"day_of_week": "요일", "count": "발행 건수"},
        color="count",
        color_continuous_scale="Sunset"
    )
    
    fig.update_traces(texttemplate="%{text}건", textposition="outside")
    fig.update_layout(
        template="plotly_white",
        coloraxis_showscale=False,
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        font=dict(family="Pretendard, -apple-system, sans-serif")
    )
    return fig


# ----------------- 3. 기타 유틸리티 시각화 -----------------

def generate_wordcloud_figure(keywords_freq: List[Tuple[str, int]]):
    """Matplotlib 기반 워드클라우드 생성 (한글 폰트 깨짐 완벽 방지)"""
    if not keywords_freq:
        return None
        
    word_dict = dict(keywords_freq)
    font_path = get_korean_font_path()
    
    wc_kwargs = {
        "width": 800,
        "height": 380,
        "background_color": "white",
        "colormap": "viridis",
        "max_words": 60
    }
    if font_path:
        wc_kwargs["font_path"] = font_path
        
    try:
        wc = WordCloud(**wc_kwargs).generate_from_frequencies(word_dict)
    except Exception:
        wc = WordCloud(
            width=800,
            height=380,
            background_color="white",
            colormap="viridis",
            max_words=60
        ).generate_from_frequencies(word_dict)
        
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    plt.tight_layout(pad=0)
    return fig
