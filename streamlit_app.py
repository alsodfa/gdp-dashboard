import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="야구 스탯 시각화",
    layout="wide",
)

# ----------------- 사이드바 -----------------
st.sidebar.title("설정")

# 1) 투수 / 타자 (반드시 하나 선택되는 radio)
st.sidebar.subheader("포지션")
position = st.sidebar.radio(
    "선수 포지션을 선택하세요.",
    ["투수", "타자"],
    index=0,
)

# 2) 세부사항 선택
st.sidebar.subheader("세부사항")

detail_options = ["세부사항 없음", "주자 있음", "주자 없음", "이닝별", "월별"]
detail = st.sidebar.radio(
    "세부사항을 하나 선택하세요.",
    detail_options,
    index=0,  # 기본값: 세부사항 없음
)

# 월/이닝 슬라이더용 변수 (초기값)
month_selection = None
inning_selection = None

# 세부사항에 따라 월별/이닝별 바(게이지) 보이기
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

# 제목 입력 칸
page_title = st.text_input("제목", value="2025 시즌 선수 스탯 시각화")

# 선수 이름 검색창
player_name = st.text_input("선수 이름 검색창", placeholder="선수 이름을 입력하세요.")

st.markdown("---")

# 시각화 영역(나중에 그래프/표 넣을 자리)
st.subheader("스탯 시각화")
st.write("여기에 나중에 선택한 조건에 맞는 그래프를 그릴 예정입니다.")
