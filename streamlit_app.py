import streamlit as st
import pandas as pd
import os
from PIL import Image

# 데이터 디렉토리 설정
# 로컬 실행 시 "data" 폴더에 모든 .xlsx 파일이 있다고 가정합니다.
DATA_DIR = "data" 

# 파일 분류 (이미 앞선 코드에서 정의되었으므로 그대로 사용)
hitter_files = [f for f in os.listdir(DATA_DIR) if f.startswith("2025_타자") and f.endswith(".xlsx")]
pitcher_files = [f for f in os.listdir(DATA_DIR) if f.startswith("2025_투수") and f.endswith(".xlsx")]

# 선수 이름 추출 함수: 항상 첫 번째 열에서 이름을 가져옴
@st.cache_data
def extract_names_from_first_column(file_list):
    names = set()
    for file in file_list:
        try:
            # 엑셀 파일을 읽을 때 항상 첫 번째 시트를 사용한다고 가정합니다.
            # .xlsx 파일을 업로드하셨으나 .csv 파일로 변환되었으므로 .xlsx로 가정하고 코드를 작성합니다.
            df = pd.read_excel(os.path.join(DATA_DIR, file), engine="openpyxl") 
            if not df.empty:
                # 첫 번째 열 이름을 가져옵니다. (ex: '선수명', '이름' 등)
                first_col = df.columns[0]
                names.update(df[first_col].dropna().astype(str).unique())
        except Exception as e:
            # 파일 로드 오류가 발생하면 건너뛰고 메시지를 출력합니다.
            print(f"파일 오류: {file} -> {e}")
    return sorted(names)

# --- 1. 전체 선수 목록 미리 로드 (캐싱) ---
# 투수와 타자 모든 파일을 분석하여 포지션별 선수 목록을 미리 생성합니다.
@st.cache_resource
def load_all_player_lists():
    # 파일명 리스트가 비어있을 경우를 대비해 빈 리스트를 반환합니다.
    hitter_names = extract_names_from_first_column(hitter_files) if hitter_files else []
    pitcher_names = extract_names_from_first_column(pitcher_files) if pitcher_files else []
    return hitter_names, pitcher_names

# 포지션별 전체 선수 목록 로드
all_hitter_names, all_pitcher_names = load_all_player_lists()

# --- 사이드바 구성 ---
st.sidebar.title("분석 조건 설정")

# 포지션 선택 (필수)
# key를 설정하여 나중에 포지션 변경 시 다른 위젯을 초기화할 수 있게 합니다.
position = st.sidebar.radio("선택", ["투수", "타자"], index=0, key='position_radio')

# --- 2. 포지션에 따라 검색 대상 선수 목록 설정 ---
# 사용자가 선택한 포지션에 해당하는 선수 목록을 준비합니다.
if position == "타자":
    current_player_list = all_hitter_names
else: # '투수'
    current_player_list = all_pitcher_names

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
st.title("⚾ KBO 데이터 분석 시각화") # 제목 변경

# 선수 이름 검색창
# key를 설정하여 포지션이 바뀔 때 검색창도 초기화되도록 합니다.
search_input = st.text_input("선수 이름 검색", "", key='search_input')

# --- 3. 검색 로직 개선: 입력값이 선수 이름에 포함되어 있는지 확인 ---
# 검색어는 소문자로 변환하여 대소문자 구분 없이 검색되도록 합니다.
search_term = search_input.strip().lower()

if search_term:
    # 현재 포지션의 선수 목록에서 검색어가 포함된 선수만 필터링
    filtered_players = [name for name in current_player_list if search_term in name.lower()]
else:
    # 검색어가 없으면 현재 포지션의 전체 선수 목록을 사용
    filtered_players = current_player_list

# 선수 선택박스 항상 노출
if filtered_players:
    # 검색된 선수 목록이 많을 경우를 대비하여 st.selectbox 사용
    selected_player = st.selectbox("선수 선택", filtered_players)
    st.success(f"선택된 선수: **{position}** - **{selected_player}**")
else:
    st.warning(f"'{search_input}'이 포함된 {position} 선수가 없습니다.")

# --- 예시 이미지 출력 ---
if 'selected_player' in locals() and selected_player:
    try:
        # 이 부분은 파일 이름 규칙에 맞게 실제 파일 경로로 수정해 주셔야 합니다.
        # 예시로 'data' 폴더에 '선수사진_예시.png'가 있다고 가정합니다.
        image_path = "data/선수사진_예시.png" 
        image = Image.open(image_path)
        st.image(image, caption=f"{selected_player} 선수", width=200)
    except FileNotFoundError:
        st.info("선수 사진이 준비되지 않았습니다. 파일 경로를 확인해 주세요.")
    except Exception as e:
        st.error(f"사진 로드 중 오류 발생: {e}")

# --- 시각화 영역 (임시) ---
st.subheader("📊 스탯 시각화")
st.info("선수와 조건을 선택하면 여기에 **실제 데이터 기반 그래프**가 나타납니다.")
