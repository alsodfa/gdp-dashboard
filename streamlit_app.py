import streamlit as st
import pandas as pd
import os
from PIL import Image

# 데이터 디렉토리 설정
DATA_DIR = "data" 

# --- 파일 리스트 생성 ---
try:
    all_files = os.listdir(DATA_DIR)
except FileNotFoundError:
    st.error(f"'{DATA_DIR}' 폴더를 찾을 수 없습니다. 폴더와 파일 경로를 확인해 주세요.")
    all_files = []

# ⭐ CSV 파일을 찾도록 확장자 변경
hitter_files = [f for f in all_files if f.startswith("2025_타자") and f.endswith(".csv")]
pitcher_files = [f for f in all_files if f.startswith("2025_투수") and f.endswith(".csv")]


# --- 선수 이름 추출 함수: CSV 로드 및 첫 번째 열 (인덱스 0) 강제 참조 ---
@st.cache_data
def extract_names_from_first_column(file_list):
    names = set()
    first_file_col_name = None 
    
    for file in file_list:
        try:
            # ⭐⭐⭐ 핵심 수정: pd.read_csv 사용 ⭐⭐⭐
            # 첫 번째 열이 이름이 없으므로, sep=','와 encoding='euc-kr' (한글)을 사용
            df = pd.read_csv(os.path.join(DATA_DIR, file), encoding='euc-kr') 
            
            if not df.empty:
                # ⭐⭐⭐ 인덱스 0의 컬럼을 무조건 선수명으로 간주 ⭐⭐⭐
                target_col = df.columns[0]
                
                # 첫 번째 파일의 실제 로드된 열 이름을 기록합니다. (디버그용)
                if first_file_col_name is None:
                    first_file_col_name = target_col
                    
                # 선수 이름 문자열에서 공백 제거 (.str.strip())
                player_names_series = df[target_col].dropna().astype(str).str.strip()
                names.update(player_names_series.unique())
            
        except UnicodeDecodeError:
            # 인코딩 오류 발생 시 utf-8로 재시도
            try:
                df = pd.read_csv(os.path.join(DATA_DIR, file), encoding='utf-8')
                if not df.empty:
                    target_col = df.columns[0]
                    if first_file_col_name is None:
                        first_file_col_name = target_col
                    player_names_series = df[target_col].dropna().astype(str).str.strip()
                    names.update(player_names_series.unique())
            except Exception as e:
                print(f"파일 로드 오류 (UTF-8): {file} -> {e}")
                
        except Exception as e:
            print(f"파일 로드 오류: {file} -> {e}")
            
    return sorted(names), first_file_col_name

# --- 전체 선수 목록 미리 로드 (캐싱) ---
@st.cache_resource
def load_all_player_lists():
    # 반환 값 분리: (이름 목록, 첫 파일 컬럼 이름)
    hitter_names, hitter_col_name = extract_names_from_first_column(hitter_files)
    pitcher_names, pitcher_col_name = extract_names_from_first_column(pitcher_files)
    
    return hitter_names, all_pitcher_names, hitter_col_name, pitcher_col_name

# 포지션별 전체 선수 목록 로드
all_hitter_names, all_pitcher_names, hitter_col_name, pitcher_col_name = load_all_player_lists()

# --- (이후 사이드바 및 메인 화면 코드는 이전과 동일) ---

# --- 사이드바 구성 ---
st.sidebar.title("분석 조건 설정")
position = st.sidebar.radio("선택", ["투수", "타자"], index=0, key='position_radio')

if position == "타자":
    current_player_list = all_hitter_names
    current_col_name = hitter_col_name
else: # '투수'
    current_player_list = all_pitcher_names
    current_col_name = pitcher_col_name

detail_options = ["세부사항없음", "주자 있음", "주자 없음", "이닝별", "월별"]
detail = st.sidebar.radio("세부사항 (하나만 선택)", detail_options, index=0)

if detail == "월별":
    st.sidebar.select_slider(
        "월 선택", options=["3~4월", "5월", "6월", "7월", "8월", "9월이후"], value="3~4월"
    )
elif detail == "이닝별":
    st.sidebar.select_slider(
        "이닝 선택", options=["1~3이닝", "4~6이닝", "7이닝 이후"], value="1~3이닝"
    )

# --- 메인 화면 ---
st.title("⚾ KBO 데이터 분석 시각화") 
search_input = st.text_input("선수 이름 검색창", "", key='search_input')

# --- 검색 로직 ---
search_term = search_input.strip().lower()

if search_term:
    filtered_players = [name for name in current_player_list if search_term in name.lower()]
else:
    filtered_players = current_player_list

# 5. 선수 선택박스 및 결과 표시
selected_player = None
if filtered_players:
    selected_player = st.selectbox("선수 선택", filtered_players)
    st.success(f"선택된 선수: **{position}** - **{selected_player}**")
else:
    st.warning(f"'{search_input}'이 포함된 {position} 선수가 없습니다. (현재 로드된 {position} 선수: {len(current_player_list)}명)")

# --- ⭐⭐ 디버그 정보 표시 ⭐⭐
st.markdown("---")
st.subheader("🛠️ 디버그 정보 (검색 문제 확인용)")
st.info(f"선택된 **{position}** 포지션의 파일에서\n첫 번째 열 이름으로 로드된 값: **'{current_col_name}'**\n\n- 이 값이 **'선수명'**이나 **`''`** (빈 문자열)이 될 수 있습니다.\n- 코드는 이 값을 무시하고 **첫 번째 열 (인덱스 0)**에서 선수를 추출했습니다.")
st.markdown("---")

# --- (이후 이미지 출력 및 시각화 영역은 생략) ---
if selected_player:
    try:
        image_path = "data/선수사진_예시.png" 
        image = Image.open(image_path)
        st.image(image, caption=f"{selected_player} 선수", width=200)
    except FileNotFoundError:
        st.info("선수 사진 파일이 없습니다.")
    except Exception as e:
        st.error(f"사진 로드 중 오류 발생: {e}")

st.subheader("📊 스탯 시각화")
st.markdown(
    """
    <div style='border: 2px solid blue; padding: 100px; text-align: center; font-size: 20px; margin-top: 20px;'>
        **선택된 조건에 맞는 데이터 시각화 차트 영역**
    </div>
    """, 
    unsafe_allow_html=True
)
