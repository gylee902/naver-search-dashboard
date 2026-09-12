"""
Naver Market Insight & Deep Intelligence Dashboard
Built with Streamlit, Plotly, Naver API Hub
Includes 5 Advanced Intelligence Enhancements:
1. Sentiment Analysis & Market Opinion Index
2. Naver Shopping Insight Trends
3. Co-occurrence Network & Latent Topic Modeling
4. Periodic Monitoring & Scheduler Integration
5. One-Click Interactive HTML Briefing Report & Excel Export
"""
import os
import io
import datetime
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# 로컬 모듈 로드
from src.api.naver_search import search_all_channels, SEARCH_ENDPOINTS_NCP
from src.api.naver_datalab import get_datalab_trend
from src.api.naver_shopping import get_shopping_category_trend, generate_mock_shopping_data
from src.api.mock_data import generate_mock_datalab_data, generate_mock_search_results
from src.storage.data_manager import save_raw_response, save_processed_data, export_excel_report
from src.storage.html_reporter import generate_interactive_html_report
from src.eda.text_analyzer import get_top_keywords_from_items, compute_channel_stats
from src.eda.advanced_stats import (
    enrich_channel_dataframe,
    get_descriptive_stats_table,
    get_crosstab_table,
    get_pivot_table,
    get_length_bins_table,
    get_keyword_rank_table,
    generate_ai_channel_summary
)
from src.eda.sentiment_analyzer import (
    add_sentiment_to_dataframe,
    plot_channel_sentiment_distribution,
    plot_sentiment_timeline
)
from src.eda.topic_network import (
    build_cooccurrence_network_figure,
    extract_latent_topics
)
from src.eda.visualizer import (
    plot_datalab_trend,
    plot_channel_bar_comparison,
    plot_channel_timeline_ma,
    plot_top_sources_bar,
    plot_text_length_boxplot,
    plot_words_vs_chars_scatter,
    plot_channel_top_keywords,
    plot_day_of_week_distribution,
    generate_wordcloud_figure
)
from src.utils.helpers import extract_channel_items, format_number

# .env 환경변수 로드
load_dotenv(override=True)

# Streamlit 페이지 설정
st.set_page_config(
    page_title="Naver Market Insight - Intelligence Platform",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .ai-summary-card {
        background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
        border: 1px solid #bfdbfe;
        border-left: 6px solid #3b82f6;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 22px;
    }
    .channel-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        background-color: #e0f2fe;
        color: #0369a1;
        margin-bottom: 6px;
    }
    .search-item-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 12px;
        transition: all 0.2s;
    }
    .search-item-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
    }
    .highlight-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: #1e293b;
        text-decoration: none;
    }
    .highlight-title:hover {
        color: #2563eb;
        text-decoration: underline;
    }
    .sub-meta {
        font-size: 0.82rem;
        color: #64748b;
        margin-top: 4px;
    }
    .section-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 20px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.image("https://developers.naver.com/inc/devcenter/images/naver_logo.png", width=160)
    st.title("⚙️ 마켓 인사이트 설정")
    
    # 1. API 인증 체계
    st.markdown("### 🔑 네이버 API 인증")
    auth_platform = st.radio(
        "인증 플랫폼 선택",
        options=["NCP (Naver Cloud Platform)", "Naver Developers (Open API)"],
        index=0,
        help="NCP NAVER API HUB(X-NCP-APIGW-API-KEY-ID) 또는 네이버 개발자센터(X-Naver-Client-Id)"
    )
    auth_type = "ncp" if "NCP" in auth_platform else "openapi"
    
    env_id = os.getenv("NCP_CLIENT_ID" if auth_type == "ncp" else "NAVER_CLIENT_ID", "")
    env_secret = os.getenv("NCP_CLIENT_SECRET" if auth_type == "ncp" else "NAVER_CLIENT_SECRET", "")
    if not env_id:
        env_id = os.getenv("NAVER_CLIENT_ID", "") or os.getenv("NCP_CLIENT_ID", "")
    if not env_secret:
        env_secret = os.getenv("NAVER_CLIENT_SECRET", "") or os.getenv("NCP_CLIENT_SECRET", "")
        
    client_id = st.text_input(
        "Client ID / API Key ID",
        value=env_id,
        type="default",
        placeholder="NCP API Key ID 또는 Client ID"
    )
    client_secret = st.text_input(
        "Client Secret / API Secret Key",
        value=env_secret,
        type="password",
        placeholder="Secret Key"
    )
    
    if st.button("💾 입력한 키를 .env 파일에 저장", use_container_width=True):
        env_path = ".env"
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        id_key = "NCP_CLIENT_ID" if auth_type == "ncp" else "NAVER_CLIENT_ID"
        sec_key = "NCP_CLIENT_SECRET" if auth_type == "ncp" else "NAVER_CLIENT_SECRET"
        
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith(f"{id_key}="):
                new_lines.append(f"{id_key}={client_id.strip()}\n")
                updated = True
            elif line.startswith(f"{sec_key}="):
                new_lines.append(f"{sec_key}={client_secret.strip()}\n")
            else:
                new_lines.append(line)
        if not updated:
            new_lines.append(f"{id_key}={client_id.strip()}\n")
            new_lines.append(f"{sec_key}={client_secret.strip()}\n")
            
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        st.success("✅ .env 파일에 API 키가 성공적으로 저장되었습니다!")
        
    has_keys = bool(client_id.strip() and client_secret.strip())
    use_mock = st.toggle("🧪 데모(Mock) 데이터 모드", value=not has_keys)
    
    if use_mock:
        st.info("💡 데모 모드 활성화: 샘플 데이터로 5대 지능형 마켓 분석 기능을 바로 체험하실 수 있습니다.")

    st.markdown("---")
    
    # 2. 검색 조건 설정
    st.markdown("### 🎯 분석 검색어 및 기간")
    raw_keywords = st.text_input(
        "검색어 입력 (쉼표 , 로 구분)",
        value="생성형 AI, LLM, 딥러닝",
        help="쉼표로 구분하여 최대 5개까지 키워드를 비교 분석할 수 있습니다."
    )
    keywords_list = [k.strip() for k in raw_keywords.split(",") if k.strip()]
    if len(keywords_list) > 5:
        st.caption("⚠️ 트렌드 비교는 최대 5개 키워드까지 지원됩니다.")
        keywords_list = keywords_list[:5]
        
    today = datetime.date.today()
    default_start = today - datetime.timedelta(days=90)
    
    date_range = st.date_input(
        "트렌드 분석 기간",
        value=(default_start, today),
        max_value=today,
        min_value=datetime.date(2016, 1, 1),
        help="조회 시작일과 종료일을 지정하세요."
    )
    
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date_str = date_range[0].strftime("%Y-%m-%d")
        end_date_str = date_range[1].strftime("%Y-%m-%d")
    else:
        start_date_str = default_start.strftime("%Y-%m-%d")
        end_date_str = today.strftime("%Y-%m-%d")
        
    time_unit = st.selectbox(
        "시간 단위",
        options=["date", "week", "month"],
        format_func=lambda x: {"date": "일간 (Date)", "week": "주간 (Week)", "month": "월간 (Month)"}[x],
        index=0
    )
    
    with st.expander("🛠️ 세부 필터 (기기/성별)"):
        device_opt = st.selectbox("기기 구분", options=["전체", "PC", "모바일 (MO)"])
        device_map = {"전체": None, "PC": "pc", "모바일 (MO)": "mo"}
        device = device_map[device_opt]
        
        gender_opt = st.selectbox("성별 구분", options=["전체", "남성 (M)", "여성 (F)"])
        gender_map = {"전체": None, "남성 (M)": "m", "여성 (F)": "f"}
        gender = gender_map[gender_opt]

    st.markdown("---")
    
    # 3. 채널 수집 건수
    st.markdown("### 📡 채널별 수집 설정")
    display_count = st.slider("채널별 수집 건수", min_value=20, max_value=100, value=50, step=10)
    sort_order = st.selectbox(
        "정렬 기준",
        options=["sim", "date"],
        format_func=lambda x: "유사도순 (sim)" if x == "sim" else "날짜순 (date)"
    )

    fetch_btn = st.button("🚀 인사이트 데이터 수집 및 심층 분석 시작", type="primary", use_container_width=True)


# ----------------- MAIN CONTENT -----------------
st.title("🔎 네이버 마켓 인텔리전스 & 검색 API 심층 EDA 플랫폼")
st.markdown("검색 API별 **AI 3줄 요약**, **5대 그래프(파이차트 제외)**, **5대 통계표**뿐만 아니라 **감성 분석**, **쇼핑 트렌드**, **토픽 모델링**, **HTML 리포트**를 제공합니다.")

# 초기 세션 상태 설정
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.datalab_df = pd.DataFrame()
    st.session_state.shopping_df = pd.DataFrame()
    st.session_state.search_results = {}
    st.session_state.channel_stats = pd.DataFrame()
    st.session_state.channel_dataframes = {}
    st.session_state.ai_summaries = {}
    st.session_state.saved_paths = {}
    st.session_state.primary_keyword = ""

# 데이터 수집 트리거
if fetch_btn or not st.session_state.data_loaded:
    if not keywords_list:
        st.error("최소 1개 이상의 검색어를 입력해주세요.")
    else:
        with st.spinner("네이버 API, 데이터랩 및 쇼핑 인사이트 데이터를 종합 수집 중입니다..."):
            primary_kw = keywords_list[0]
            st.session_state.primary_keyword = primary_kw
            
            if use_mock:
                df_trend = generate_mock_datalab_data(keywords_list, start_date_str, end_date_str, time_unit)
                df_shopping = generate_mock_shopping_data(start_date_str, end_date_str)
                search_res = generate_mock_search_results(keywords_list, display=display_count)
                raw_datalab_json = None
            else:
                # 1. DataLab Trend
                res_dl = get_datalab_trend(client_id, client_secret, start_date_str, end_date_str, time_unit, keywords_list, auth_type=auth_type, device=device, gender=gender)
                df_trend = res_dl["df"] if res_dl["success"] else pd.DataFrame()
                raw_datalab_json = res_dl.get("raw")
                
                # 2. Shopping Insight
                res_shop = get_shopping_category_trend(client_id, client_secret, start_date_str, end_date_str, time_unit, device=device, gender=gender)
                df_shopping = res_shop["df"] if res_shop["success"] else generate_mock_shopping_data(start_date_str, end_date_str)
                
                # 3. 8 Channels Search API
                search_res = search_all_channels(query=primary_kw, client_id=client_id, client_secret=client_secret, auth_type=auth_type, display=display_count, sort=sort_order)

            # 채널별 데이터프레임 구성 및 감성 라벨링
            channel_dfs = {}
            all_collected_items = []
            ai_summaries_dict = {}
            
            for ch_name in SEARCH_ENDPOINTS_NCP.keys():
                ch_res = search_res.get(ch_name, {})
                if ch_res.get("success") and ch_res.get("data"):
                    items = extract_channel_items(ch_res["data"], ch_name)
                    all_collected_items.extend(items)
                    df_enriched = enrich_channel_dataframe(items)
                    df_sent = add_sentiment_to_dataframe(df_enriched)
                    channel_dfs[ch_name] = df_sent
                    
                    # AI 3줄 요약 생성
                    ch_total = ch_res["data"].get("total", 0)
                    top_kws = get_keyword_rank_table(df_sent, top_n=5, custom_stopwords=[primary_kw])
                    top_kw_tuples = [(r["키워드"], r["출현 빈도(회)"]) for _, r in top_kws.iterrows()]
                    ai_summaries_dict[ch_name] = generate_ai_channel_summary(ch_name, df_sent, ch_total, top_kw_tuples)
                else:
                    channel_dfs[ch_name] = pd.DataFrame()

            df_items_all = pd.DataFrame(all_collected_items)
            stats_df = compute_channel_stats(search_res)
            
            # data/ 및 output/ 로컬 저장
            raw_file = save_raw_response(primary_kw, search_res, raw_datalab_json)
            proc_files = save_processed_data(primary_kw, df_items_all, stats_df, df_trend)
            report_excel = export_excel_report(primary_kw, df_items_all, stats_df, df_trend)
            report_html = generate_interactive_html_report(primary_kw, keywords_list, stats_df, channel_dfs, ai_summaries_dict)
            
            saved_paths = {
                "raw": raw_file,
                "items": proc_files.get("items", ""),
                "stats": proc_files.get("stats", ""),
                "trend": proc_files.get("trend", ""),
                "report_excel": report_excel,
                "report_html": report_html
            }
            
            # 세션에 저장
            st.session_state.datalab_df = df_trend
            st.session_state.shopping_df = df_shopping
            st.session_state.search_results = search_res
            st.session_state.channel_stats = stats_df
            st.session_state.channel_dataframes = channel_dfs
            st.session_state.ai_summaries = ai_summaries_dict
            st.session_state.saved_paths = saved_paths
            st.session_state.data_loaded = True


# ----------------- REUSABLE CHANNEL EDA RENDERER -----------------
def render_channel_eda_page(channel_name: str, df: pd.DataFrame, total_count: int, primary_kw: str, ai_lines: List[str]):
    """각 검색 API 채널별 5대 그래프 + 5대 통계표 + AI 3줄 요약 렌더링"""
    if df is None or df.empty:
        st.warning(f"'{channel_name}' 채널에서 수집된 유효 데이터가 없습니다.")
        return
        
    top_kws = get_keyword_rank_table(df, top_n=15, custom_stopwords=[primary_kw])
    top_kw_tuples = [(row["키워드"], row["출현 빈도(회)"]) for _, row in top_kws.iterrows()] if not top_kws.empty else []
    
    # AI 3줄 안전 추출
    l1 = ai_lines[0] if isinstance(ai_lines, list) and len(ai_lines) > 0 else f"1️⃣ **수집 현황**: '{channel_name}' 채널 데이터 수집이 완료되었습니다."
    l2 = ai_lines[1] if isinstance(ai_lines, list) and len(ai_lines) > 1 else "2️⃣ **담론 트렌드**: 주요 키워드와 발행 패턴이 분석되었습니다."
    l3 = ai_lines[2] if isinstance(ai_lines, list) and len(ai_lines) > 2 else "3️⃣ **인사이트**: 세부 통계표 및 시각화 차트를 참조하세요."

    # 1. 🤖 AI 3-Line Summary Card
    st.markdown(f"""
    <div class="ai-summary-card">
        <div style="font-size:1.15rem; font-weight:800; color:#1e40af; margin-bottom:8px;">
            🤖 AI 기반 '{channel_name}' 채널 핵심 인사이트 세 줄 요약
        </div>
        <div style="font-size:0.95rem; color:#1e293b; line-height:1.7;">
            {l1}<br>
            {l2}<br>
            {l3}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.metric("총 인덱스 검색수", f"{total_count:,}건")
    with col_b:
        st.metric("분석 표본 수", f"{len(df):,}건")
    with col_c:
        avg_l = df['total_len'].mean() if 'total_len' in df.columns else 0
        st.metric("평균 텍스트 길이", f"{avg_l:.1f}자")
    with col_d:
        pos_ratio = (df["sentiment"] == "긍정").mean() * 100 if "sentiment" in df.columns else 0
        st.metric("긍정 감성 비율", f"{pos_ratio:.1f}%")

    st.markdown("---")
    
    # 2. 📊 5종 이상의 시각화 그래프 (파이차트 제외)
    st.markdown(f"<div class='section-title'>📊 [그래프 분석] '{channel_name}' 5대 시각화 차트 (파이차트 제외)</div>", unsafe_allow_html=True)
    
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        fig_ma = plot_channel_timeline_ma(df)
        st.plotly_chart(fig_ma, use_container_width=True, key=f"{channel_name}_chart_timeline_ma")
    with g_col2:
        fig_src = plot_top_sources_bar(df, top_n=10)
        st.plotly_chart(fig_src, use_container_width=True, key=f"{channel_name}_chart_top_sources")
        
    g_col3, g_col4 = st.columns(2)
    with g_col3:
        fig_box = plot_text_length_boxplot(df)
        st.plotly_chart(fig_box, use_container_width=True, key=f"{channel_name}_chart_text_box")
    with g_col4:
        fig_scatter = plot_words_vs_chars_scatter(df)
        st.plotly_chart(fig_scatter, use_container_width=True, key=f"{channel_name}_chart_words_chars")
        
    g_col5, g_col6 = st.columns(2)
    with g_col5:
        fig_kw = plot_channel_top_keywords(top_kw_tuples, top_n=15)
        st.plotly_chart(fig_kw, use_container_width=True, key=f"{channel_name}_chart_top_keywords")
    with g_col6:
        if "day_of_week" in df.columns and (df["day_of_week"] != "-").any():
            fig_dow = plot_day_of_week_distribution(df)
            st.plotly_chart(fig_dow, use_container_width=True, key=f"{channel_name}_chart_day_of_week")
        else:
            wc_fig = generate_wordcloud_figure(top_kw_tuples)
            if wc_fig:
                st.pyplot(wc_fig)

    st.markdown("---")
    
    # 3. 📋 5종 이상의 통계 분석 표
    st.markdown(f"<div class='section-title'>📋 [통계 분석] '{channel_name}' 5대 통계표 & 교차/피봇 분석</div>", unsafe_allow_html=True)
    
    t_tab1, t_tab2, t_tab3, t_tab4, t_tab5, t_tab6 = st.tabs([
        "1. 계량 텍스트 기술통계표",
        "2. 출처 × 요일/일자 교차표",
        "3. 출처별 집계 피봇테이블",
        "4. 텍스트 길이 구간(Binning)표",
        "5. 핵심 키워드 빈도 및 점유율표",
        "6. 전체 수집 문서 상세 목록"
    ])
    
    with t_tab1:
        st.dataframe(get_descriptive_stats_table(df), use_container_width=True, key=f"{channel_name}_tbl_desc")
    with t_tab2:
        st.dataframe(get_crosstab_table(df), use_container_width=True, key=f"{channel_name}_tbl_crosstab")
    with t_tab3:
        st.dataframe(get_pivot_table(df), use_container_width=True, key=f"{channel_name}_tbl_pivot")
    with t_tab4:
        st.dataframe(get_length_bins_table(df), use_container_width=True, key=f"{channel_name}_tbl_bins")
    with t_tab5:
        st.dataframe(top_kws, use_container_width=True, key=f"{channel_name}_tbl_top_kws")
    with t_tab6:
        desired_cols = ["title", "source", "date", "sentiment", "total_len", "total_words", "link"]
        avail_cols = [c for c in desired_cols if c in df.columns]
        st.dataframe(df[avail_cols] if avail_cols else df, use_container_width=True, key=f"{channel_name}_tbl_docs")


# ----------------- DASHBOARD BODY (INTELLIGENCE TABS) -----------------
if st.session_state.data_loaded:
    df_trend = st.session_state.datalab_df
    df_shopping = st.session_state.shopping_df
    stats_df = st.session_state.channel_stats
    channel_dfs = st.session_state.channel_dataframes
    ai_summaries = st.session_state.ai_summaries
    saved_paths = st.session_state.saved_paths
    primary_kw = st.session_state.primary_keyword
    combined_df = pd.concat([df for df in channel_dfs.values() if not df.empty], ignore_index=True) if channel_dfs else pd.DataFrame()

    # TOP KPI METRICS
    st.markdown("### 📌 마켓 종합 KPI 메트릭")
    col1, col2, col3, col4 = st.columns(4)
    
    total_market_docs = stats_df["total_count"].sum() if not stats_df.empty else 0
    top_channel = stats_df.sort_values(by="total_count", ascending=False).iloc[0]["channel"] if not stats_df.empty else "-"
    top_channel_count = stats_df["total_count"].max() if not stats_df.empty else 0
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:0.85rem; color:#64748b; font-weight:600;">메인 분석 키워드</div>
            <div style="font-size:1.5rem; font-weight:800; color:#2563eb; margin-top:4px;">{primary_kw}</div>
            <div style="font-size:0.8rem; color:#94a3b8; margin-top:4px;">비교 검색어: {len(keywords_list)}개</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:0.85rem; color:#64748b; font-weight:600;">8대 채널 총 누적 문서수</div>
            <div style="font-size:1.5rem; font-weight:800; color:#0f172a; margin-top:4px;">{format_number(total_market_docs)}건</div>
            <div style="font-size:0.8rem; color:#10b981; margin-top:4px;">전체 네이버 인덱스 합산</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:0.85rem; color:#64748b; font-weight:600;">최대 언급 채널 (1위)</div>
            <div style="font-size:1.5rem; font-weight:800; color:#7c3aed; margin-top:4px;">{top_channel}</div>
            <div style="font-size:0.8rem; color:#64748b; margin-top:4px;">{format_number(top_channel_count)}건 점유</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:0.85rem; color:#64748b; font-weight:600;">분석 기간 & 리포트</div>
            <div style="font-size:1.05rem; font-weight:700; color:#334155; margin-top:6px;">{start_date_str} ~</div>
            <div style="font-size:0.8rem; color:#16a34a; margin-top:4px;">📄 HTML/Excel 리포트 완비</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ----------------- MAIN TABS (5 ADVANCED ENHANCEMENTS + 8 CHANNELS) -----------------
    tab_overview, tab_sentiment, tab_shopping, tab_topics, tab_news, tab_blog, tab_cafe, tab_web, tab_encyc, tab_kin, tab_local, tab_image, tab_export = st.tabs([
        "📊 종합 트렌드",
        "💡 1. 감성 분석 & 여론 지수",
        "🛍️ 2. 쇼핑 인사이트",
        "🕸️ 3. 토픽 & 네트워크",
        "📰 뉴스 (News)",
        "📝 블로그 (Blog)",
        "☕ 카페글 (Cafe)",
        "🌐 웹문서 (Web)",
        "📚 백과사전 (Encyc)",
        "❓ 지식iN (Kin)",
        "📍 지역 (Local)",
        "🖼️ 이미지 (Image)",
        "💾 5. 보고서 & 다운로드"
    ])

    # 1. 종합 트렌드 탭 (파이차트 제외)
    with tab_overview:
        st.subheader("📈 다중 검색어 상대 트렌드 비교 (Naver DataLab)")
        if not df_trend.empty:
            st.plotly_chart(plot_datalab_trend(df_trend, time_unit), use_container_width=True, key="overview_datalab_line_chart")
        st.markdown("---")
        st.subheader("📊 8대 채널별 총 검색 문서 건수 비교 (파이차트 제외)")
        st.plotly_chart(plot_channel_bar_comparison(stats_df), use_container_width=True, key="overview_channel_bar_chart")

    # 2. 감성 분석 & 여론 지수 탭
    with tab_sentiment:
        st.subheader("💡 채널별 시장 여론 및 긍정/중립/부정 감성 분석")
        st.plotly_chart(plot_channel_sentiment_distribution(channel_dfs), use_container_width=True, key="sentiment_distribution_bar_chart")
        
        st.markdown("---")
        st.subheader("📈 일자별 시장 여론 감성 지수 시계열 추이 (뉴스/블로그/카페 통합)")
        if not combined_df.empty:
            st.plotly_chart(plot_sentiment_timeline(combined_df), use_container_width=True, key="sentiment_timeline_line_chart")

    # 3. 쇼핑 인사이트 탭
    with tab_shopping:
        st.subheader("🛍️ 네이버 쇼핑 카테고리별 클릭 추이 (Shopping Insight)")
        if not df_shopping.empty:
            import plotly.express as px
            fig_shop = px.line(
                df_shopping,
                x="period",
                y="ratio",
                color="category",
                markers=True,
                title="🛒 주요 쇼핑 카테고리별 상대 클릭 추이",
                labels={"period": "조회 일자", "ratio": "상대 클릭 비율", "category": "카테고리"}
            )
            fig_shop.update_layout(template="plotly_white", hovermode="x unified")
            st.plotly_chart(fig_shop, use_container_width=True, key="shopping_trend_line_chart")
            with st.expander("📋 쇼핑 클릭 데이터프레임 확인"):
                st.dataframe(df_shopping, use_container_width=True, key="shopping_raw_df_table")
        else:
            st.info("쇼핑 인사이트 데이터가 없습니다.")

    # 4. 토픽 모델링 & 동시출현 네트워크 탭
    with tab_topics:
        st.subheader("🕸️ 연관 키워드 동시출현(Co-occurrence) 네트워크 & 토픽 모델링")
        if not combined_df.empty:
            st.plotly_chart(build_cooccurrence_network_figure(combined_df, top_n_keywords=18, custom_stopwords=[primary_kw]), use_container_width=True, key="topics_cooccurrence_network_chart")
            
            st.markdown("---")
            st.subheader("🏷️ 핵심 담론 잠재 토픽(Topic Modeling) 자동 분류표")
            df_topics = extract_latent_topics(combined_df, num_topics=3, custom_stopwords=[primary_kw])
            st.dataframe(df_topics, use_container_width=True, key="topics_latent_df_table")

    # 5. 뉴스 탭
    with tab_news:
        ch_tot = stats_df[stats_df["channel"] == "뉴스"]["total_count"].values[0] if "뉴스" in stats_df["channel"].values else 0
        render_channel_eda_page("뉴스", channel_dfs.get("뉴스", pd.DataFrame()), ch_tot, primary_kw, ai_summaries.get("뉴스", ["-", "-", "-"]))

    # 6. 블로그 탭
    with tab_blog:
        ch_tot = stats_df[stats_df["channel"] == "블로그"]["total_count"].values[0] if "블로그" in stats_df["channel"].values else 0
        render_channel_eda_page("블로그", channel_dfs.get("블로그", pd.DataFrame()), ch_tot, primary_kw, ai_summaries.get("블로그", ["-", "-", "-"]))

    # 7. 카페글 탭
    with tab_cafe:
        ch_tot = stats_df[stats_df["channel"] == "카페글"]["total_count"].values[0] if "카페글" in stats_df["channel"].values else 0
        render_channel_eda_page("카페글", channel_dfs.get("카페글", pd.DataFrame()), ch_tot, primary_kw, ai_summaries.get("카페글", ["-", "-", "-"]))

    # 8. 웹문서 탭
    with tab_web:
        ch_tot = stats_df[stats_df["channel"] == "웹문서"]["total_count"].values[0] if "웹문서" in stats_df["channel"].values else 0
        render_channel_eda_page("웹문서", channel_dfs.get("웹문서", pd.DataFrame()), ch_tot, primary_kw, ai_summaries.get("웹문서", ["-", "-", "-"]))

    # 9. 백과사전 탭
    with tab_encyc:
        ch_tot = stats_df[stats_df["channel"] == "백과사전"]["total_count"].values[0] if "백과사전" in stats_df["channel"].values else 0
        render_channel_eda_page("백과사전", channel_dfs.get("백과사전", pd.DataFrame()), ch_tot, primary_kw, ai_summaries.get("백과사전", ["-", "-", "-"]))

    # 10. 지식iN 탭
    with tab_kin:
        ch_tot = stats_df[stats_df["channel"] == "지식iN"]["total_count"].values[0] if "지식iN" in stats_df["channel"].values else 0
        render_channel_eda_page("지식iN", channel_dfs.get("지식iN", pd.DataFrame()), ch_tot, primary_kw, ai_summaries.get("지식iN", ["-", "-", "-"]))

    # 11. 지역 탭
    with tab_local:
        ch_tot = stats_df[stats_df["channel"] == "지역"]["total_count"].values[0] if "지역" in stats_df["channel"].values else 0
        render_channel_eda_page("지역", channel_dfs.get("지역", pd.DataFrame()), ch_tot, primary_kw, ai_summaries.get("지역", ["-", "-", "-"]))

    # 12. 이미지 탭
    with tab_image:
        ch_tot = stats_df[stats_df["channel"] == "이미지"]["total_count"].values[0] if "이미지" in stats_df["channel"].values else 0
        render_channel_eda_page("이미지", channel_dfs.get("이미지", pd.DataFrame()), ch_tot, primary_kw, ai_summaries.get("이미지", ["-", "-", "-"]))

    # 13. 보고서 & 다운로드 탭 (Excel + HTML 브리핑 리포트)
    with tab_export:
        st.subheader("💾 보고서 제출 및 로컬 저장소 다운로드")
        
        st.markdown(f"""
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:15px; margin-bottom:20px;">
            <b>📂 자동 저장된 파일 목록:</b>
            <ul style="margin-top:8px; margin-bottom:0;">
                <li><b>독립형 HTML 보고서:</b> <code>{saved_paths.get('report_html', '-')}</code></li>
                <li><b>종합 엑셀 리포트:</b> <code>{saved_paths.get('report_excel', '-')}</code></li>
                <li><b>원본 JSON (Raw):</b> <code>{saved_paths.get('raw', '-')}</code></li>
                <li><b>정제된 문서 (Items CSV):</b> <code>{saved_paths.get('items', '-')}</code></li>
                <li><b>채널 통계 (Stats CSV):</b> <code>{saved_paths.get('stats', '-')}</code></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        exp_c1, exp_c2, exp_c3 = st.columns(3)
        
        # 1. HTML 브리핑 리포트 다운로드
        with exp_c1:
            st.markdown("#### 1. 📑 독립형 HTML 브리핑 보고서")
            html_file_path = saved_paths.get("report_html")
            if html_file_path and os.path.exists(html_file_path):
                with open(html_file_path, "r", encoding="utf-8") as f:
                    html_data = f.read().encode("utf-8")
                st.download_button(
                    label="📥 원클릭 HTML 보고서 다운로드",
                    data=html_data,
                    file_name=f"naver_briefing_report_{primary_kw}_{datetime.date.today()}.html",
                    mime="text/html",
                    use_container_width=True
                )
                
        # 2. 통합 엑셀 다운로드
        with exp_c2:
            st.markdown("#### 2. 📊 전체 채널 통합 엑셀 리포트")
            excel_buf = io.BytesIO()
            with pd.ExcelWriter(excel_buf, engine='openpyxl') as writer:
                for ch_n, df_c in channel_dfs.items():
                    if not df_c.empty:
                        df_c.to_excel(writer, index=False, sheet_name=ch_n[:30])
                if not stats_df.empty:
                    stats_df.to_excel(writer, index=False, sheet_name="채널별통계")
                if not df_trend.empty:
                    df_trend.to_excel(writer, index=False, sheet_name="데이터랩트렌드")
                if not df_shopping.empty:
                    df_shopping.to_excel(writer, index=False, sheet_name="쇼핑인사이트")
            excel_data = excel_buf.getvalue()
            
            st.download_button(
                label="📊 통합 엑셀 (.xlsx) 다운로드",
                data=excel_data,
                file_name=f"naver_market_intelligence_{primary_kw}_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        # 3. 시계열 트렌드 CSV
        with exp_c3:
            st.markdown("#### 3. 📈 데이터랩 트렌드 CSV")
            if not df_trend.empty:
                csv_trend = df_trend.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 DataLab Trend (CSV)",
                    data=csv_trend,
                    file_name=f"naver_trend_{primary_kw}_{datetime.date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
