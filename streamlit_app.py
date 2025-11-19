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
        "requirements.txt에 `openpyxl>=3.1.2`를 추가하거나 로컬이면 `pip install openpyxl`을 실행하세요.\n\n"
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
    return list(dict.fromkeys(found))

HITTER_PATHS = resolve_existing_paths(HITTER_FILES)
PITCHER_PATHS = resolve_existing_paths(PITCHER_FILES)

# ============== 유틸 ==============
def read_xlsx(path):
    return pd.read_excel(path, engine="openpyxl")

def first_col_strip(df):
    return df.iloc[:, 0].dropna().astype(str).map(lambda x: x.strip())

def normalize_colname(s: str) -> str:
    return str(s).strip().lower()

def get_col(df, candidates):
    cols = list(df.columns)
    norm_cols = [normalize_colname(c) for c in cols]
    for cand in candidates:
        target = normalize_colname(cand)
        for orig, norm in zip(cols, norm_cols):
            if target in norm:
                return orig
    return None

def parse_number(x):
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

def value_from_any(dfs, candidates, row_masks):
    for df, m in zip(dfs, row_masks):
        if df is None or m is None or not m.any():
            continue
        col = get_col(df, candidates)
        if col:
            try:
                return parse_number(df.loc[m].iloc[0][col])
            except Exception:
                continue
    return None

# ============== 공통: 차트 / 표 유틸 ==============
def bar_with_labels(data, x_field, y_field, y_fmt, height=350):
    base = alt.Chart(data).encode(
        x=alt.X(f"{x_field}:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(f"{y_field}:Q", title=None),
        tooltip=[x_field, alt.Tooltip(f"{y_field}:Q", format=y_fmt)],
    )
    bars = base.mark_bar()
    labels = base.mark_text(dy=-5).encode(text=alt.Text(f"{y_field}:Q", format=y_fmt))
    return (bars + labels).properties(height=height).interactive()

def horizontal_row_from_df(df: pd.DataFrame, k_col="지표", v_col="값", is_rate=False):
    row = {}
    for _, r in df.iterrows():
        if is_rate:
            val = 0.000 if pd.isna(r[v_col]) else round(float(r[v_col]), 3)
        else:
            val = 0 if pd.isna(r[v_col]) else int(round(r[v_col]))
        row[str(r[k_col])] = val
    return pd.DataFrame([row])

# ============== 선수명 로딩 ==============
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

position = st.sidebar.radio("선수 포지션", ["투수", "타자"], index=1)
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
query = st.text_input("선수 이름 검색창", placeholder="예: 구, 구자, 구자욱 / 포지션에 맞게 검색됩니다")
matched_players, selected_player = [], None
if query:
    q = query.strip()
    matched_players = [n for n in ACTIVE_PLAYERS if q in n]
    if matched_players:
        selected_player = st.selectbox("검색 결과에서 선수 선택", matched_players)

st.markdown("---")
st.subheader("스탯 시각화")

# ==================== 타자 (세부사항 없음 + 월별 타율 추이) ====================
def visualize_batter_overall(player_name: str):
    f1 = next((p for p in HITTER_PATHS if p.endswith("타자_최종성적1.xlsx")), None)
    f2 = next((p for p in HITTER_PATHS if p.endswith("타자_최종성적2.xlsx")), None)
    if not f1 or not f2:
        st.error("타자 최종성적 파일(1,2)을 찾을 수 없습니다.")
        return

    df1 = read_xlsx(f1); df2 = read_xlsx(f2)
    m1 = first_col_strip(df1) == player_name
    m2 = first_col_strip(df2) == player_name
    if not m1.any() and not m2.any():
        st.info("선택한 선수를 최종성적 파일에서 찾지 못했습니다.")
        return

    ab   = value_from_any([df1],[ "타수"],[m1])
    r    = value_from_any([df1],[ "득점"],[m1])
    h    = value_from_any([df1],[ "안타"],[m1])
    hr   = value_from_any([df1],[ "홈런"],[m1])
    rbi  = value_from_any([df1],[ "타점"],[m1])
    avg  = value_from_any([df1],[ "타율"],[m1])

    bb   = value_from_any([df2],[ "볼넷"],[m2]) or 0
    ibb  = value_from_any([df2],[ "고의4구","고의 사구","고의4"],[m2]) or 0
    hbp  = value_from_any([df2],[ "몸에맞는볼","사구"],[m2]) or 0
    so   = value_from_any([df2],[ "삼진"],[m2])
    gidp = value_from_any([df2],[ "병살","병살타"],[m2])
    slg  = value_from_any([df2],[ "장타율"],[m2])
    obp  = value_from_any([df2],[ "출루율"],[m2])
    ops  = value_from_any([df2],[ "ops","OPS","OPS(출+장)","ops(출+장)"],[m2])
    risp = value_from_any([df2],[ "득점권","득점권 타율","득점권타율"],[m2])

    bb_sum = (bb or 0) + (ibb or 0) + (hbp or 0)

    counting_df = pd.DataFrame([{"지표": k, "값": v if v is not None else 0} for k, v in {
        "타수":ab,"득점":r,"안타":h,"홈런":hr,"타점":rbi,"볼넷":bb_sum,"삼진":so,"병살타":gidp
    }.items()])
    rate_df = pd.DataFrame([{"지표": k, "값": v if v is not None else 0} for k, v in {
        "타율":avg,"출루율":obp,"장타율":slg,"OPS(출+장)":ops,"득점권 타율":risp
    }.items()])

    c1,c2=st.columns(2)
    with c1:
        st.markdown(f"#### {player_name} — 카운팅 스탯")
        st.altair_chart(bar_with_labels(counting_df, "지표", "값", ",.0f", height=350), use_container_width=True)
        st.caption("카운팅 스탯 (가로형)")
        st.dataframe(horizontal_row_from_df(counting_df, is_rate=False), use_container_width=True, hide_index=True)

    with c2:
        st.markdown(f"#### {player_name} — 비율/율/OPS")
        chart = bar_with_labels(rate_df, "지표", "값", ".3f", height=350).encode(
            y=alt.Y("값:Q", title=None, scale=alt.Scale(domain=[0,2]))
        )
        st.altair_chart(chart, use_container_width=True)
        st.caption("비율/OPS (가로형)")
        st.dataframe(horizontal_row_from_df(rate_df, is_rate=True), use_container_width=True, hide_index=True)

def visualize_batter_monthly_avg(player_name: str):
    month_defs = [
        ("타자_3~4월.xlsx","3~4월"),("타자_5월.xlsx","5월"),("타자_6월.xlsx","6월"),
        ("타자_7월.xlsx","7월"),("타자_8월.xlsx","8월"),("타자_9월이후.xlsx","9월이후"),
    ]
    rows=[]
    for fname,label in month_defs:
        p = next((x for x in HITTER_PATHS if x.endswith(fname)), None)
        if not p: continue
        df = read_xlsx(p)
        m = first_col_strip(df)==player_name
        if m.any():
            c = get_col(df,["타율"])
            val = parse_number(df.loc[m].iloc[0][c]) if c else None
            rows.append({"월":label,"타율":val})
    if not rows:
        st.info("월별 타율 데이터를 찾지 못했습니다."); return
    trend_df = pd.DataFrame(rows)
    order=[x[1] for x in month_defs]
    trend_df["월"]=pd.Categorical(trend_df["월"],categories=order,ordered=True)
    trend_df=trend_df.sort_values("월")
    st.markdown("#### 월별 추이 — 타율")
    st.altair_chart(
        alt.Chart(trend_df).mark_line(point=True).encode(
            x=alt.X("월:N", sort=order, axis=alt.Axis(labelAngle=0), title=None),
            y=alt.Y("타율:Q", title=None, scale=alt.Scale(domain=[0,1])),
            tooltip=[alt.Tooltip("월:N"), alt.Tooltip("타율:Q", format=".3f")]
        ).properties(height=320).interactive()
    , use_container_width=True)

# ==================== 투수 · 세부사항 없음 ====================
def visualize_pitcher_overall(player_name: str):
    paths = {
        "p1": next((p for p in PITCHER_PATHS if p.endswith("투수_최종성적1.xlsx")), None),
        "p2": next((p for p in PITCHER_PATHS if p.endswith("투수_최종성적2.xlsx")), None),
        "p3": next((p for p in PITCHER_PATHS if p.endswith("투수_최종성적3.xlsx")), None),
        "p4": next((p for p in PITCHER_PATHS if p.endswith("투수_최종성적4.xlsx")), None),
    }
    if not any(paths.values()):
        st.error("투수 최종성적 파일(1~4) 중 최소 1개 이상을 찾을 수 없습니다.")
        return

    dfs = {k: (read_xlsx(v) if v else None) for k,v in paths.items()}
    masks = {k: (first_col_strip(df)==player_name if df is not None else None) for k,df in dfs.items()}

    era   = value_from_any(dfs.values(), ["평균자책","평균자책점","era","평자"], masks.values())
    w     = value_from_any(dfs.values(), ["승","승리","W"], masks.values())
    l     = value_from_any(dfs.values(), ["패","패배","L"], masks.values())
    sv    = value_from_any(dfs.values(), ["세이브","SV","Save"], masks.values())
    hld   = value_from_any(dfs.values(), ["홀드","HLD","HD","Hold"], masks.values())
    ip    = value_from_any(dfs.values(), ["이닝","IP"], masks.values())
    qs    = value_from_any(dfs.values(), ["퀄리티스타트","QS"], masks.values())

    top_cols = st.columns(6)
    with top_cols[0]: st.metric("평균자책점", "N/A" if era is None else f"{era:.2f}")
    with top_cols[1]: st.metric("승리", "N/A" if w   is None else f"{int(round(w))}")
    with top_cols[2]: st.metric("패배", "N/A" if l   is None else f"{int(round(l))}")
    with top_cols[3]: st.metric("세이브", "N/A" if sv is None else f"{int(round(sv))}")
    with top_cols[4]: st.metric("홀드", "N/A" if hld is None else f"{int(round(hld))}")
    with top_cols[5]: st.metric("이닝", "N/A" if ip  is None else f"{ip:.1f}")
    if qs is not None:
        st.metric("퀄리티스타트", f"{int(round(qs))}")

    h_allowed = value_from_any(dfs.values(), ["피안타","피 h","h_allowed","피H"], masks.values())
    hr_allowed= value_from_any(dfs.values(), ["피홈런","피 hr","hr_allowed","피HR"], masks.values())
    bb       = value_from_any(dfs.values(), ["볼넷","bb","Base on Balls"], masks.values()) or 0
    hbp      = value_from_any(dfs.values(), ["몸에맞는볼","사구","hbp"], masks.values()) or 0
    so       = value_from_any(dfs.values(), ["삼진","so","k"], masks.values())

    bb_sum = (bb or 0) + (hbp or 0)

    counting_df = pd.DataFrame([
        {"지표":"피안타","값": h_allowed or 0},
        {"지표":"피홈런","값": hr_allowed or 0},
        {"지표":"볼넷","값": bb_sum or 0},
        {"지표":"삼진","값": so or 0},
    ])
    st.markdown("#### 카운팅 스탯 (투수)")
    st.altair_chart(bar_with_labels(counting_df, "지표", "값", ",.0f", height=340), use_container_width=True)
    st.caption("카운팅 스탯 (가로형)")
    st.dataframe(horizontal_row_from_df(counting_df, is_rate=False), use_container_width=True, hide_index=True)

    whip = value_from_any(dfs.values(), ["이닝당출루허용률","whip"], masks.values())
    k9   = value_from_any(dfs.values(), ["9이닝당 삼진","9이닝당삼진","k/9","k9","so/9","삼진/9","탈삼진/9","탈삼진9"], masks.values())
    bb9  = value_from_any(dfs.values(), ["9이닝당볼넷","9이닝당 볼넷","bb/9","bb9","볼넷/9"], masks.values())
    kbb  = value_from_any(dfs.values(), ["삼진/볼넷","k/bb","kbb"], masks.values())
    o_ops= value_from_any(dfs.values(), ["피ops","피 ops","o-ops","ops"], masks.values())
    o_avg= value_from_any(dfs.values(), ["피안타율","피타율","oavg","avg","OAVG","BAA"], masks.values())

    rate_df = pd.DataFrame([
        {"지표":"이닝당출루허용률", "값": whip or 0},
        {"지표":"9이닝당 삼진", "값": k9 or 0},
        {"지표":"9이닝당 볼넷", "값": bb9 or 0},
        {"지표":"삼진/볼넷", "값": kbb or 0},
        {"지표":"피OPS", "값": o_ops or 0},
        {"지표":"피안타율", "값": o_avg or 0},
    ])
    st.markdown("#### 비율 지표 (투수)")
    st.altair_chart(bar_with_labels(rate_df, "지표", "값", ".3f", height=340), use_container_width=True)
    st.caption("비율 지표 (가로형)")
    st.dataframe(horizontal_row_from_df(rate_df, is_rate=True), use_container_width=True, hide_index=True)

    # 월별 피안타율
    month_defs = [
        ("투수_3~4월.xlsx","3~4월"),
        ("투수_5월.xlsx","5월"),
        ("투수_6월.xlsx","6월"),
        ("투수_7월.xlsx","7월"),
        ("투수_8월.xlsx","8월"),
        ("투수_9월이후.xlsx","9월이후"),
    ]
    rows=[]
    for fname,label in month_defs:
        p = next((x for x in PITCHER_PATHS if x.endswith(fname)), None)
        if not p: continue
        df = read_xlsx(p)
        m  = first_col_strip(df)==player_name
        if m.any():
            oavg_col = get_col(df, ["피안타율","피타율","oavg","OAVG","BAA","AVG"])
            val = parse_number(df.loc[m].iloc[0][oavg_col]) if oavg_col else None
            rows.append({"월":label,"피안타율":val})

    if rows:
        trend_df = pd.DataFrame(rows)
        order=[x[1] for x in month_defs]
        trend_df["월"]=pd.Categorical(trend_df["월"],categories=order,ordered=True)
        trend_df=trend_df.sort_values("월")

        st.markdown("#### 월별 추이 — 피안타율")
        st.altair_chart(
            alt.Chart(trend_df).mark_line(point=True).encode(
                x=alt.X("월:N", sort=order, axis=alt.Axis(labelAngle=0), title=None),
                y=alt.Y("피안타율:Q", title=None, scale=alt.Scale(domain=[0,1])),
                tooltip=[alt.Tooltip("월:N"), alt.Tooltip("피안타율:Q", format=".3f")],
            ).properties(height=320).interactive()
        , use_container_width=True)

        table_row = {r["월"]: (0.000 if pd.isna(r["피안타율"]) else round(float(r["피안타율"]),3)) for _, r in trend_df.iterrows()}
        st.caption("월별 피안타율 (가로형)")
        st.dataframe(pd.DataFrame([table_row]), use_container_width=True, hide_index=True)
    else:
        st.info("월별 피안타율 데이터를 찾지 못했습니다.")

# ==================== 투수 · 주자 있음/없음 ====================
def visualize_pitcher_onbase(player_name: str, has_runner: bool):
    """주자 있음/없음: 피안타율 메트릭을 맨 위에 표시 → 그 다음 막대 그래프 + 가로형 표"""
    suffix = "투수_주자있음.xlsx" if has_runner else "투수_주자없음.xlsx"
    path = next((p for p in PITCHER_PATHS if p.endswith(suffix)), None)
    if not path:
        st.error(f"{suffix} 파일을 찾을 수 없습니다.")
        return

    df = read_xlsx(path)
    mask = first_col_strip(df) == player_name
    if not mask.any():
        st.info("선택한 선수를 해당 파일에서 찾지 못했습니다.")
        return

    h_allowed = value_from_any([df], ["피안타","피 H","H_ALLOWED","H"], [mask]) or 0
    double    = value_from_any([df], ["2루타","2B","2루"], [mask]) or 0
    triple    = value_from_any([df], ["3루타","3B","3루"], [mask]) or 0
    hr        = value_from_any([df], ["피홈런","홈런","HR"], [mask]) or 0
    bb        = value_from_any([df], ["볼넷","BB"], [mask]) or 0
    hbp       = value_from_any([df], ["몸에맞는볼","사구","HBP"], [mask]) or 0
    so        = value_from_any([df], ["삼진","SO","K"], [mask]) or 0
    oavg      = value_from_any([df], ["피안타율","피타율","OAVG","BAA","AVG"], [mask])

    # ✅ 피안타율 메트릭을 맨 위로
    title = "주자 있음" if has_runner else "주자 없음"
    st.markdown(f"#### {player_name} — {title}")
    st.metric(f"{title} — 피안타율", "N/A" if oavg is None else f"{oavg:.3f}")

    # 막대그래프
    bb_sum = (bb or 0) + (hbp or 0)
    bar_df = pd.DataFrame([
        {"지표":"피안타", "값": h_allowed},
        {"지표":"2루타", "값": double},
        {"지표":"3루타", "값": triple},
        {"지표":"홈런",  "값": hr},
        {"지표":"볼넷",  "값": bb_sum},
        {"지표":"삼진",  "값": so},
    ])
    st.altair_chart(bar_with_labels(bar_df, "지표", "값", ",.0f", height=340), use_container_width=True)

    # 가로형 표
    st.caption(f"{title} — 카운팅 스탯 (가로형)")
    st.dataframe(horizontal_row_from_df(bar_df, is_rate=False), use_container_width=True, hide_index=True)

# ===================== 호출 분기 =====================
if position == "타자" and selected_player:
    if detail == "세부사항 없음":
        visualize_batter_overall(selected_player)
        visualize_batter_monthly_avg(selected_player)
    else:
        st.info("타자 주자/이닝/월별 시각화는 앞서 만든 함수로 동작합니다.")
elif position == "투수" and selected_player:
    if detail == "세부사항 없음":
        visualize_pitcher_overall(selected_player)
    elif detail == "주자 있음":
        visualize_pitcher_onbase(selected_player, has_runner=True)
    elif detail == "주자 없음":
        visualize_pitcher_onbase(selected_player, has_runner=False)
    else:
        st.info("투수의 이닝별/월별 등은 이어서 확장 가능합니다.")
elif not selected_player:
    st.info("상단 검색창에 일부 이름을 입력해 선수를 선택해 주세요. (포지션에 따라 검색 대상이 달라집니다.)")
