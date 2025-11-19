import os
import streamlit as st
import pandas as pd

# ----------------- 설정 -----------------
st.set_page_config(
    page_title="2025 시즌 스탯 시각화",
    layout="wide",
)

BASE_DIR = "data"  # 엑셀 파일들이 들어있는 폴더 이름

# 저장해 둔 30개 파일 이름들
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
    """
    모든 엑셀 파일에서 첫 번째 열(선수명)만 모아서
    중복 제거 후 정렬해서 리스트로 반환
    """
    names = set()

    for fname in ALL_FILES:
        path = os.path.join(base_dir, fname)
        if not os.path.exists(path):
            # 필요하면 나중에 st.warning으로 바꿔도 됨
            continue

        df = pd.read_excel(path)
        # 첫 번째 열에서 이름 추출
        col0 = df.iloc[:, 0].dropna().astype(str)
        # 앞뒤 공백 제거
        cleaned = col0.map(lambda x: x.strip())
        names.update(cleaned.tolist())

    # 정렬(한글도 ㄱ~ㅎ 순서대로 정렬됨)
    return sorted(names)


ALL_PLAYERS = load_all_player_names(BASE_DIR)

# ----------------- 사이드바 -----------------
st.sidebar.title("설정")

# 1) 투수 / 타자
st.sidebar.subheader("포지션")
position = st.sidebar.radio(
    "선수 포지션을 선택하세요.",
    ["투수", "타자"],
    index=0,
)

# 2) 세부사항
st.sidebar.subheader("세부사항")

detail_options = ["세부사항 없음", "주자 있음", "주자 없음", "이닝별", "월별"]
detail = st.sidebar.radio(
    "세부사항을 하나 선택하세요.",
    detail_options,
    index=0,
)

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

# ----------------- 메인 영역 -----------------

# 제목: 2025
title_text = st.text_input("제목", value="2025")

st.markdown("---")

# ---- 선수 이름 검색창 ----
search_query = st.text_input(
    "선수 이름 검색창",
    placeholder="예: 구, 구자, 구자욱 등 일부만 입력해도 검색되게",
)

matched_players = []
selected_player = None

if search_query:
    # 부분 문자열 검색 (대소문자 구분 없이 하고 싶으면 둘 다 lower() 하면 됨)
    matched_players = [name for name in ALL_PLAYERS if search_query in name]

    if matched_players:
        selected_player = st.selectbox(
            "검색 결과에서 선수 선택",
            matched_players,
        )
    else:
        st.info("검색 결과가 없습니다. (파일에 없는 이름이거나, 오타일 수 있어요)")

