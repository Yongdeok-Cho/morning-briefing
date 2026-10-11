"""
Morning Briefing — 뷰어 (Streamlit)
· 공개: 시황 · CMP 동향 · 뉴스 · 논문 · 공부 자료
· 비공개(비밀번호): Lab Table 연구 아이디어 · 노트 · 직접 생성 버튼
· 매일 자동 발행은 GitHub Actions가 pipeline.py 로 수행 (.github/workflows/daily.yml)
"""
import hmac
import json
from datetime import datetime

import streamlit as st

import briefing_ui as ui
import pipeline as pl
import store

st.set_page_config(page_title="Morning Briefing", page_icon="◆", layout="wide", initial_sidebar_state="expanded")


def render(s: str):
    """들여쓰기·빈 줄 제거 + $ 이스케이프 (Streamlit 마크다운의 코드블록·수식 오인 방지)"""
    s = " ".join(line.strip() for line in s.splitlines() if line.strip())
    st.markdown(s.replace("$", "&#36;"), unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def fonts_ready():
    try:
        store.sync_fonts(pl.BASE / "static")  # 비공개 저장소의 폰트를 서버에 한 번만 내려받음
    except Exception:
        pass
    return True


fonts_ready()
render(ui.css(ui.kopub_faces(pl.BASE / "static")))


@st.cache_data(ttl=7 * 86400, show_spinner=False)
def logos():
    return {name: pl.logo_uri(name, dom) for name, _, _, dom in pl.COMPANIES}


@st.cache_data(ttl=300, show_spinner=False)
def note_dates():
    return {n[:-3] for n in store.listdir("notes") if n.endswith(".md")}


# ════════════════════════════════════════════════════════════════
#  어떤 날을 볼지 · 잠금 상태
# ════════════════════════════════════════════════════════════════
now = datetime.now(pl.KST)
today = now.strftime("%Y-%m-%d")
view = st.query_params.get("d", today)
is_today = view == today
edition = pl.load_edition(view)

password = store.cfg("APP_PASSWORD")
# 비밀번호가 설정되지 않았으면 항상 잠김 (공개 홈페이지에서 실수로 열리지 않도록)
unlocked = bool(password) and st.session_state.get("unlocked", False)

# ════════════════════════════════════════════════════════════════
#  사이드바: 아카이브 · 비공개 접근 · 설정
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    entries = pl.list_editions()
    if unlocked:
        marks = note_dates()
        for e in entries:
            e["has_note"] = e["date"] in marks
    render(ui.archive_nav(entries, view))

    with st.expander("Private Access", expanded=False):
        if not password:
            st.caption("비밀번호가 아직 설정되지 않았습니다. Streamlit 앱 Settings → Secrets에 APP_PASSWORD를 추가하세요.")
        elif unlocked:
            render('<div class="lock-state">◆ Unlocked</div>')
            if store.mode() != "github":
                st.caption("⚠ 비공개 저장소가 연결되지 않아 노트가 영구 저장되지 않습니다. Secrets의 GH_PRIVATE_REPO, GH_TOKEN_PRIVATE를 확인하세요.")
            if st.button("Lock"):
                st.session_state["unlocked"] = False
                st.rerun()
        else:
            pw = st.text_input("Password", type="password", key="pw")
            if pw:
                if hmac.compare_digest(pw, password):
                    st.session_state["unlocked"] = True
                    st.rerun()
                else:
                    st.caption("비밀번호가 맞지 않습니다.")

    regen = False
    if unlocked:
        with st.expander("Settings"):
            api_key = st.text_input("Gemini API Key", value=store.cfg("GEMINI_API_KEY"), type="password")
            model_name = st.text_input("Model", value=store.cfg("GEMINI_MODEL") or "gemini-3.8-flash")
            focus = st.text_area("연구 초점 (브레인스토밍 주제)", value=store.cfg("RESEARCH_FOCUS"), height=80)
            names = [t[0] for t in pl.SYLLABUS]
            theme_name = st.selectbox("오늘의 공부 주제", names, index=names.index(pl.theme_for(now)[0]))
            regen = st.button("Regenerate Today") if (is_today and edition) else False

# ════════════════════════════════════════════════════════════════
#  본문
# ════════════════════════════════════════════════════════════════
shown_date = datetime.strptime(view, "%Y-%m-%d").replace(tzinfo=pl.KST) if edition else now
render(ui.masthead(shown_date, shown_date.timetuple().tm_yday, store.cfg("DEDICATION") or "CMP Slurry R&D"))
render(ui.viewing_banner(view, is_today))

go_btn = False
if not edition:
    if is_today:
        render('<div class="prelude"><div class="orn">◆ ◆ ◆</div><p>오늘 호는 매일 아침 6시 무렵 발행됩니다.</p></div>')
        if unlocked:
            _, mid, _ = st.columns([1.4, 1, 1.4])
            with mid:
                go_btn = st.button("Generate Now")
    else:
        render('<div class="prelude"><p>이 날짜에는 발행된 호가 없습니다.</p></div>')

if go_btn or regen:
    if not api_key:
        st.error("Settings에 Gemini API 키를 입력해 주세요.")
    else:
        theme = next(t for t in pl.SYLLABUS if t[0] == theme_name)
        status = st.empty()
        try:
            with st.spinner("오늘의 호를 편집하고 있습니다 …"):
                pl.build_edition(api_key, model_name, focus or None, theme,
                                 log=lambda m: status.markdown(f"<div class='notices'><span>· {m}</span></div>", unsafe_allow_html=True))
            st.rerun()
        except Exception as e:
            st.error(f"편집 중 문제가 발생했습니다: {e}")

if edition:
    data, rows = edition["data"], edition.get("rows", [])
    news = data.get("news", [])
    lg = logos()

    render(ui.section("I", "The Global Market", "세계 반도체 시황"))
    if rows:
        render(ui.ticker(rows, lg))
    render(ui.market(data.get("market_insight", {}), rows, lg, shown_date))

    render(ui.section("II", "Advanced CMP Technology", "첨단 CMP 기술 동향 · 업계 니즈"))
    render(ui.pulse(data.get("industry_needs"), news))
    for i, t in enumerate(data.get("cmp_tech", [])):
        render(ui.tech_article(i, t, news))

    render(ui.section("III", "Nanoparticle Research", "주목할 연구 · OpenAlex 검색"))
    tocs, papers = edition.get("tocs", []), data.get("papers", [])
    if not papers:
        render('<div class="empty">오늘 조건에 맞는 실제 논문을 찾지 못해 비워 둡니다.</div>')
    for i, p in enumerate(papers):
        render(ui.paper_article(i, p, tocs[i] if i < len(tocs) else None))

    # ── IV. 비공개 구역 ──
    render(ui.section("IV", "The Lab Table", "연구 방향 브레인스토밍 · 비공개"))
    if not unlocked:
        render(ui.locked_panel())
    else:
        raw = store.read(f"ideas/{view}.json")
        brainstorm = json.loads(raw) if raw else data.get("brainstorm", {})
        if brainstorm:
            render(ui.lab_table(brainstorm))
        else:
            render('<div class="empty">이 날의 아이디어 기록이 없습니다.</div>')

        note_path = f"notes/{view}.md"
        memo = st.text_area(f"My Notes · {view.replace('-', '.')}의 생각", value=store.read(note_path) or "",
                            height=220, placeholder="떠오른 가설, 반론, 해볼 실험을 적어 두세요.", key=f"memo-{view}")
        _, c2 = st.columns([3, 1])
        with c2:
            if st.button("Save Notes"):
                try:
                    store.write(note_path, memo, f"note {view}")
                    note_dates.clear()
                    st.toast(f"{view} 노트를 저장했습니다")
                except Exception as e:
                    st.error(str(e))

    render(ui.section("V", "The Daily Study", "오늘의 공부 · 논문과 특허"))
    render(ui.daily_study(data.get("study", {}), edition.get("day", 1), edition.get("total_days", len(pl.SYLLABUS))))

    render(ui.colophon(shown_date.timetuple().tm_yday, shown_date))
    render(ui.notices(edition.get("notices")))
