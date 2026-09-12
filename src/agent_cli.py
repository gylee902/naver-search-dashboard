"""
Naver Market Insight Automated CLI Subagent with Deep EDA & AI 3-Line Summary
"""
import os
import sys
import argparse
import datetime
import pandas as pd
from dotenv import load_dotenv

# Windows cp949 인코딩 처리
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 상위 경로 모듈 로드
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.naver_search import search_all_channels, SEARCH_ENDPOINTS_NCP
from src.api.naver_datalab import get_datalab_trend
from src.api.mock_data import generate_mock_datalab_data, generate_mock_search_results
from src.storage.data_manager import save_raw_response, save_processed_data, export_excel_report
from src.eda.text_analyzer import get_top_keywords_from_items, compute_channel_stats
from src.eda.advanced_stats import (
    enrich_channel_dataframe,
    get_descriptive_stats_table,
    get_keyword_rank_table,
    generate_ai_channel_summary
)
from src.utils.helpers import extract_channel_items, format_number

load_dotenv(override=True)

def run_market_insight_pipeline(
    keywords_str: str,
    start_date: str = None,
    end_date: str = None,
    days: int = 90,
    time_unit: str = "date",
    display: int = 50,
    sort: str = "sim"
):
    print("=" * 70)
    print("[Naver Market Insight Subagent] 심층 EDA & AI 요약 자동 파이프라인 가동")
    print("=" * 70)
    
    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()][:5]
    if not keywords:
        print("[!] 유효한 검색어가 없습니다.")
        return
        
    primary_kw = keywords[0]
    print(f"[*] 메인 검색어: [{primary_kw}] | 비교 검색어: {keywords}")
    
    today = datetime.date.today()
    if not end_date:
        end_date = today.strftime("%Y-%m-%d")
    if not start_date:
        start_date = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        
    print(f"[*] 분석 기간: {start_date} ~ {end_date} (단위: {time_unit})")
    
    ncp_id = os.getenv("NCP_CLIENT_ID", "")
    ncp_sec = os.getenv("NCP_CLIENT_SECRET", "")
    nav_id = os.getenv("NAVER_CLIENT_ID", "")
    nav_sec = os.getenv("NAVER_CLIENT_SECRET", "")
    
    use_mock = not (bool(ncp_id and ncp_sec) or bool(nav_id and nav_sec))
    
    if use_mock:
        print("[i] API 키가 미등록되어 [데모 Mock 데이터 모드]로 심층 분석을 진행합니다.")
        df_trend = generate_mock_datalab_data(keywords, start_date, end_date, time_unit)
        search_res = generate_mock_search_results(keywords, display=display)
        raw_datalab_json = None
    else:
        print("[*] 등록된 네이버 API 키를 사용하여 실시간 데이터를 수집합니다...")
        auth_type = "ncp" if (ncp_id and ncp_sec) else "openapi"
        cid = ncp_id if auth_type == "ncp" else nav_id
        sec = ncp_sec if auth_type == "ncp" else nav_sec
        
        res_dl = get_datalab_trend(cid, sec, start_date, end_date, time_unit, keywords, auth_type=auth_type)
        df_trend = res_dl["df"] if res_dl["success"] else pd.DataFrame()
        raw_datalab_json = res_dl.get("raw")
        search_res = search_all_channels(primary_kw, cid, sec, auth_type=auth_type, display=display, sort=sort)
        
    all_items = []
    channel_dfs = {}
    for ch_name in SEARCH_ENDPOINTS_NCP.keys():
        ch_res = search_res.get(ch_name, {})
        if ch_res.get("success") and ch_res.get("data"):
            items = extract_channel_items(ch_res["data"], ch_name)
            all_items.extend(items)
            channel_dfs[ch_name] = enrich_channel_dataframe(items)
            
    df_items = pd.DataFrame(all_items)
    stats_df = compute_channel_stats(search_res)
    
    print("\n[*] 수집된 데이터를 로컬 디렉토리에 저장 중...")
    raw_path = save_raw_response(primary_kw, search_res, raw_datalab_json)
    proc_paths = save_processed_data(primary_kw, df_items, stats_df, df_trend)
    report_path = export_excel_report(primary_kw, df_items, stats_df, df_trend)
    
    print(f"  - 원본 JSON  : {raw_path}")
    print(f"  - 문서 CSV   : {proc_paths.get('items', '-')}")
    print(f"  - 통계 CSV   : {proc_paths.get('stats', '-')}")
    print(f"  - 트렌드 CSV : {proc_paths.get('trend', '-')}")
    print(f"  - 엑셀 리포트: {report_path}")
    
    print("\n" + "-" * 70)
    print("🤖 [검색 API별 AI 3줄 핵심 인사이트 요약]")
    print("-" * 70)
    for ch_name in ["뉴스", "블로그", "카페글", "웹문서", "백과사전"]:
        df_ch = channel_dfs.get(ch_name, pd.DataFrame())
        ch_tot = stats_df[stats_df["channel"] == ch_name]["total_count"].values[0] if ch_name in stats_df["channel"].values else 0
        
        top_kws = get_keyword_rank_table(df_ch, top_n=5, custom_stopwords=[primary_kw])
        top_kw_tuples = [(r["키워드"], r["출현 빈도(회)"]) for _, r in top_kws.iterrows()]
        
        ai_summary = generate_ai_channel_summary(ch_name, df_ch, ch_tot, top_kw_tuples)
        print(f"\n📌 [{ch_name}] 채널 인사이트:")
        for line in ai_summary:
            print(f"  {line}")
            
    print("\n" + "=" * 70)
    print("[+] 대시보드(http://localhost:8501)에서 5대 그래프 및 5대 통계표를 확인하세요.")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Naver Market Insight CLI Subagent")
    parser.add_argument("--keywords", "-k", type=str, default="생성형 AI, LLM, 딥러닝", help="검색어 목록")
    parser.add_argument("--start", "-s", type=str, default=None, help="시작일 (YYYY-MM-DD)")
    parser.add_argument("--end", "-e", type=str, default=None, help="종료일 (YYYY-MM-DD)")
    parser.add_argument("--days", "-d", type=int, default=90, help="최근 N일")
    parser.add_argument("--unit", "-u", type=str, default="date", choices=["date", "week", "month"], help="시간 단위")
    parser.add_argument("--display", type=int, default=50, help="채널별 수집 건수")
    parser.add_argument("--sort", type=str, default="sim", choices=["sim", "date"], help="정렬 기준")
    
    args = parser.parse_args()
    run_market_insight_pipeline(
        keywords_str=args.keywords,
        start_date=args.start,
        end_date=args.end,
        days=args.days,
        time_unit=args.unit,
        display=args.display,
        sort=args.sort
    )
