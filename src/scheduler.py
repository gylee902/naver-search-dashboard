"""
Background Periodic Monitoring & Alert Scheduler Module
Runs data collection at defined intervals and dumps summary reports automatically.
"""
import os
import sys
import time
import argparse
import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent_cli import run_market_insight_pipeline

load_dotenv(override=True)

def run_scheduler(keywords: str, interval_minutes: int = 60, iterations: int = 5):
    print("=" * 70)
    print(f"⏰ [Naver Market Scheduler] {interval_minutes}분 주기로 자동 수집 및 모니터링 시작 (총 {iterations}회)")
    print("=" * 70)
    
    for i in range(1, iterations + 1):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n🚀 [{i}/{iterations}회차 실행] 타임스탬프: {now_str}")
        try:
            run_market_insight_pipeline(keywords_str=keywords, days=30, display=30)
            print(f"✅ [{i}회차] 정상 수집 및 보고서 저장 완료.")
        except Exception as e:
            print(f"❌ [{i}회차] 수집 중 오류 발생: {e}")
            
        if i < iterations:
            print(f"⏳ 다음 실행까지 {interval_minutes}분 동안 대기합니다...")
            time.sleep(interval_minutes * 60)
            
    print("\n🏁 [Naver Market Scheduler] 모든 모니터링 스케줄이 완료되었습니다.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Naver Market Periodic Scheduler")
    parser.add_argument("--keywords", "-k", type=str, default="생성형 AI, LLM", help="모니터링 검색어")
    parser.add_argument("--interval", "-i", type=int, default=60, help="수집 간격 (분)")
    parser.add_argument("--count", "-c", type=int, default=3, help="총 실행 횟수")
    args = parser.parse_args()
    
    run_scheduler(args.keywords, args.interval, args.count)
