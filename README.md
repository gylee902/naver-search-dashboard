# 🔍 Naver Market Insight & Search EDA Dashboard

네이버 오픈 API(검색 API 8종 + 데이터랩 트렌드 API)를 활용하여 다중 검색어 비교, 기간별 검색어 트렌드 분석, 뉴스/블로그/웹문서/이미지/지식iN/지역/카페글/백과사전 데이터 수집 및 EDA 시각화를 제공하는 Streamlit 대시보드입니다.

---

## 🌟 주요 기능

1. **다중 검색어 트렌드 비교 (Naver DataLab)**:
   - 쉼표(`,`)로 구분된 다중 키워드(최대 5개)의 상대 검색량 트렌드 시각화
   - 기간(시작일/종료일), 시간 단위(일간/주간/월간), 기기(전체/PC/모바일), 성별 필터 지원
2. **8대 채널 통합 검색 & 점유율 분석**:
   - 뉴스, 블로그, 웹문서, 지식iN, 카페글, 지역(Local), 백과사전, 이미지
   - 채널별 총 언급량 및 비중 파이/도넛 & 바 차트
   - 채널별 상세 결과 카드 및 테이블 뷰
3. **텍스트 EDA & 연관 키워드 추출**:
   - 제목 및 요약문 대상 불용어 필터링 & 단어 빈도(N-gram) 분석
   - 주요 연관어 TOP 순위 차트 및 워드클라우드(WordCloud)
4. **데이터 Export**:
   - 트렌드 시계열 및 채널별 수집 결과 CSV / Excel 통합본 다운로드
5. **데모(Mock) 모드 탑재**:
   - 네이버 API 키가 없어도 바로 시연 및 탐색 가능

---

## 🚀 실행 방법

`uv`를 사용하여 간편하게 실행할 수 있습니다.

```bash
# 디렉토리 이동
cd naver-search-dashboard

# Streamlit 대시보드 실행
uv run streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속할 수 있습니다.

---

## 🔑 네이버 API 키 설정 (선택 사항)

실시간 네이버 API 데이터를 조회하려면 [네이버 개발자 센터](https://developers.naver.com/)에서 애플리케이션 등록 후 키를 발급받으세요.
1. 대시보드 사이드바에서 `Client ID`와 `Client Secret`을 직접 입력하거나,
2. `.env` 파일에 아래와 같이 설정할 수 있습니다.

```env
NAVER_CLIENT_ID=your_client_id_here
NAVER_CLIENT_SECRET=your_client_secret_here
```
