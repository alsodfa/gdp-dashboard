import os
from glob import glob
import streamlit as st
import pandas as pd

# ----------------- 기본 설정 -----------------
st.set_page_config(page_title="2025 시즌 스탯 시각화", layout="wide")

# openpyxl 의존성 체크
try:
    import openpyxl  # noqa: F401
except Exception as e:
    st.error(
        "엑셀 파일(xlsx)을 읽으려면 openpyxl이 필요합니다.\n"
        "requirements.txt에 `openpyxl>=3.1.2` 추가 후 재배포하거나, 로컬이면 `pip install openpyxl`을 실행하세요.\n\n"
        f"원본 에러: {e}"
    )
    st.stop()

# ----------------- 파일 정의 -----------------
# 레포 구조: 루트와 ./data 모두 지원
APP_DIR = os.path.dirname(os.path.abspath(__file__))
SEARCH_DIRS = [APP_DIR, os.path.join(APP_DIR, "data")]

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

def resolve_existing_paths(filenames):
    """정의된 파일명들을 레포 루트/ data 폴더에서 찾아 실제 경로 리스트로 반환"""
    found = []
    for name in filenames:
        path = None
        # 우선순위: 루트 -> data
        for d in SEARCH_DIRS:
            candidate = os.path.join(d, name)
            if os.path.exists(candidate):
                path = candidate
                break
        if path:
            found.append(path)
    # 중복 제거(같은 파일명이 루트/데이터 양쪽 있을 가능성 대비)
    return list(dict.fromkeys(found))

HITTER_PATHS = resolve_existing_paths(HITTER_FILES)
PITCHER_PATHS = resolve_existing_paths(PITCHER_FILES)

# ----------------- 선수명 수집 -----------------
@st.cache_data(show_spinner=False)
def load_player_names(file_paths):
    """
    주어진 파일들에서 1열(선수명)만 모아 중복 제거 후 정렬해 반환.
    - 공백만 strip. '(좌)', '(우)' 등 표기는 그대로 보존.
    """
    names = set()
    broken = []
    for p in file_paths:
        try:
            df = pd.read_excel(p, engine="openpyxl")
            if df.shape[1] == 0:
                continue
            # 첫 번째 열에서 이름만 추출
            col0 = df.iloc[:, 0].dropna().astype(str).map(lambda x: x.strip())
            names.update(col0.tolist())
        except Exception:
            broken.append(os.path.basename(p))
            continue
    return sorted(names), broken

HITTER_PLAYERS, BROKEN_H = load_player_names(tuple(HITTER_PATHS))
PITCHER_PLAYERS, BROKEN_P = load_player_names(tuple(PITCHER_PATHS))

# ----------------- 사이드바 -----------------
st.sidebar.title("설정")

# (1) 포지션
position = st.sidebar.radio("선수 포지션", ["투수", "타자"], index=0)

# (2) 세부사항
detail = st.sidebar.radio(
    "세부사항 (하나만 선택)",
    ["세부사항 없음", "주자 있음", "주자 없음", "이닝별", "월별"],
    index=0,
)

# (3) 월/이닝 바(조건부 표시)
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
# 제목 고정
st.title("2025")

# 포지션별 플레이어 목록
ACTIVE_PLAYERS = PITCHER_PLAYERS if position == "투수" else HITTER_PLAYERS

# 선수 검색
query = st.text_input("선수 이름 검색창", placeholder="예: 구, 구자, 구자욱")
matched_players = []
selected_player = None
if query:
    q = query.strip()
    # 부분 문자열 검색
    matched_players = [name for name in ACTIVE_PLAYERS if q in name]
    if matched_players:
        selected_player = st.selectbox("검색 결과에서 선수 선택", matched_players)
    else:
        st.info("검색 결과가 없습니다. (선택한 포지션의 파일 내 존재 선수만 검색됩니다)")

st.markdown("---")
st.subheader("스탯 시각화")
st.write("여기에 선택한 조건에 맞는 그래프/표를 이후 단계에서 표시할 예정입니다.")

# --- 진단/확인용 (원하면 지워도 됨) ---
with st.expander("진단 정보(필요 시만 열기)", expanded=False):
    st.write("포지션:", position)
    st.write("세부사항:", detail)
    st.write("월 선택:", month_selection)
    st.write("이닝 선택:", inning_selection)
    st.write("타자 파일 수:", len(HITTER_PATHS), "투수 파일 수:", len(PITCHER_PATHS))
    st.write("타자 선수 수:", len(HITTER_PLAYERS), "투수 선수 수:", len(PITCHER_PLAYERS))
    if BROKEN_H or BROKEN_P:
        if BROKEN_H:
            st.warning(f"읽기 실패(타자): {BROKEN_H}")
        if BROKEN_P:
            st.warning(f"읽기 실패(투수): {BROKEN_P}")
    st.write("검색어:", query)
    st.write("검색 결과 수:", len(matched_players))
    st.write("선택한 선수:", selected_player)
