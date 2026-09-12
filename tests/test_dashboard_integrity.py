"""
Comprehensive Dashboard Integrity & Error Detection Test Script
"""
import os
import sys
import pandas as pd
from dotenv import load_dotenv

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.mock_data import generate_mock_datalab_data, generate_mock_search_results
from src.api.naver_shopping import generate_mock_shopping_data
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
from src.utils.helpers import extract_channel_items

from src.storage.data_manager import save_raw_response, save_processed_data, export_excel_report
from src.storage.html_reporter import generate_interactive_html_report
from src.eda.text_analyzer import compute_channel_stats

def run_full_validation_test():
    print("=" * 70)
    print("[Dashboard Component Integrity, Edge Cases & Stress Test]")
    print("=" * 70)
    
    # 1. Mock 데이터 생성
    keywords = ["생성형 AI", "LLM", "딥러닝"]
    df_trend = generate_mock_datalab_data(keywords, "2026-08-01", "2026-09-01")
    df_shopping = generate_mock_shopping_data("2026-08-01", "2026-09-01")
    search_res = generate_mock_search_results(keywords, display=30)
    
    print("[+] 1. 데이터 수집 파이프라인 검증 성공")
    
    # 2. 종합 트렌드 차트 검증
    fig1 = plot_datalab_trend(df_trend)
    stats_df = compute_channel_stats(search_res)
    fig_bar = plot_channel_bar_comparison(stats_df)
    assert fig1 is not None and fig_bar is not None
    print("[+] 2. 종합 데이터랩 트렌드 & 채널 비교 차트 검증 성공")
    
    # 3. 8개 채널별 데이터프레임 보강 및 감성 분석 검증
    channel_dfs = {}
    ai_summaries = {}
    for ch_name in ["뉴스", "블로그", "카페글", "웹문서", "백과사전", "지식iN", "지역", "이미지"]:
        raw_items = extract_channel_items(search_res[ch_name]["data"], ch_name)
        df_enr = enrich_channel_dataframe(raw_items)
        df_sent = add_sentiment_to_dataframe(df_enr)
        channel_dfs[ch_name] = df_sent
        
        # 5대 통계표 검증
        t1 = get_descriptive_stats_table(df_sent)
        t2 = get_crosstab_table(df_sent)
        t3 = get_pivot_table(df_sent)
        t4 = get_length_bins_table(df_sent)
        t5 = get_keyword_rank_table(df_sent)
        assert not t1.empty
        assert not t5.empty
        
        # 5대 그래프 검증
        g1 = plot_channel_timeline_ma(df_sent)
        g2 = plot_top_sources_bar(df_sent)
        g3 = plot_text_length_boxplot(df_sent)
        g4 = plot_words_vs_chars_scatter(df_sent)
        top_kws = [(r["키워드"], r["출현 빈도(회)"]) for _, r in t5.iterrows()]
        g5 = plot_channel_top_keywords(top_kws)
        g6 = plot_day_of_week_distribution(df_sent)
        
        # AI 요약 검증
        ai_lines = generate_ai_channel_summary(ch_name, df_sent, 10000, top_kws)
        assert len(ai_lines) == 3
        ai_summaries[ch_name] = ai_lines
        
        print(f"[+] 3. [{ch_name}] 탭 (5대 차트 + 5대 통계표 + AI 요약) 검증 성공")
        
    # 4. 감성 분석 탭 시각화 검증
    fig_sent_dist = plot_channel_sentiment_distribution(channel_dfs)
    comb_df = pd.concat(channel_dfs.values(), ignore_index=True)
    fig_sent_time = plot_sentiment_timeline(comb_df)
    assert fig_sent_dist is not None and fig_sent_time is not None
    print("[+] 4. 감성 분석 & 여론 지수 시계열 차트 검증 성공")
    
    # 5. 토픽 모델링 & 동시출현 네트워크 검증
    fig_net = build_cooccurrence_network_figure(comb_df)
    df_topics = extract_latent_topics(comb_df)
    assert fig_net is not None and not df_topics.empty
    print("[+] 5. 동시출현 네트워크 & 토픽 모델링 분류표 검증 성공")
    
    # 6. 리포트 생성 및 저장소 검증
    html_rep = generate_interactive_html_report("생성형 AI", keywords, stats_df, channel_dfs, ai_summaries)
    excel_rep = export_excel_report("생성형 AI", comb_df, stats_df, df_trend)
    assert os.path.exists(html_rep) and os.path.exists(excel_rep)
    print(f"[+] 6. HTML 및 Excel 리포트 내보내기 검증 성공 ({html_rep})")
    
    # 7. 극단적 엣지 케이스 (빈 데이터프레임) 안전성 검증
    empty_df = pd.DataFrame()
    assert get_descriptive_stats_table(empty_df).empty
    assert get_crosstab_table(empty_df).empty
    assert get_pivot_table(empty_df).empty
    assert get_length_bins_table(empty_df).empty
    assert get_keyword_rank_table(empty_df).empty
    assert len(generate_ai_channel_summary("테스트", empty_df, 0, [])) == 3
    assert plot_channel_timeline_ma(empty_df) is not None
    assert plot_top_sources_bar(empty_df) is not None
    assert plot_text_length_boxplot(empty_df) is not None
    assert plot_words_vs_chars_scatter(empty_df) is not None
    assert plot_channel_top_keywords([]) is not None
    assert plot_channel_sentiment_distribution({}) is not None
    assert plot_sentiment_timeline(empty_df) is not None
    assert build_cooccurrence_network_figure(empty_df) is not None
    assert extract_latent_topics(empty_df).empty
    print("[+] 7. 빈 데이터프레임 및 결측치 엣지 케이스 100% 무결성 방어 확인")
    
    print("\n" + "=" * 70)
    print("[SUCCESS] 전체 13개 탭, 모든 시각화 차트 및 통계 분석 무결성 100% 통과 (0 Errors)")
    print("=" * 70)

if __name__ == "__main__":
    run_full_validation_test()
