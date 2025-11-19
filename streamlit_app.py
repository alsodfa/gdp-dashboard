import streamlit as st
import pandas as pd
import os
from PIL import Image

# 데이터 디렉토리 설정
DATA_DIR = "data"  # 로컬 실행 시에는 "./data" 또는 절대 경로로 변경 필요

# 파일 분류
hitter_files = [f for f in os.listdir(DATA_DIR) if f.startswith("2025_타자") and f.endswith(".xlsx")]
pitcher_files = [f for f in os.listdir(DATA_DIR) if f.startswith("2025_투수") and f.endswith(".xlsx")]

# 선수 이름 추출 함수: 항상 첫 번째 열에서 이름을 가져옴
@st.cache_data
def extract_names_from_first_column(file_list):
    names = set()
    for file in file_list:
        try:
            df = pd.read_excel(os.path.join(DATA_DIR, file), engine="openpyxl")
            if not df.empty:
                first_col = df.columns[0]
                names.update(df[first_col].dropna().astype(str).unique())
        except Exception as e:
            print(f"파일 오류: {file} -> {e}")
    return sorted(names)

# --- 사이드바 구성 ---
st.sidebar.title("분석 조건 설정")

# 포지션 선택 (필수)
position = st.sidebar.radio("선택", ["투수", "타자"], index=0)

# 포지션에 따라 선수 이름 불러오기
if position == "타자":
    player_list = extract_names_from_first_column(hitter_files)
else:
    player_list = extract_names_from_first_column(pitcher_files)

# 세부사항 단일 선택
detail_options = ["세부사항없음", "주자 있음", "주자 없음", "이닝별", "월별"]
detail = st.sidebar.radio("세부사항 (하나만 선택)", detail_options, index=0)

# 월별 또는 이닝별 세부 선택
month_selection = None
inning_selection = None

if detail == "월별":
    month_selection = st.sidebar.select_slider(
        "월 선택", options=["3~4월", "5월", "6월", "7월", "8월", "9월이후"], value="3~4월"
    )
elif detail == "이닝별":
    inning_selection = st.sidebar.select_slider(
        "이닝 선택", options=["1~3이닝", "4~6이닝", "7이닝 이후"], value="1~3이닝"
    )

# --- 메인 화면 ---
st.title("제목 입력")

# 선수 이름 검색창
search_input = st.text_input("선수 이름 검색", "")

# 입력값이 있으면 필터링, 없으면 전체 출력
if search_input:
    filtered_players = [name for name in player_list if search_input in name]
else:
    filtered_players = player_list

# 선수 선택박스 항상 노출
if filtered_players:
    selected_player = st.selectbox("선수 선택", filtered_players)
    st.success(f"선택된 선수: {selected_player}")
else:
    st.warning("해당하는 이름의 선수가 없습니다.")

# --- 예시 이미지 출력 (선택된 경우) ---
if 'selected_player' in locals():
    try:
        image = Image.open("data/선수사진_예시.png")  # 파일명 조건에 맞게 수정 필요
        st.image(image, caption=f"{selected_player} 선수", width=200)
    except:
        st.info("선수 사진이 준비되지 않았습니다.")

# --- 시각화 영역 (임시) ---
st.subheader("스탯 시각화")
st.info("선수와 조건을 선택하면 여기에 그래프가 나타납니다.")
