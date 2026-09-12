"""Data Storage & Local File Manager Module"""
import os
import json
import datetime
import pandas as pd
from typing import Dict, Any, List, Optional

RAW_DATA_DIR = os.path.join("data", "raw")
PROCESSED_DATA_DIR = os.path.join("data", "processed")
OUTPUT_REPORTS_DIR = os.path.join("output", "reports")

def ensure_directories():
    """데이터 및 출력 폴더 존재 확인 및 자동 생성"""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_REPORTS_DIR, exist_ok=True)

def save_raw_response(query: str, search_results: Dict[str, Any], datalab_raw: Optional[Dict[str, Any]] = None) -> str:
    """원본 수집 응답 JSON 파일 저장 (data/raw/)"""
    ensure_directories()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(c for c in query if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    filename = f"raw_{safe_query}_{timestamp}.json"
    filepath = os.path.join(RAW_DATA_DIR, filename)
    
    payload = {
        "timestamp": timestamp,
        "query": query,
        "search_results": search_results,
        "datalab_raw": datalab_raw
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        
    return filepath

def save_processed_data(query: str, df_items: pd.DataFrame, df_stats: pd.DataFrame, df_datalab: pd.DataFrame) -> Dict[str, str]:
    """정제된 데이터셋 CSV 파일 저장 (data/processed/)"""
    ensure_directories()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(c for c in query if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    
    saved_paths = {}
    
    if not df_items.empty:
        items_path = os.path.join(PROCESSED_DATA_DIR, f"items_{safe_query}_{timestamp}.csv")
        df_items.to_csv(items_path, index=False, encoding="utf-8-sig")
        saved_paths["items"] = items_path
        
    if not df_stats.empty:
        stats_path = os.path.join(PROCESSED_DATA_DIR, f"stats_{safe_query}_{timestamp}.csv")
        df_stats.to_csv(stats_path, index=False, encoding="utf-8-sig")
        saved_paths["stats"] = stats_path
        
    if not df_datalab.empty:
        trend_path = os.path.join(PROCESSED_DATA_DIR, f"trend_{safe_query}_{timestamp}.csv")
        df_datalab.to_csv(trend_path, index=False, encoding="utf-8-sig")
        saved_paths["trend"] = trend_path
        
    return saved_paths

def export_excel_report(query: str, df_items: pd.DataFrame, df_stats: pd.DataFrame, df_datalab: pd.DataFrame) -> str:
    """통합 분석 리포트 Excel 파일 생성 (output/reports/)"""
    ensure_directories()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(c for c in query if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    report_path = os.path.join(OUTPUT_REPORTS_DIR, f"report_{safe_query}_{timestamp}.xlsx")
    
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        if not df_items.empty:
            df_items.to_excel(writer, index=False, sheet_name="수집문서상세")
        if not df_stats.empty:
            df_stats.to_excel(writer, index=False, sheet_name="채널별통계")
        if not df_datalab.empty:
            df_datalab.to_excel(writer, index=False, sheet_name="데이터랩트렌드")
            
    return report_path
