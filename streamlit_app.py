import streamlit as st
import pandas as pd
import os
from PIL import Image

# 데이터 디렉토리 설정
DATA_DIR = "data" 

# 파일 분류 (로컬 환경에 data 폴더와 파일이 존재한다고 가정)
hitter_files = [f for f in os.listdir(DATA_DIR) if f.startswith("2025_타자") and f.endswith(".xlsx")]
pitcher_files = [f for f in os.listdir(DATA_DIR) if f.startswith("2025_투수") and f.endswith(".xlsx")]

# --- 선수 이름 추출 함수: '선수명' 열 명시적으로 사용 ---
@st.cache_data
def extract_names_from_first_column(file_list):
    names = set()
    # '선수명' 열이 첫 번째 열로 바뀌었다면, header=0 또는 header가 없는 상태로 로드합니다.
    # header=None을 지정하지 않으면 첫 번째 행이 자동으로 헤더로 인식됩니다.
    # 만약 '선수명'이 첫 번째 행에 있다면 header 인자는 생략합니다.
    
    # 가정: 모든 파일의 첫 번째 행/첫 번째 열에 '선수명'이 적혀있음
    COLUMN_NAME_FOR_PLAYER = '선수명' 
    
    for file in file_list:
        try:
            # header 인자 생략 (첫 행을 헤더로 사용)
            df = pd.read_excel(os.path.join(DATA_DIR, file), engine="openpyxl") 
            
            if not df.empty and COLUMN_NAME_FOR_PLAYER in df.columns:
                # 명시적으로 '선수명' 열의 데이터만 추출
                names.update(df[COLUMN_NAME_FOR_PLAYER].dropna().astype(str).unique())
            
        except Exception as e:
            # 오류 발생 시 해당 파일명을 출력하여 디버깅에 도움을 줍니다.
            print(f"파일 로드 오류: {file} -> {e}")
            
    return sorted(names)

# --- 전체 선수 목록 미리 로드 (캐싱) ---
@st.cache_resource
def load_all_player_lists():
    hitter_names = extract_names_from_first_column(hitter_files) if hitter_files else []
    pitcher_names = extract_names_from_first_column(pitcher_files) if pitcher_files else []
    return hitter_names, pitcher_names

# 포지션별 전체 선수 목록 로드
all_hitter_names, all_pitcher_names = load_all_player_lists()

# --- 사이드바 구성 ---
st.sidebar.title("분석 조건 설정")

# 포지션 선택 (필수)
position = st.sidebar.radio("선택", ["투수", "타자"], index=0, key='position_radio')

# 포지션에 따라 검색 대상 선수 목록 설정
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
st.title("⚾ KBO 데이터 분석 시각화") 

# 선수 이름 검색창
search_input = st.text_input("선수 이름 검색창", "", key='search_input')

# --- 검색 로직 (부분 일치 검색) ---
search_term = search_input.strip().lower()

if search_term:
    # 현재 포지션의 선수 목록에서 검색어가 포함된 선수만 필터링
    filtered_players = [name for name in current_player_list if search_term in name.lower()]
else:
    # 검색어가 없으면 현재 포지션의 전체 선수 목록을 사용
    filtered_players = current_player_list

# 선수 선택박스 및 결과 표시
selected_player = None
if filtered_players:
    selected_player = st.selectbox("선수 선택", filtered_players)
    st.success(f"선택된 선수: **{position}** - **{selected_player}**")
else:
    st.warning(f"'{search_input}'이 포함된 {position} 선수가 없습니다.")

# --- 예시 이미지 출력 ---
if selected_player:
    try:
        # 이 부분은 파일 이름 규칙에 맞게 실제 파일 경로로 수정해 주셔야 합니다.
        image_path = "data/선수사진_예시.png" 
        image = Image.open(image_path)
        st.image(image, caption=f"{selected_player} 선수", width=200)
    except FileNotFoundError:
        st.info("선수 사진이 준비되지 않았습니다.")
    except Exception as e:
        st.error(f"사진 로드 중 오류 발생: {e}")

# --- 시각화 영역 (임시) ---
st.subheader("📊 스탯 시각화")
st.info(f"현재 조건:\n- 포지션: **{position}**\n- 세부 필터: **{detail}**\n- 선택된 선수: **{selected_player if selected_player else '없음'}**")
