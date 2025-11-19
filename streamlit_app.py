import os
import streamlit as st
import pandas as pd

st.set_page_config(page_title="2025 시즌 스탯 시각화", layout="wide")

# 0) 필수 라이브러리 체크
try:
    import openpyxl  # noqa: F401
except ImportError as e:
    st.error(
        "엑셀 파일(xlsx)을 읽으려면 `openpyxl`이 필요합니다.\n\n"
        "✅ 해결 방법\n"
        "1) requirements.txt에 `openpyxl>=3.1.2` 추가 후 재배포\n"
        "2) (로컬) `pip install openpyxl`\n\n"
        f"원본 에러: {e}"
    )
    st.stop()

# 1) 파일 경로 설정
#   - 앱 파일들과 엑셀이 같은 폴더에 있으면 "."이면 됩니다.
#   - 혹시 스트림릿 클라우드에서 경로가 다르면 os.getcwd() 기준으로 상대경로 확인돼요.
BASE_DIR = "."

HITTER_FILES = [
    "2025_타자_1~3회.xlsx", "2025_타자_3~4월.xlsx", "2025_타자_4~6회.xlsx",
    "2025_타자_5월.xlsx", "2025_타자_6월.xlsx", "2025_타자_7월.xlsx",
    "2025_타자_7회이후.xlsx", "2025_타자_8월.xlsx", "2025_타자_9월이후.xlsx",
    "2025_타자_주자득점권.xlsx", "2025_타자_주자없음.xlsx", "2025_타자_주자있음.xlsx",
    "2025_타자_최종성적1.xlsx", "2025_타자_최종성적2.xlsx",
]
PITCHER_FILES = [
    "2025_투수_1~3회.xlsx", "2025_투수_3~4월.xlsx", "2025_투수_4~6회.xlsx",
    "2025_투수_5월.xlsx", "2025_투수_6월.xlsx", "2025_투수_7월.xlsx",
    "2025_투수_7회이후.xlsx", "2025_투수_8월.xlsx", "2025_투수_9월이후.xlsx",
    "2025_투수_주자득점권.xlsx", "2025_투수_주자없음.xlsx", "2025_투수_주자있음.xlsx",
    "2025_투수_최종성적1.xlsx", "2025_투수_최종성적2.xlsx",
    "2025_투수_최종성적3.xlsx", "2025_투수_최종성적4.xlsx",
]
ALL_FILES = HITTER_FILES + PITCHER_FILES

# 2) 선수명 로딩
@st.cache_data
def load_all_player_names(base_dir: str):
    names = set()
    missing = []
    for fname in ALL_FILES:
        path = os.path.join(base_dir, fname)
        if not os.path.exists(path):
            missing.append(fname)
            continue
        # engine 명시 (openpyxl)
        df = pd.read_excel(path, engine="openpyxl")
        col0 = df.iloc[:, 0].dropna().astype(str).map(lambda x: x.strip())
        names.update(col0.tolist())
    return sorted(names), missing

ALL_PLAYERS, MISSING = load_all_player_names(BASE_DIR)

if MISSING:
    with st.expander("경고: 누락된 파일 목록", expanded=False):
        for m in MISSING:
            st.write("•", m)

# 3) 사이드바 (이전과 동일)
st.sidebar.title("설정")
position = st.sidebar.radio("선수 포지션", ["투수", "타자"], index=0)

detail_options = ["세부사항 없음", "주자 있음", "주자 없음", "이닝별", "월별"]
detail = st.sidebar.radio("세부사항", detail_options, index=0)

month_selection = None
inning_selection = None
if detail == "월별":
    month_selection = st.sidebar.select_slider(
        "월 선택", options=["3~4월", "5월", "6월", "7월", "8월", "9이후"], value="3~4월"
    )
elif detail == "이닝별":
    inning_selection = st.sidebar.select_slider(
        "이닝 선택", options=["1~3이닝", "4~6이닝", "7이후"], value="1~3이닝"
    )

# 4) 메인: 제목 + 검색
title_text = st.text_input("제목", value="2025")
st.markdown("---")

search_query = st.text_input("선수 이름 검색", placeholder="예: 구, 구자, 구자욱")

matched_players = []
selected_player = None
if search_query:
    matched_players = [name for name in ALL_PLAYERS if search_query in name]
    if matched_players:
        selected_player = st.selectbox("검색 결과", matched_players)
    else:
        st.info("검색 결과가 없습니다. (파일 내 존재 선수만 검색됩니다)")

# (옵션) 상태 확인
with st.expander("현재 선택 값 확인용", expanded=False):
    st.write("포지션:", position)
    st.write("세부사항:", detail)
    st.write("월 선택:", month_selection)
    st.write("이닝 선택:", inning_selection)
    st.write("검색어:", search_query)
    st.write("검색 결과 수:", len(matched_players))
    st.write("선택한 선수:", selected_player)
    st.write("총 선수 수:", len(ALL_PLAYERS))
