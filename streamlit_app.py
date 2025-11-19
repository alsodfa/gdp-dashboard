import streamlit as st
import pandas as pd
import os

# 포지션 선택 (필수)
position = st.sidebar.radio("선택", ["타자", "투수"], index=0)

# 파일 목록 불러오기
file_dir = "/mnt/data"
all_files = os.listdir(file_dir)
hitter_files = [f for f in all_files if "타자" in f and f.endswith(".xlsx")]
pitcher_files = [f for f in all_files if "투수" in f and f.endswith(".xlsx")]

# 이름 추출 함수
@st.cache_data
def get_player_names(file_list):
    names = set()
    for file in file_list:
        df = pd.read_excel(os.path.join(file_dir, file))
        name_cols = [col for col in df.columns if "이름" in col or "선수명" in col]
        if name_cols:
            col = name_cols[0]
            names.update(df[col].dropna().unique())
    return sorted(names)

# 포지션에 따라 이름 리스트 가져오기
if position == "타자":
    player_list = get_player_names(hitter_files)
else:
    player_list = get_player_names(pitcher_files)

# 선수 검색창
selected_text = st.text_input("선수 이름 검색", "")
if selected_text:
    filtered_names = [name for name in player_list if selected_text in name]
    if filtered_names:
        selected_player = st.selectbox("선수 선택", filtered_names)
    else:
        st.warning("해당 이름을 포함하는 선수가 없습니다.")
