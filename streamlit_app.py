import os
from glob import glob
import streamlit as st
import pandas as pd
import altair as alt

# ============== 기본 설정 ==============
st.set_page_config(page_title="2025 시즌 스탯 시각화", layout="wide")

# openpyxl 의존성 체크
try:
    import openpyxl  # noqa: F401
except Exception as e:
    st.error(
        "엑셀(xlsx) 읽기에 필요한 openpyxl이 없습니다.\n"
        "requirements.txt에 `openpyxl>=3.1.2`를 추가하거나 로컬은 `pip install openpyxl`을 실행하세요.\n\n"
        f"원본 에러: {e}"
    )
    st.stop()

# ============== 파일 경로 ==============
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
    found = []
    for name in filenames:
        for d in SEARCH_DIRS:
            p = os.path.join(d, name)
            if os.path.exists(p):
                found.append(p)
                break
    # 중복 제거
    return list(dict.fromkeys(found))

HITTER_PATHS = resolve_existing_paths(HITTER_FILES)
PITCHER_PATHS = resolve_existing_paths(PITCHER_FILES)

# ============== 유틸 ==============
def read_xlsx(path):
    return pd.read_excel(path, engine="openpyxl")

def first_col_strip(df):
    """첫 번째 열(선수명)만 공백 strip 후 반환"""
    return df.iloc[:, 0].dropna().astype(str).map(lambda x: x.strip())

def normalize_colname(s: str) -> str:
    """컬럼명 비교용 정규화(소문자, 양쪽 공백 제거)"""
    return str(s).strip().lower()

def get_col(df, candidates):
    """
    후보 문자열 리스트 중 하나라도 '부분 포함'되면 해당 컬럼명을 반환.
    - 대소문자 무시
    - 컬럼명 앞뒤 공백 무시
    """
    cols = list(df.columns)
    norm_cols = [normalize_colname(c) for c in cols]
    for cand in candidates:
        target = normalize_colname(cand)
        for orig, norm in zip(cols, norm_cols):
            if target in norm:
                return orig
    return None

def parse_number(x):
    """
    문자열 수치 안전 변환:
    - 공백 제거, 콤마 제거
    - % 포함 시 100으로 나눠 0~1/0~2 스케일 정규화(예: '85%' -> 0.85)
    - 빈칸/하이픈 등은 None
    """
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s in {"-", "—", "NaN", "nan"}:
        return None
    is_percent = "%" in s
    s = s.replace(",", "").replace("%", "")
    try:
        val = float(s)
        if is_percent:
            val = val / 100.0
        return val
    except Exception:
        return None

# ============== 선수명 로딩 (포지션별) ==============
@st.cache_data(show_spinner=False)
def load_player_names(file_paths):
    names = set()
    broken = []
    for p in file_paths:
        try:
            df = read_xlsx(p)
            names.update(first_col_strip(df).tolist())
        except Exception:
            broken.append(os.path.basename(p))
    return sorted(names), broken

HITTER_PLAYERS, BROKEN_H = load_player_names(tuple(HITTER_PATHS))
PITCHER_PLAYERS, BROKEN_P = load_player_names(tuple(PITCHER_PATHS))

# ============== 사이드바 ==============
st.sidebar.title("설정")

position = st.sidebar.radio("선수 포지션", ["투수", "타자"], index=1)  # 타자 기본
detail = st.sidebar.radio(
    "세부사항 (하나만 선택)",
    ["세부사항 없음", "주자 있음", "주자 없음", "이닝별", "월별"],
    index=0,
)

month_selection = None
inning_selection = None
if detail == "월별":
    month_selection = st.sidebar.select_slider(
        "월 선택", options=["3~4월", "5월", "6월", "7월", "8월", "9이후"], value="3~4월"
    )
elif detail == "이닝별":
    inning_selection = st.sidebar.select_slider(
        "이닝 선택", options=["1~3이닝", "4~6이닝", "7이후"], value="1~3이닝"
    )

# ============== 메인 타이틀 / 검색 ==============
st.title("2025")

ACTIVE_PLAYERS = PITCHER_PLAYERS if position == "투수" else HITTER_PLAYERS
query = st.text_input("선수 이름 검색창", placeholder="예: 구, 구자, 구자욱")
matched_players, selected_player = [], None
if query:
    q = query.strip()
    matched_players = [n for n in ACTIVE_PLAYERS if q in n]
    if matched_players:
        selected_player = st.selectbox("검색 결과에서 선수 선택", matched_players)

st.markdown("---")
st.subheader("스탯 시각화")

# ============== 타자 · 세부사항 없음: 시각화 ==============
def visualize_batter_overall(player_name: str):
    """
    타자_최종성적1/2 에서 지정 지표를 읽어
    - (비율/율/OPS) 묶음: Altair bar + interactive
    - (카운팅 스탯) 묶음: Altair bar + interactive
    - 아래 표로 원값 출력
    """
    f1 = next((p for p in HITTER_PATHS if p.endswith("타자_최종성적1.xlsx")), None)
    f2 = next((p for p in HITTER_PATHS if p.endswith("타자_최종성적2.xlsx")), None)
    if not f1 or not f2:
        st.error("타자 최종성적 파일(1,2)을 찾을 수 없습니다.")
        return

    df1 = read_xlsx(f1)
    df2 = read_xlsx(f2)

    # 선수 행 찾기(첫 열이 선수명)
    mask1 = first_col_strip(df1) == player_name
    mask2 = first_col_strip(df2) == player_name
    row1 = df1[mask1]
    row2 = df2[mask2]

    if row1.empty and row2.empty:
        st.info("선택한 선수를 최종성적 파일에서 찾지 못했습니다.")
        return

    # -------- df1에서 컬럼 찾기 --------
    c_ab   = get_col(df1, ["타수"])
    c_r    = get_col(df1, ["득점"])
    c_h    = get_col(df1, ["안타"])
    c_hr   = get_col(df1, ["홈런"])
    c_rbi  = get_col(df1, ["타점"])
    c_avg  = get_col(df1, ["타율"])

    # -------- df2에서 컬럼 찾기 --------
    c_bb   = get_col(df2, ["볼넷"])
    c_ibb  = get_col(df2, ["고의4구", "고의 사구", "고의4"])
    c_hbp  = get_col(df2, ["몸에맞는볼", "사구"])
    c_so   = get_col(df2, ["삼진"])
    c_gidp = get_col(df2, ["병살", "병살타"])
    c_slg  = get_col(df2, ["장타율"])
    c_obp  = get_col(df2, ["출루율"])
    c_ops  = get_col(df2, ["ops", "OPS", "OPS(출+장)", "ops(출+장)"])
    c_risp = get_col(df2, ["득점권", "득점권 타율", "득점권타율"])

    # 값 안전 추출 함수(문자/퍼센트 처리)
    def v(df, col):
        if col is None or df.empty:
            return None
        return parse_number(df.iloc[0][col])

    # 수치 뽑기
    ab   = v(row1, c_ab)
    r    = v(row1, c_r)
    h    = v(row1, c_h)
    hr   = v(row1, c_hr)
    rbi  = v(row1, c_rbi)
    avg  = v(row1, c_avg)

    bb   = v(row2, c_bb)  or 0.0
    ibb  = v(row2, c_ibb) or 0.0
    hbp  = v(row2, c_hbp) or 0.0
    so   = v(row2, c_so)
    gidp = v(row2, c_gidp)
    slg  = v(row2, c_slg)
    obp  = v(row2, c_obp)
    ops  = v(row2, c_ops)
    risp = v(row2, c_risp)

    # 볼넷 = 볼넷 + 고의4구 + 몸에맞는볼(=사구)
    bb_sum = (bb or 0) + (ibb or 0) + (hbp or 0)

    # 카운팅 스탯 / 비율 스탯 분리
    counting_dict = {
        "타수": ab, "득점": r, "안타": h, "홈런": hr, "타점": rbi,
        "볼넷": bb_sum, "삼진": so, "병살타": gidp
    }
    rate_dict = {
        "타율": avg, "출루율": obp, "장타율": slg, "OPS(출+장)": ops, "득점권 타율": risp
    }

    # DataFrame으로 변환
    counting_df = pd.DataFrame(
        [{"지표": k, "값": v if v is not None else 0} for k, v in counting_dict.items()]
    )
    rate_df = pd.DataFrame(
        [{"지표": k, "값": v if v is not None else 0} for k, v in rate_dict.items()]
    )

    # Altair 인터랙티브 바차트(줌/이동 가능)
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(f"#### {player_name} — 카운팅 스탯")
        chart1 = (
            alt.Chart(counting_df)
            .mark_bar()
            .encode(
                x=alt.X("지표:N", sort=None, title=None),
                y=alt.Y("값:Q", title=None),
                tooltip=["지표", alt.Tooltip("값:Q", format=",.0f")],
            )
            .properties(height=350)
            .interactive()
        )
        st.altair_chart(chart1, use_container_width=True)

    with c2:
        st.markdown(f"#### {player_name} — 비율/율/OPS")
        chart2 = (
            alt.Chart(rate_df)
            .mark_bar()
            .encode(
                x=alt.X("지표:N", sort=None, title=None),
                y=alt.Y("값:Q", title=None, scale=alt.Scale(domain=[0, 2])),
                tooltip=["지표", alt.Tooltip("값:Q", format=".3f")],
            )
            .properties(height=350)
            .interactive()
        )
        st.altair_chart(chart2, use_container_width=True)

    # 원값 표
    st.markdown("#### 원값 표")
    show_df = pd.concat(
        [
            counting_df.assign(구분="카운팅"),
            rate_df.assign(구분="비율/OPS"),
        ],
        ignore_index=True,
    )[["구분", "지표", "값"]]

    def fmt(row):
        return f"{row['값']:.0f}" if row["구분"] == "카운팅" else f"{row['값']:.3f}"
    show_df["표시값"] = show_df.apply(fmt, axis=1)
    st.dataframe(show_df, use_container_width=True, hide_index=True)

def visualize_batter_monthly_avg(player_name: str):
    """
    월별 추이(타율) 꺾은선 그래프
    사용 파일: 타자_3~4월, 5월, 6월, 7월, 8월, 9월이후
    """
    # 파일 이름 패턴과 라벨 순서
    month_defs = [
        ("타자_3~4월.xlsx", "3~4월"),
        ("타자_5월.xlsx",   "5월"),
        ("타자_6월.xlsx",   "6월"),
        ("타자_7월.xlsx",   "7월"),
        ("타자_8월.xlsx",   "8월"),
        ("타자_9월이후.xlsx", "9월이후"),
    ]

    rows = []
    for fname, label in month_defs:
        # 실제 경로 해석
        p = next((x for x in HITTER_PATHS if x.endswith(fname)), None)
        if not p or not os.path.exists(p):
            # 파일이 없으면 건너뜀 (나중에 빈 값으로 노출하지 않음)
            continue

        df = read_xlsx(p)
        mask = first_col_strip(df) == player_name
        if mask.any():
            # 타율 컬럼 찾기
            c_avg = get_col(df, ["타율"])
            val = parse_number(df.loc[mask].iloc[0][c_avg]) if c_avg else None
            rows.append({"월": label, "타율": val})

    if not rows:
        st.info("월별 타율 데이터를 찾지 못했습니다.")
        return

    trend_df = pd.DataFrame(rows)
    # 지정 순서대로 카테고리 정렬
    order = [label for _, label in month_defs]
    trend_df["월"] = pd.Categorical(trend_df["월"], categories=order, ordered=True)
    trend_df = trend_df.sort_values("월")

    st.markdown("#### 월별 추이 — 타율")
    line = (
        alt.Chart(trend_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("월:N", sort=order, title=None),
            y=alt.Y("타율:Q", title=None, scale=alt.Scale(domain=[0, 1])),
            tooltip=[alt.Tooltip("월:N"), alt.Tooltip("타율:Q", format=".3f")],
        )
        .properties(height=320)
        .interactive()
    )
    st.altair_chart(line, use_container_width=True)

# 실제 호출
if position == "타자" and selected_player and detail == "세부사항 없음":
    visualize_batter_overall(selected_player)
    visualize_batter_monthly_avg(selected_player)  # ← 월별추이(타율) 추가
elif position == "타자" and not selected_player:
    st.info("타자 데이터를 보려면 상단 검색창에서 선수를 선택하세요.")
elif position == "투수":
    st.info("투수쪽 시각화는 다음 단계에서 붙일게!")
