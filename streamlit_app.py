import streamlit as st

def main():
    # --- 페이지 설정 ---
    st.set_page_config(layout="wide")
    
    # --- 메인 영역 제목 ---
    st.title("📊 KBO 데이터 분석 시각화") # 이미지에 있는 '제목' 부분

    # --- 사이드바 시작 (선택 영역) ---
    with st.sidebar:
        st.header("⚙️ 데이터 필터")
        
        # 1. 투수/타자 선택 (반드시 하나 선택해야 함)
        st.subheader("⚾ 포지션 선택")
        # radio를 사용하여 필수 선택 항목 구성
        position = st.radio(
            "선택하세요",
            ('투수', '타자'),
            key='position_select',
            index=0, # 기본값은 '투수'
            label_visibility="collapsed" # 레이블 숨김
        )

        st.markdown("---") # 시각적 구분선

        # 2. 세부사항 선택
        st.subheader("🔍 세부 필터")
        
        # 세부사항 옵션 정의
        detail_options = {
            '세부사항 없음': 'none',
            '주자 있음': 'runner_on',
            '주자 없음': 'runner_off',
            '이닝별': 'inning_split',
            '월별': 'month_split'
        }
        
        # 라디오 버튼으로 세부 필터 선택
        # 세부사항 없음이 기본으로 선택되어 있어야 하므로 index=0
        selected_detail_korean = st.radio(
            "선택하세요",
            list(detail_options.keys()),
            key='detail_select',
            index=0, 
            label_visibility="collapsed"
        )
        
        # 선택된 값의 키를 가져옴
        selected_detail = detail_options[selected_detail_korean]

        st.markdown("---") # 시각적 구분선

        # 3. 월별/이닝별 선택 시 조건부 위젯 표시
        
        # 월별 선택 시 (2025_타자_3~4월.xlsx 형식 참고)
        if selected_detail == 'month_split':
            st.subheader("🗓️ 월 선택")
            # 월 옵션: 3~4, 5, 6, 7, 8, 9이후 (6개 선택 가능)
            # 파일명을 보니 3~4월이 하나의 범주로 묶여있어 이를 반영
            month_options = ['3~4월', '5월', '6월', '7월', '8월', '9월이후']
            
            # 단일 선택을 위한 셀렉트 박스 또는 슬라이더를 사용할 수 있으나,
            # '바 같은 것'을 요청하셔서 슬라이더에 가장 가까운 `st.select_slider`를 사용해볼게요.
            # 하지만 6개의 명확한 옵션을 선택하는 경우에는 `st.selectbox`가 더 일반적입니다.
            # 여기서는 요청에 따라 **st.select_slider**를 사용하겠습니다.
            selected_month = st.select_slider(
                '월 범위 조절',
                options=month_options,
                value=month_options[0] # 기본값 설정
            )
            st.info(f"선택된 월: **{selected_month}**")


        # 이닝별 선택 시 (2025_투수_1~3회.xlsx 형식 참고)
        elif selected_detail == 'inning_split':
            st.subheader("⚾ 이닝 선택")
            # 이닝 옵션: 1~3회, 4~6회, 7회이후 (3개 선택 가능)
            inning_options = ['1~3회', '4~6회', '7회이후']
            
            selected_inning = st.selectbox(
                '이닝 범위 선택',
                options=inning_options,
                index=0
            )
            st.info(f"선택된 이닝: **{selected_inning}**")
            
        
    # --- 메인 영역 시각화/검색창 ---
    
    # 선수 이름 검색창
    player_name = st.text_input(
        "선수 이름 검색창", 
        placeholder="선수 이름을 입력하세요",
        label_visibility="visible"
    )
    
    # 스탯 시각화 영역 (큰 네모 부분)
    st.markdown("## 스탯 시각화")
    st.info(
        f"**선택된 필터:**\n\n"
        f"- **포지션:** {position}\n"
        f"- **세부사항:** {selected_detail_korean}\n"
        f"- **선수 이름:** {player_name if player_name else '입력 없음'}\n"
        + (f"- **월:** {selected_month}" if selected_detail == 'month_split' else '')
        + (f"- **이닝:** {selected_inning}" if selected_detail == 'inning_split' else '')
    )
    
    # 시각화 차트가 들어갈 자리
    st.markdown(
        """
        <div style='border: 2px solid blue; padding: 200px; text-align: center; font-size: 20px;'>
            **스탯 시각화 차트 영역**
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
