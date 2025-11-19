import os
import streamlit as st
import pandas as pd

# ----------------- 설정 -----------------
st.set_page_config(
    page_title="2025 시즌 스탯 시각화",
    layout="wide",
)

# 중요! 여기를 수정해야 검색이 정상 작동함
BASE_DIR = "."   # 기존 data → 현재 폴더로 변경


HITTER_FILES = [
    "2025_타자_1~3회.xlsx",
    "2025_타자_3~4월.xlsx",
    "2025_타자_4~6회.xlsx",
    "2025_타자_5월.xlsx",
    "2025_타자_6월.xlsx",
    "2025_타자_7월.xlsx",
    "2025_타자_7회이후.xlsx",
    "2025_타자_8월.xlsx",
    "2025_타자_9월이후.xlsx",
    "2025_타자_주자득점권.xlsx",
    "2025_타자_주자없음.xlsx",
    "2025_타자_주자있음.xlsx",
    "2025_타자_최종성적1.xlsx",
    "2025_타자_최종성적2.xlsx",
]

PITCHER_FILES = [
    "2025_투수_1~3회.xlsx",
    "2025_투수_3~4월.xlsx",
    "2025_투수_4~6회.xlsx",
    "2025_투수_5월.xlsx",
    "2025_투수_6월.xlsx",
    "2025_투수_7월.xlsx",
    "2025_투수_7회이후.xlsx",
    "2025_투수_8월.xlsx",
    "2025_투수_9월이후.xlsx",
    "2025_투수_주자득점권.xlsx",
    "2025_투수_주자없음.xlsx",
    "2025_투수_주자있음.xlsx",
    "2025_투수_최종성적1.xlsx",
    "2025_투수_최종성적2.xlsx",
    "2025_투수_최종성적3.xlsx",
    "2025_투수_최종성적4.xlsx",
]

ALL_FILES = HITTER_FILES + PITCHER_FILES

# ----------------- 선수 이름 불러오기 -----------------
@st.cache_data
def load_all_player_names(base_dir: str):
    names = set()

    for fname in ALL_FILES:
        path = os.path.join(base_dir, fname)
        if not os.path.exists(path):
            continue

        df = pd.read_excel(path)
        col0 = df.iloc[:, 0].dropna().astype(str)
        cleaned = col0.map(lambda x: x.strip())
        names.update(cleaned.tolist())

    return sorted(names)

ALL_PLAYERS = load_all_player_names(BASE_DIR)

# ----------------- 사이드바 UI -----------------
st.sidebar.title("설정")

position = st.sidebar.radio("선수 포지션", ["투수", "타자"], index=0)

detail_options = ["세부사항 없음", "주자 있음", "주자 없음", "이닝별", "월별"]
detail = st.sidebar.radio("세부사항", detail_options)

month_selection = None
inning_selection = None

if detail == "월별":
    month_selection = st.sidebar.select_slider(
        "월 선택",
        options=["3~4월", "5월", "6월", "7월", "8월", "9이후"],
        value="3~4월",
    )
elif detail == "이닝별":
    inning_selection = st.sidebar.select_slider(
        "이닝 선택",
        options=["1~3이닝", "4~6이닝", "7이후"],
        value="1~3이닝",
    )

# ----------------- 메인 -----------------
title_text = st.text_input("제목", value="2025")

st.markdown("---")

search_query = st.text_input(
    "선수 이름 검색",
    placeholder="예: 구, 구자, 구자욱",
)

matched_players = []
selected_player = None

if search_query:
    matched_players = [name for name in ALL_PLAYERS if search_query in name]

    if matched_players:
        selected_player = st.selectbox(
            "검색 결과",
            matched_players,
        )
    else:
        st.info("검색 결과 없음")

