"""
Sentiment Analysis & Market Opinion Indexing Module
Classifies Korean texts into Positive, Neutral, and Negative sentiments and computes time-series trends.
"""
import re
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Tuple

# 한국어 긍정/부정 대표 어휘 사전
POSITIVE_WORDS = {
    "성장", "혁신", "성공", "상승", "호조", "우수", "최고", "추천", "인기", "돌파",
    "개선", "확대", "도약", "기대", "선도", "효과", "강점", "만족", "호평", "유망",
    "장점", "편리", "주목", "가속", "수혜", "긍정", "활약", "성과", "발전", "강세"
}

NEGATIVE_WORDS = {
    "우려", "하락", "위기", "감소", "둔화", "부진", "논란", "위험", "실패", "악화",
    "불안", "문제", "경고", "피해", "한계", "적자", "약세", "타격", "부작용", "부정",
    "침체", "갈등", "단점", "불만", "취약", "규제", "압박", "쇼크", "급락", "소송"
}

def analyze_text_sentiment(text: str) -> Dict[str, Any]:
    """단일 텍스트에 대한 감성 분석 및 스코어 반환 (-1.0 ~ +1.0)"""
    if not isinstance(text, str) or not text.strip():
        return {"sentiment": "중립", "score": 0.0, "pos_count": 0, "neg_count": 0}
        
    cleaned = re.sub(r"[^가-힣a-zA-Z\s]", " ", text)
    tokens = [t.lower().strip() for t in cleaned.split() if len(t.strip()) >= 2]
    
    pos_matches = [t for t in tokens if any(pw in t for pw in POSITIVE_WORDS)]
    neg_matches = [t for t in tokens if any(nw in t for nw in NEGATIVE_WORDS)]
    
    pos_count = len(pos_matches)
    neg_count = len(neg_matches)
    
    if pos_count > neg_count:
        sentiment = "긍정"
        score = min(1.0, (pos_count - neg_count) / max(1, (pos_count + neg_count)))
    elif neg_count > pos_count:
        sentiment = "부정"
        score = max(-1.0, (pos_count - neg_count) / max(1, (pos_count + neg_count)))
    else:
        sentiment = "중립"
        score = 0.0
        
    return {
        "sentiment": sentiment,
        "score": round(score, 2),
        "pos_count": pos_count,
        "neg_count": neg_count,
        "pos_words": pos_matches,
        "neg_words": neg_matches
    }


def add_sentiment_to_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame에 감성 라벨 및 감성 점수 컬럼 추가"""
    if df.empty:
        return df
        
    df_copy = df.copy()
    sentiments = []
    scores = []
    
    for _, row in df_copy.iterrows():
        full_text = f"{row.get('title', '')} {row.get('description', '')}"
        res = analyze_text_sentiment(full_text)
        sentiments.append(res["sentiment"])
        scores.append(res["score"])
        
    df_copy["sentiment"] = sentiments
    df_copy["sentiment_score"] = scores
    return df_copy


def plot_channel_sentiment_distribution(channel_dfs: Dict[str, pd.DataFrame]) -> go.Figure:
    """채널별 긍정/중립/부정 감성 비율 수평 누적 막대 그래프 (파이차트 대체)"""
    rows = []
    for ch_name, df in channel_dfs.items():
        if not df.empty and "sentiment" in df.columns:
            counts = df["sentiment"].value_counts(normalize=True) * 100
            rows.append({
                "channel": ch_name,
                "긍정": round(counts.get("긍정", 0.0), 1),
                "중립": round(counts.get("중립", 0.0), 1),
                "부정": round(counts.get("부정", 0.0), 1)
            })
            
    if not rows:
        fig = go.Figure()
        fig.update_layout(title="감성 분석 데이터가 없습니다.", template="plotly_white")
        return fig
        
    df_sent = pd.DataFrame(rows)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_sent["channel"],
        x=df_sent["긍정"],
        name="긍정 (Positive)",
        orientation="h",
        marker_color="#10b981",
        text=df_sent["긍정"].apply(lambda v: f"{v}%" if v > 0 else ""),
        textposition="inside"
    ))
    fig.add_trace(go.Bar(
        y=df_sent["channel"],
        x=df_sent["중립"],
        name="중립 (Neutral)",
        orientation="h",
        marker_color="#94a3b8",
        text=df_sent["중립"].apply(lambda v: f"{v}%" if v > 0 else ""),
        textposition="inside"
    ))
    fig.add_trace(go.Bar(
        y=df_sent["channel"],
        x=df_sent["부정"],
        name="부정 (Negative)",
        orientation="h",
        marker_color="#ef4444",
        text=df_sent["부정"].apply(lambda v: f"{v}%" if v > 0 else ""),
        textposition="inside"
    ))
    
    fig.update_layout(
        barmode="stack",
        title="📊 채널별 시장 여론 및 감성 반응 점유율 (100% 누적 막대)",
        xaxis=dict(title="비율 (%)", range=[0, 100], showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="채널"),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        font=dict(family="Pretendard, -apple-system, sans-serif")
    )
    return fig


def plot_sentiment_timeline(df: pd.DataFrame) -> go.Figure:
    """일자별 감성 지수 평균 시계열 추세선 차트"""
    if df.empty or "date" not in df.columns or "sentiment_score" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="감성 시계열 데이터가 없습니다.", template="plotly_white")
        return fig
        
    valid_df = df[df["date"] != "-"].copy()
    if valid_df.empty:
        fig = go.Figure()
        fig.update_layout(title="유효한 날짜의 감성 데이터가 없습니다.", template="plotly_white")
        return fig
        
    timeline_sent = valid_df.groupby("date")["sentiment_score"].mean().reset_index()
    timeline_sent["date"] = pd.to_datetime(timeline_sent["date"])
    timeline_sent = timeline_sent.sort_values(by="date")
    
    fig = px.line(
        timeline_sent,
        x="date",
        y="sentiment_score",
        markers=True,
        title="📈 일자별 시장 여론 감성 지수 추이 (-1.0: 부정 ~ +1.0: 긍정)",
        labels={"date": "발행일자", "sentiment_score": "평균 감성 지수"}
    )
    
    # 0 기준선 추가
    fig.add_hline(y=0, line_dash="dash", line_color="#94a3b8", annotation_text="중립 기준선")
    
    fig.update_traces(line=dict(color="#3b82f6", width=2.5), marker=dict(size=7))
    fig.update_layout(
        template="plotly_white",
        yaxis=dict(range=[-1.05, 1.05], showgrid=True, gridcolor="#f1f5f9"),
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        margin=dict(l=40, r=40, t=50, b=40),
        font=dict(family="Pretendard, -apple-system, sans-serif")
    )
    return fig
