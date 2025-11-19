import streamlit as st
import pandas as pd
import os

DATA_DIR = "data"

# 포지션 선택 (필수)
position = st.sidebar.radio("포지션을 선택하세요", ["타자", "투수"])

# 파일 분류
hitter_files = [f for f in os.listdir(DATA_DIR) if f.startswith("2025_타자") and f.endswith(".xlsx")]
pitcher_files = [f for f in os.listdir(DATA_DIR) if f.startswith("2025_투수") and f.endswith(".xlsx")]

# 선수 이름 추출 함수 (1열 기준)
@st.cache_data
def extract_player_names_from_first_column(file_list):
    names = set()
    for file in file_list:
        df = pd.read_excel(os.path.join(DATA_DIR, file))
        if not df.empty:
            first_col = df.columns[0]
            names.update(df[first_col].dropna().astype(str).unique())
    return sorted(names)

# 포지션별 이름 추출
if position == "타자":
    player_list = extract_player_names_from_first_column(hitter_files)
else:
    player_list = extract_player_names_from_first_column(pitcher_files)

# 검색창 + 필터
search_input = st.text_input("선수 이름을 입력하세요")
if search_input:
    filtered_names = [name for name in player_list if search_input in name]
    if filtered_names:
        selected_player = st.selectbox("선수 선택", filtered_names)
        st.success(f"선택된 선수: {selected_player}")
    else:
        st.warning("해당 이름을 포함하는 선수가 없습니다.")
