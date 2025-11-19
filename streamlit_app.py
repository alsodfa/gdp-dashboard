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

# 엑셀 위치: 레포 루트 + ./data 둘 다 지원
APP_DIR = os.path.dirname(os.path.abspath(__file__))
SEARCH_DIRS = [
    APP_DIR,                        # 레포 루트
    os.path.join(APP_DIR, "data"),  # data 폴더
]

def find_xlsx_files():
    paths = []
    for d in SEARCH_DIRS:
        if os.path.isdir(d):
            paths += glob(os.path.join(d, "2025_*.xlsx"))
    # 중복 제거 + 정렬
    return sorted(list(dict.fromkeys(paths)))

ALL_XLSX = find_xlsx_files()

# ----------------- 선수명 수집 -----------------
@st.cache_data(show_spinner=False)
def load_all_player_names(file_paths):
    """
    xlsx들에서 1열(선수명)만 모아 중복 제거 후 정렬.
    """
    names = set()
    broken = []
    for p in file_paths:
        try:
            df = pd.read_excel(p, engine="openpyxl")
            if df.shape[1] == 0:
                continue
            col0 = df.iloc[:, 0].dropna().astype(str).map(lambda x: x.strip())
            names.update(col0.tolist())
        except Exception:
            broken.append(os.path.basename(p))
            continue
    return sorted(names), broken

ALL_PLAYERS, BROKEN = load_all_player_names(tuple(ALL_XLSX))  # 캐시 키로 tuple 사용

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
# 제목을 고정으로 표시
st.title("2025 삼성라이온즈 결산")

# 선수 검색
player_query = st.text_input("선수 이름 검색창", placeholder="예: 구, 구자, 구자욱")

matched_players = []
selected_player = None
if player_query:
    q = player_query.strip()
    matched_players = [name for name in ALL_PLAYERS if q in name]
    if matched_players:
        selected_player = st.selectbox("검색 결과에서 선수 선택", matched_players)
    else:
        st.info("검색 결과가 없습니다. (파일 내 존재 선수만 검색됩니다)")

st.markdown("---")
st.subheader("스탯 시각화")
st.write("여기에 선택한 조건에 맞는 그래프/표를 이후 단계에서 표시할 예정입니다.")

# --- 진단/확인용 (원하면 지워도 됨) ---
with st.expander("진단 정보(필요 시만 열기)", expanded=False):
    st.write("발견된 엑셀 파일 수:", len(ALL_XLSX))
    if not ALL_XLSX:
        st.warning("엑셀 파일을 찾지 못했습니다. 레포 루트 또는 data/에 '2025_*.xlsx' 형태로 두세요.")
    else:
        st.write("샘플 파일 5개:", [os.path.basename(p) for p in ALL_XLSX[:5]])
    st.write("총 선수 수:", len(ALL_PLAYERS))
    if BROKEN:
        st.warning("읽기 실패 파일:", BROKEN)
    st.write(
        {
            "포지션": position,
            "세부사항": detail,
            "월 선택": month_selection,
            "이닝 선택": inning_selection,
            "검색어": player_query,
            "검색 결과 수": len(matched_players),
            "선택한 선수": selected_player,
        }
    )
