"""
Morning Briefing — 디자인 부품 모듈
모든 함수는 HTML/SVG 문자열만 돌려준다 (Streamlit 의존성 없음).
"""
import html as _html
import random
import re

# ════════════════════════════════════════════════════════════════
#  Palette
# ════════════════════════════════════════════════════════════════
INK, INK_SOFT, MUTE = "#17140F", "#4A443B", "#8C8475"
PAPER, PAPER_DEEP, RULE = "#F4EFE5", "#EAE3D3", "#CFC5B2"
GOLD = "#A3864F"
UP, DOWN = "#8A2A1F", "#2B4A5C"

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


# ════════════════════════════════════════════════════════════════
#  Text helpers
# ════════════════════════════════════════════════════════════════
def esc(s) -> str:
    return _html.escape(str(s if s is not None else ""))


def md(s) -> str:
    """**굵게**, ==밑줄== 마크업을 HTML로 변환 (나머지는 이스케이프)"""
    t = esc(s)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"==(.+?)==", r"<u>\1</u>", t)
    return t.replace("\n", "<br>")


def plain(s) -> str:
    return re.sub(r"\*\*|==", "", str(s or ""))


def clip(s, n):
    s = plain(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def wrap(t, n):
    words, lines, cur = plain(t).split(), [], ""
    for w in words:
        if cur and len(cur) + len(w) + 1 > n:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


# ════════════════════════════════════════════════════════════════
#  KoPubWorld 폰트 (한글 글자에만 적용)
# ════════════════════════════════════════════════════════════════
HANGUL = "U+1100-11FF, U+3000-303F, U+3130-318F, U+A960-A97F, U+AC00-D7AF, U+D7B0-D7FF, U+FF00-FFEF"
_FMT = {".woff2": "woff2", ".woff": "woff", ".otf": "opentype", ".ttf": "truetype"}


def kopub_faces(font_dir, url_prefix="app/static/"):
    """font_dir 안의 KoPubWorld 바탕/돋움 파일을 찾아 @font-face 생성 (파일명은 원본 그대로 OK)"""
    from pathlib import Path
    files = [f for f in Path(font_dir).glob("*") if f.suffix.lower() in _FMT] if Path(font_dir).exists() else []
    faces = []
    for fam, css_name in (("batang", "KoPubBatang"), ("dotum", "KoPubDotum")):
        # 바탕: 본문(300)=Light, 보통(400)=Medium, 제목·강조(500~700)=Bold  /  돋움: 라벨용
        weights = (("light", "100 300"), ("medium", "400"), ("bold", "500 900")) if fam == "batang" else \
                  (("light", "100 300"), ("medium", "400 500"), ("bold", "600 900"))
        for label, weight in weights:
            hit = next((f for f in files if "kopub" in f.name.lower() and fam in f.name.lower() and label in f.name.lower()), None)
            if hit:
                faces.append(f"@font-face {{ font-family:'{css_name}'; font-weight:{weight}; font-display:swap; "
                             f"src:url('{url_prefix}{hit.name}') format('{_FMT[hit.suffix.lower()]}'); unicode-range:{HANGUL}; }}")
    return "\n".join(faces)


# ════════════════════════════════════════════════════════════════
#  Stylesheet
# ════════════════════════════════════════════════════════════════
_GRAIN = ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'>"
          "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/>"
          "<feColorMatrix values='0 0 0 0 0.09 0 0 0 0 0.08 0 0 0 0 0.06 0 0 0 0.055 0'/></filter>"
          "<rect width='100%' height='100%' filter='url(%23n)'/></svg>\")")


def css(font_faces: str = "") -> str:
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400;1,500&family=Noto+Serif+KR:wght@300;400;500;600;700&family=Jost:wght@300;400;500&display=swap');
{font_faces}
:root {{
  --ink:{INK}; --ink-soft:{INK_SOFT}; --mute:{MUTE}; --paper:{PAPER}; --paper-deep:{PAPER_DEEP};
  --rule:{RULE}; --gold:{GOLD}; --up:{UP}; --down:{DOWN};
  --display:'Cormorant Garamond','KoPubBatang','Noto Serif KR','Noto Serif CJK KR',serif;
  --body:'KoPubBatang','Noto Serif KR','Noto Serif CJK KR','Cormorant Garamond',serif;
  --label:'Jost','KoPubDotum','Noto Sans CJK KR',sans-serif;
}}
.stApp, body.preview {{ font-synthesis-style:none; background-color:var(--paper); background-image:{_GRAIN}; color:var(--ink); font-family:var(--body); }}
[data-testid="stHeader"] {{ background:transparent; }}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display:none !important; }}
.block-container {{ max-width:1160px; padding:2.6rem 3rem 5rem; }}
::selection {{ background:var(--gold); color:var(--paper); }}

/* Streamlit widgets */
[data-testid="stSidebar"] {{ background:var(--paper-deep); border-right:1px solid var(--rule); }}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea, [data-testid="stSidebar"] button, [data-testid="stSidebar"] summary {{ font-family:var(--label); letter-spacing:.03em; }}
[data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea {{ background:var(--paper) !important; border-radius:0 !important; }}
.stButton > button {{ background:var(--ink); color:var(--paper); border:1px solid var(--ink); border-radius:0;
  font-family:var(--label); font-weight:400; font-size:.76rem; letter-spacing:.32em; text-transform:uppercase;
  padding:1rem 2.4rem; width:100%; transition:all .5s ease; }}
.stButton > button:hover {{ background:transparent; color:var(--ink); border-color:var(--gold); }}
.stButton > button:focus {{ box-shadow:none; color:var(--paper); }}
.stButton > button p {{ font-family:var(--label); }}
[data-testid="stSpinner"] p {{ font-family:var(--display); font-style:italic; font-size:1.15rem; color:var(--ink-soft); }}
.stTextArea textarea {{ background:rgba(255,255,255,.35) !important; border:1px solid var(--rule) !important; border-radius:0 !important;
  font-family:var(--body) !important; font-size:.98rem !important; line-height:1.9 !important; color:var(--ink) !important;
  background-image:repeating-linear-gradient(transparent, transparent 1.85rem, rgba(163,134,79,.18) 1.85rem, rgba(163,134,79,.18) calc(1.85rem + 1px)) !important; }}
.stTextArea label p {{ font-family:var(--label) !important; font-size:.62rem !important; letter-spacing:.3em; text-transform:uppercase; color:var(--gold) !important; }}

/* Shared atoms */
.kicker {{ font-family:var(--label); font-size:.62rem; font-weight:400; letter-spacing:.32em; text-transform:uppercase; color:var(--gold); }}
.rule {{ height:1px; background:var(--ink); }}
.rule-double {{ border-top:1px solid var(--ink); border-bottom:1px solid var(--ink); height:5px; }}
.prose {{ font-family:var(--body); font-weight:300; font-size:1rem; line-height:1.95; color:var(--ink-soft); word-break:keep-all; }}
.prose b {{ font-weight:600; color:var(--ink); }}
.prose u {{ color:var(--ink); }}
.stApp u, body.preview u {{ text-decoration:none; color:inherit; background-image:linear-gradient(var(--gold),var(--gold));
  background-size:100% 1.5px; background-repeat:no-repeat; background-position:0 96%; padding-bottom:2px;
  -webkit-box-decoration-break:clone; box-decoration-break:clone; }}
.badge {{ display:inline-block; font-family:var(--label); font-size:.56rem; letter-spacing:.2em; text-transform:uppercase;
  padding:.28rem .6rem .24rem; border:1px solid var(--rule); color:var(--mute); vertical-align:middle; }}
.badge.ok {{ border-color:var(--gold); color:var(--gold); }}
.badge.solid {{ background:var(--ink); border-color:var(--ink); color:var(--paper); }}
.link {{ font-family:var(--label); font-size:.62rem; letter-spacing:.24em; text-transform:uppercase; color:var(--ink) !important;
  text-decoration:none !important; border-bottom:1px solid var(--gold); padding-bottom:2px; }}
.link:hover {{ color:var(--gold) !important; }}

/* Masthead */
.mast {{ text-align:center; margin-bottom:1rem; }}
.mast-meta {{ display:flex; justify-content:space-between; font-family:var(--label); font-size:.66rem; letter-spacing:.28em;
  text-transform:uppercase; color:var(--ink-soft); padding-bottom:.9rem; }}
.mast-title {{ font-family:var(--display); font-weight:300; font-size:clamp(3.2rem,8.5vw,7.4rem); line-height:.95;
  letter-spacing:-.015em; color:var(--ink); margin:2.2rem 0 .6rem; padding:0; }}
.mast-title em {{ font-style:italic; font-weight:300; color:var(--gold); }}
.mast-sub {{ font-family:var(--display); font-style:italic; font-size:1.35rem; color:var(--ink-soft); margin-bottom:2rem; }}
.mast-ded {{ font-family:var(--label); font-size:.64rem; letter-spacing:.34em; text-transform:uppercase; color:var(--mute); margin-top:1rem; }}
.mast-ded b {{ color:var(--gold); font-weight:400; }}
.contents {{ display:flex; justify-content:center; flex-wrap:wrap; gap:.4rem 2.2rem; margin:2rem 0 3rem; }}
.contents span {{ font-family:var(--display); font-size:1.05rem; color:var(--ink-soft); }}
.contents i {{ color:var(--gold); margin-right:.45rem; }}
.prelude {{ text-align:center; max-width:520px; margin:3rem auto 2.4rem; }}
.prelude .orn {{ color:var(--gold); font-size:.9rem; letter-spacing:1.2em; }}
.prelude p {{ font-family:var(--display); font-style:italic; font-size:1.3rem; line-height:1.6; color:var(--ink-soft); margin:1.2rem 0 0; }}

/* Section header */
.sec {{ display:flex; align-items:baseline; gap:1.6rem; margin:4.8rem 0 2.2rem; padding-bottom:1rem; border-bottom:1px solid var(--rule); }}
.sec-num {{ font-family:var(--display); font-style:italic; font-weight:300; font-size:3.4rem; line-height:1; color:var(--gold); min-width:3.6rem; }}
.sec-title {{ font-family:var(--display); font-weight:400; font-size:2.05rem; color:var(--ink); line-height:1.1; }}
.sec-ko {{ font-family:var(--label); font-size:.64rem; letter-spacing:.3em; color:var(--mute); margin-top:.45rem; }}

/* Logo */
.logo {{ display:flex; align-items:center; height:30px; }}
.logo img {{ max-height:26px; max-width:84px; width:auto; object-fit:contain; filter:grayscale(1) contrast(1.08); opacity:.82;
  mix-blend-mode:multiply; transition:filter .5s, opacity .5s; }}
.logo:hover img, .tk:hover .logo img {{ filter:none; opacity:1; }}
.logo .mono {{ font-family:var(--display); font-weight:600; font-size:.98rem; letter-spacing:.04em; white-space:nowrap; color:var(--ink); }}

/* Ticker */
.ticker {{ display:grid; grid-template-columns:repeat(6,1fr); border-top:1px solid var(--ink); border-bottom:1px solid var(--ink); }}
.tk {{ padding:1.2rem 1.1rem 1.15rem; border-right:1px solid var(--rule); }}
.tk:last-child {{ border-right:none; }}
.tk-head {{ display:flex; align-items:center; justify-content:space-between; gap:.5rem; }}
.tk-head .logo {{ height:22px; }} .tk-head .logo img {{ max-height:18px; max-width:56px; }}
.tk-name {{ font-family:var(--label); font-size:.56rem; letter-spacing:.22em; text-transform:uppercase; color:var(--mute); }}
.tk-px {{ font-family:var(--display); font-size:1.8rem; font-weight:400; margin:.5rem 0 .1rem; font-variant-numeric:lining-nums tabular-nums; }}
.tk-chg {{ font-family:var(--label); font-size:.76rem; letter-spacing:.06em; }}
.up {{ color:var(--up); }} .down {{ color:var(--down); }}
.tk-cap {{ font-family:var(--display); font-style:italic; font-size:.95rem; color:var(--mute); margin-top:.3rem; }}

/* Market: insight + movers */
.market {{ display:grid; grid-template-columns:1.08fr 1fr; grid-template-rows:auto auto; column-gap:4rem; row-gap:0; margin-top:2.8rem; }}
.m-head {{ grid-column:1; grid-row:1; }} .m-cap {{ grid-column:2; grid-row:1; align-self:end; }}
.m-body {{ grid-column:1; grid-row:2; border-top:1px solid var(--ink); }} .m-chart {{ grid-column:2; grid-row:2; border-top:1px solid var(--ink); }}
.ins-head {{ font-family:var(--display); font-weight:400; font-style:italic; font-size:1.95rem; line-height:1.3; color:var(--ink);
  margin:1rem 0 1.3rem; padding:0; word-break:keep-all; }}
.ins-list {{ list-style:none; margin:0; padding:0; }}
.ins-list li {{ display:grid; grid-template-columns:2.6rem 1fr; padding:1rem 0; border-bottom:1px solid var(--rule); margin:0; }}
.ins-list .n {{ font-family:var(--display); font-style:italic; font-size:1.25rem; color:var(--gold); line-height:1.6; }}
.sig {{ font-family:var(--label); font-size:.6rem; letter-spacing:.28em; text-transform:uppercase; color:var(--mute); margin-top:1.2rem; }}
.chart-cap {{ font-family:var(--label); font-size:.6rem; letter-spacing:.28em; text-transform:uppercase; color:var(--mute);
  padding-bottom:.8rem; display:flex; justify-content:space-between; }}
.movers {{ position:relative; }}
.mv-row {{ display:grid; grid-template-columns:104px 1fr; align-items:center; height:62px; border-bottom:1px solid rgba(207,197,178,.55); }}
.mv-id .code {{ font-family:var(--label); font-size:.52rem; letter-spacing:.22em; color:var(--mute); margin-top:.2rem; }}
.mv-track {{ display:grid; grid-template-columns:1fr 1px 1fr; align-items:center; height:100%; }}
.mv-axis {{ background:var(--ink); height:100%; }}
.mv-half {{ display:flex; align-items:center; gap:.55rem; height:100%; }}
.mv-half.neg {{ justify-content:flex-end; }}
.bar {{ display:block; height:20px; flex:none; }}
.bar.up {{ background:linear-gradient(180deg,#B5574A 0%,#8A2A1F 48%,#661B13 100%); border-radius:0 2px 2px 0;
  box-shadow:0 5px 10px -3px rgba(102,27,19,.45), inset 0 1px 0 rgba(255,255,255,.28), inset 0 -2px 0 rgba(0,0,0,.18); }}
.bar.down {{ background:linear-gradient(180deg,#56788B 0%,#2B4A5C 48%,#1A3140 100%); border-radius:2px 0 0 2px;
  box-shadow:0 5px 10px -3px rgba(26,49,64,.45), inset 0 1px 0 rgba(255,255,255,.25), inset 0 -2px 0 rgba(0,0,0,.2); }}
.mv-val {{ font-family:var(--display); font-size:1.05rem; font-weight:500; font-variant-numeric:lining-nums tabular-nums; white-space:nowrap; }}
.mv-scale {{ display:grid; grid-template-columns:104px 1fr; padding-top:.5rem; }}
.mv-scale div {{ display:flex; justify-content:space-between; font-family:var(--label); font-size:.56rem; letter-spacing:.14em; color:var(--mute); }}

/* Points (개조식) */
.points {{ list-style:none; margin:0; padding:0; }}
.points li {{ display:grid; grid-template-columns:5rem 1fr; gap:1rem; padding:.85rem 0; border-top:1px solid var(--rule); margin:0; }}
.points li:last-child {{ border-bottom:1px solid var(--rule); }}
.pt-k {{ font-family:var(--label); font-size:.6rem; letter-spacing:.22em; text-transform:uppercase; color:var(--gold); padding-top:.5rem; }}
.figs {{ display:flex; flex-wrap:wrap; gap:1.2rem 2.6rem; margin-top:1.8rem; }}
.fig-v {{ font-family:var(--display); font-weight:400; font-size:2.3rem; line-height:1; color:var(--ink); font-variant-numeric:lining-nums; }}
.fig-l {{ font-family:var(--label); font-size:.56rem; letter-spacing:.22em; text-transform:uppercase; color:var(--mute); margin-top:.45rem; }}

/* Tech article */
.article {{ display:grid; grid-template-columns:1.12fr 1fr; gap:3.6rem; padding:2.8rem 0; border-bottom:1px solid var(--rule); align-items:start; }}
.article.rev > .col-text {{ order:2; }} .article.rev > figure {{ order:1; }}
.art-no {{ margin-bottom:1rem; }}
.art-title {{ font-family:var(--display); font-weight:500; font-size:2.05rem; line-height:1.2; color:var(--ink); margin:0 0 1rem; padding:0; word-break:keep-all; }}
.lede {{ font-family:var(--display); font-style:italic; font-size:1.22rem; line-height:1.55; color:var(--ink-soft); margin:0 0 1.5rem; word-break:keep-all; }}
.plate {{ margin:0; }}
.plate-box {{ background:var(--paper-deep); padding:.9rem; }}
.plate-frame {{ border:1px solid rgba(163,134,79,.55); outline:1px solid rgba(163,134,79,.22); outline-offset:-6px; padding:1.1rem .9rem .7rem; background:rgba(244,239,229,.55); }}
.plate-frame svg {{ display:block; width:100%; height:auto; }}
.plate-title {{ font-family:var(--display); font-style:italic; font-size:1.02rem; color:var(--gold); text-align:center; margin-bottom:.4rem; }}
.plate figcaption b, .toc figcaption b {{ font-weight:600; color:var(--ink-soft); }}
.plate figcaption, .toc figcaption {{ font-family:var(--display); font-style:italic; font-size:.98rem; color:var(--mute); margin-top:.75rem; line-height:1.5; word-break:keep-all; }}
.fig-no {{ font-style:normal; font-family:var(--label); font-weight:400; font-size:.58rem; letter-spacing:.24em; color:var(--gold); margin-right:.5rem; }}

/* Paper */
.paper {{ padding:2.8rem 0; border-bottom:1px solid var(--rule); }}
.paper-meta {{ display:flex; flex-wrap:wrap; align-items:center; gap:.6rem 1.1rem; margin-bottom:1.1rem; }}
.paper-meta .jr {{ font-family:var(--label); font-size:.68rem; letter-spacing:.24em; text-transform:uppercase; color:var(--ink); }}
.paper-meta .yr {{ font-family:var(--display); font-size:1.15rem; color:var(--gold); }}
.paper-meta .if {{ font-family:var(--label); font-size:.6rem; letter-spacing:.18em; color:var(--mute); }}
.corr {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:.3rem .8rem; margin:.2rem 0 1.8rem; }}
.corr .lbl {{ font-family:var(--label); font-size:.56rem; letter-spacing:.24em; text-transform:uppercase; color:var(--gold); }}
.corr .nm {{ font-family:var(--display); font-weight:600; font-size:1.25rem; color:var(--ink); }}
.corr .af {{ font-family:var(--display); font-style:italic; font-size:1.08rem; color:var(--ink-soft); }}
.corr .co {{ font-family:var(--display); font-style:italic; font-size:1rem; color:var(--mute); }}
.toc {{ margin:0 0 2rem; }}
.toc-box {{ background:var(--paper-deep); padding:.9rem; }}
.toc-box .inner {{ border:1px solid rgba(163,134,79,.5); padding:1rem; background:rgba(244,239,229,.6); text-align:center; }}
.toc-box img {{ max-width:100%; max-height:380px; mix-blend-mode:multiply; }}
.toc-box svg {{ display:block; width:100%; height:auto; }}
.paper-body {{ display:grid; grid-template-columns:1.6fr 1fr; gap:3.4rem; align-items:start; }}
.paper-aside {{ border-left:1px solid var(--rule); padding-left:2rem; }}
.paper-aside .figs {{ margin-top:.4rem; flex-direction:column; gap:1.4rem; }}
.paper-aside .link {{ display:inline-block; margin-top:1.8rem; }}

/* Lab table (brainstorm) */
.provocation {{ display:grid; grid-template-columns:1fr 1fr; gap:3.6rem; align-items:end; padding-bottom:2.2rem; border-bottom:1px solid var(--ink); }}
.provocation blockquote {{ margin:.9rem 0 0; padding:0; border:none; font-family:var(--display); font-style:italic; font-weight:400;
  font-size:2.1rem; line-height:1.3; color:var(--ink); word-break:keep-all; }}
.ideas {{ display:grid; grid-template-columns:repeat(3,1fr); gap:0; margin-top:0; }}
.idea {{ padding:2rem 1.8rem 2rem 0; border-right:1px solid var(--rule); }}
.idea + .idea {{ padding-left:1.8rem; }}
.idea:last-child {{ border-right:none; padding-right:0; }}
.idea h4 {{ font-family:var(--display); font-weight:500; font-size:1.42rem; line-height:1.3; color:var(--ink); margin:.7rem 0 1.1rem; padding:0; word-break:keep-all; }}
.idea dl {{ margin:0; }}
.idea dt {{ font-family:var(--label); font-size:.54rem; letter-spacing:.24em; text-transform:uppercase; color:var(--mute); margin-top:.9rem; }}
.idea dd {{ margin:.25rem 0 0; font-family:var(--body); font-weight:300; font-size:.92rem; line-height:1.75; color:var(--ink-soft); word-break:keep-all; }}
.idea dd b {{ font-weight:600; color:var(--ink); }}
.qs {{ background:var(--ink); color:var(--paper); padding:2.2rem 2.4rem; margin-top:.6rem; }}
.qs ol {{ list-style:none; margin:1rem 0 0; padding:0; counter-reset:q; }}
.qs li {{ counter-increment:q; display:grid; grid-template-columns:2.4rem 1fr; padding:.75rem 0; border-top:1px solid rgba(207,197,178,.2); margin:0;
  font-family:var(--body); font-weight:300; font-size:1rem; line-height:1.7; color:rgba(244,239,229,.9); word-break:keep-all; }}
.qs li::before {{ content:"Q" counter(q); font-family:var(--display); font-style:italic; color:var(--gold); font-size:1.1rem; }}
.notes-cap {{ margin:2.2rem 0 .4rem; }}

/* Daily study */
.study-head {{ display:grid; grid-template-columns:auto 1fr; gap:3rem; align-items:center; padding:2rem 0 2.2rem; border-bottom:1px solid var(--ink); }}
.day {{ font-family:var(--display); font-weight:300; font-size:1.1rem; color:var(--mute); text-align:center; padding-right:3rem; border-right:1px solid var(--rule); }}
.day em {{ display:block; font-style:italic; font-size:5.6rem; line-height:.9; color:var(--gold); }}
.study-head h3 {{ font-family:var(--display); font-weight:500; font-size:2.3rem; line-height:1.2; margin:.6rem 0 .8rem; padding:0; color:var(--ink); word-break:keep-all; }}
.concept {{ display:grid; grid-template-columns:1fr 1fr; gap:3.4rem; padding:2.6rem 0; border-bottom:1px solid var(--rule); align-items:start; }}
.equation {{ border-top:1px solid var(--ink); border-bottom:1px solid var(--ink); padding:1.4rem 1rem; text-align:center; margin:1rem 0 1.4rem;
  font-family:var(--display); font-style:italic; font-size:1.9rem; color:var(--ink); }}
.equation small {{ display:block; font-style:normal; font-family:var(--label); font-size:.56rem; letter-spacing:.24em; color:var(--mute); margin-top:.6rem; text-transform:uppercase; }}
.sub-k {{ display:flex; justify-content:space-between; align-items:baseline; margin:2.6rem 0 0; padding-bottom:.7rem; border-bottom:1px solid var(--ink); }}
.sub-k span:first-child {{ font-family:var(--display); font-size:1.5rem; color:var(--ink); }}
.read-row {{ display:grid; grid-template-columns:3rem 1fr 15rem; gap:1.6rem; padding:1.4rem 0; border-bottom:1px solid var(--rule); align-items:start; }}
.read-row .idx {{ font-family:var(--display); font-style:italic; font-size:1.6rem; color:var(--gold); line-height:1; }}
.read-row h5 {{ font-family:var(--display); font-weight:500; font-size:1.28rem; line-height:1.3; margin:.45rem 0 .3rem; padding:0; color:var(--ink); }}
.read-row .by {{ font-family:var(--display); font-style:italic; font-size:1rem; color:var(--mute); }}
.read-row .focus {{ font-family:var(--body); font-weight:300; font-size:.9rem; line-height:1.75; color:var(--ink-soft); word-break:keep-all; }}
.read-row .focus b {{ font-weight:600; color:var(--ink); }}
.read-row .focus .kicker {{ display:block; margin-bottom:.3rem; }}
.read-row .acts {{ margin-top:.7rem; display:flex; gap:1rem; align-items:center; flex-wrap:wrap; }}
.pat-no {{ font-family:var(--label); font-size:.8rem; letter-spacing:.14em; color:var(--ink); }}
.study-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:3.6rem; margin-top:.4rem; }}
.plan {{ list-style:none; margin:1.2rem 0 0; padding:0; border-left:1px solid var(--gold); }}
.plan li {{ position:relative; padding:0 0 1.4rem 1.6rem; margin:0; }}
.plan li::before {{ content:""; position:absolute; left:-4px; top:.45rem; width:7px; height:7px; background:var(--paper); border:1px solid var(--gold); transform:rotate(45deg); }}
.plan .t {{ font-family:var(--label); font-size:.6rem; letter-spacing:.22em; color:var(--gold); }}
.plan .d {{ font-family:var(--body); font-weight:300; font-size:.95rem; line-height:1.7; color:var(--ink-soft); word-break:keep-all; }}
.plan .d b {{ font-weight:600; color:var(--ink); }}
details.check {{ border-bottom:1px solid var(--rule); padding:1rem 0; }}
details.check summary {{ cursor:pointer; list-style:none; font-family:var(--body); font-size:.98rem; line-height:1.7; color:var(--ink); word-break:keep-all; }}
details.check summary::-webkit-details-marker {{ display:none; }}
details.check summary::before {{ content:"＋"; font-family:var(--label); color:var(--gold); margin-right:.8rem; font-size:.8rem; }}
details.check[open] summary::before {{ content:"－"; }}
details.check div {{ margin:.7rem 0 0 1.7rem; font-family:var(--body); font-weight:300; font-size:.92rem; line-height:1.8; color:var(--ink-soft); }}


/* Industry pulse */
.pulse {{ margin-bottom:1rem; }}
.pulse-head {{ display:flex; justify-content:space-between; align-items:baseline; padding-bottom:.8rem; border-bottom:1px solid var(--ink); }}
.pulse-ko {{ font-family:var(--display); font-size:1.2rem; color:var(--ink-soft); }}
.needs {{ display:grid; grid-template-columns:repeat(3,1fr); }}
.need {{ padding:1.6rem 1.6rem 1.6rem 0; border-right:1px solid var(--rule); }}
.need + .need {{ padding-left:1.6rem; }} .need:last-child {{ border-right:none; padding-right:0; }}
.need h4 {{ font-family:var(--display); font-weight:500; font-size:1.35rem; line-height:1.35; margin:.6rem 0 .9rem; padding:0; color:var(--ink); word-break:keep-all; }}
.pain {{ font-family:var(--body); font-weight:300; font-size:.93rem; line-height:1.75; color:var(--ink-soft); word-break:keep-all; }}
.pain span {{ display:block; font-family:var(--label); font-size:.54rem; letter-spacing:.24em; color:var(--mute); margin-bottom:.25rem; }}
.need-refs {{ margin-top:.7rem; }}
.refm {{ display:inline-flex; align-items:center; justify-content:center; min-width:1.15rem; height:1.15rem; margin-left:.25rem; padding:0 .2rem;
  border:1px solid var(--gold); color:var(--gold) !important; font-family:var(--label); font-size:.58rem; text-decoration:none !important; vertical-align:super; }}
.refm:hover {{ background:var(--gold); color:var(--paper) !important; }}
.hls {{ display:grid; grid-template-columns:1fr 1fr; column-gap:3rem; }}
.hl {{ display:grid; grid-template-columns:1.6rem 3.2rem 1fr; grid-template-rows:auto auto; column-gap:.6rem; padding:.85rem 0;
  border-bottom:1px solid var(--rule); text-decoration:none !important; }}
.hl:hover .hl-t {{ color:var(--gold); }}
.hl-n {{ grid-row:1 / span 2; font-family:var(--display); font-style:italic; color:var(--gold); font-size:1.1rem; }}
.hl-d {{ grid-row:1 / span 2; font-family:var(--label); font-size:.6rem; letter-spacing:.14em; color:var(--mute); padding-top:.3rem; }}
.hl-t {{ font-family:var(--body); font-size:.95rem; line-height:1.55; color:var(--ink); transition:color .3s; word-break:keep-all; }}
.hl-s {{ font-family:var(--display); font-style:italic; font-size:.92rem; color:var(--mute); }}

/* References & players */
.refs {{ margin-top:2rem; }}
.refs .kicker {{ display:block; padding-bottom:.5rem; border-bottom:1px solid var(--rule); }}
.ref-row {{ display:grid; grid-template-columns:1.4rem 1fr; column-gap:.6rem; padding:.6rem 0; border-bottom:1px solid var(--rule); text-decoration:none !important; }}
.ref-row:hover .ref-t {{ color:var(--gold); }}
.ref-n {{ grid-row:1 / span 2; font-family:var(--label); font-size:.62rem; color:var(--gold); padding-top:.2rem; }}
.ref-t {{ font-family:var(--body); font-size:.88rem; line-height:1.55; color:var(--ink); transition:color .3s; word-break:keep-all; }}
.ref-s {{ font-family:var(--display); font-style:italic; font-size:.88rem; color:var(--mute); }}
.tech-block {{ border-bottom:1px solid var(--rule); padding-bottom:2.4rem; }}
.tech-block .article {{ border-bottom:none; }}
.who {{ background:var(--paper-deep); padding:1.6rem 1.8rem 1.4rem; }}
.who-head {{ display:flex; justify-content:space-between; align-items:baseline; padding-bottom:.8rem; border-bottom:1px solid var(--ink); }}
.who-head span:first-child {{ font-family:var(--display); font-size:1.35rem; color:var(--ink); }}
.players {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); }}
.player {{ padding:1.1rem 1.2rem 0 0; border-right:1px solid var(--rule); }}
.player + .player {{ padding-left:1.2rem; }} .player:last-child {{ border-right:none; }}
.pl-role {{ font-family:var(--label); font-size:.54rem; letter-spacing:.24em; text-transform:uppercase; color:var(--gold); }}
.pl-name {{ font-family:var(--display); font-weight:600; font-size:1.3rem; color:var(--ink); margin:.3rem 0 .4rem; }}
.pl-act {{ font-family:var(--body); font-weight:300; font-size:.88rem; line-height:1.7; color:var(--ink-soft); word-break:keep-all; }}
.pl-act b {{ font-weight:600; color:var(--ink); }}
.empty {{ font-family:var(--display); font-style:italic; font-size:1.05rem; color:var(--mute); padding:1.4rem 0; border-bottom:1px solid var(--rule); }}
.notices {{ display:flex; flex-direction:column; gap:.2rem; margin:1rem 0 0; font-family:var(--label); font-size:.62rem; letter-spacing:.08em; color:var(--mute); text-align:center; }}
.past-banner {{ display:flex; justify-content:center; align-items:center; gap:1.4rem; padding:.9rem; margin:-1rem 0 2rem;
  border-top:1px solid var(--gold); border-bottom:1px solid var(--gold); font-family:var(--display); font-size:1.1rem; color:var(--ink); }}

/* Archive sidebar */
[data-testid="stSidebar"] {{ min-width:300px; }}
.arch {{ padding:.4rem 0 1.4rem; }}
.arch-title {{ font-family:var(--display) !important; font-weight:400; font-size:1.9rem; color:var(--ink); letter-spacing:0 !important; }}
.arch-sub {{ font-family:var(--label); font-size:.58rem; letter-spacing:.26em; text-transform:uppercase; color:var(--mute); padding-bottom:.9rem; border-bottom:1px solid var(--ink); }}
.arch-month {{ font-family:var(--display) !important; font-style:italic; font-size:1.05rem; color:var(--gold); margin:1.3rem 0 .3rem; letter-spacing:0 !important; }}
a.arch-item {{ display:block; padding:.75rem 0 .75rem .9rem; border-left:2px solid transparent; border-bottom:1px solid var(--rule);
  text-decoration:none !important; transition:background .3s, border-color .3s; }}
a.arch-item:hover {{ background:rgba(163,134,79,.08); border-left-color:var(--rule); }}
a.arch-item.on {{ border-left-color:var(--gold); background:rgba(163,134,79,.1); }}
.arch-date {{ display:block; font-family:var(--label); font-size:.62rem; letter-spacing:.2em; color:var(--gold); }}
.arch-note {{ color:var(--ink-soft); margin-left:.3rem; }}
.arch-sum {{ display:block; font-family:var(--body) !important; font-weight:500; font-size:.95rem; line-height:1.5; color:var(--ink); margin-top:.2rem; letter-spacing:0 !important; word-break:keep-all; }}
.arch-theme {{ display:block; font-family:var(--body) !important; font-weight:300; font-size:.78rem; color:var(--mute); margin-top:.15rem; letter-spacing:0 !important; }}
.arch-empty {{ font-family:var(--display) !important; font-style:italic; color:var(--mute); padding:1rem 0; }}

.locked {{ text-align:center; padding:3.4rem 2rem; background:var(--ink); color:var(--paper); position:relative; }}
.locked::before {{ content:''; position:absolute; inset:8px; border:1px solid rgba(163,134,79,.45); pointer-events:none; }}
.lock-mark {{ font-family:var(--display); color:var(--gold); font-size:1.4rem; margin-bottom:1rem; }}
.locked h4 {{ font-family:var(--display); font-weight:500; font-size:1.7rem; color:var(--paper); margin:.8rem 0 .7rem; padding:0; }}
.locked p {{ font-family:var(--body); font-weight:300; font-size:.95rem; color:rgba(244,239,229,.75); margin:0; }}
.locked b {{ color:var(--gold); font-weight:500; }}
.lock-state {{ font-family:var(--label); font-size:.58rem; letter-spacing:.24em; text-transform:uppercase; color:var(--gold); margin:.4rem 0 .2rem; }}


/* Long read */
.dropcap::first-letter {{ float:left; font-family:var(--display); font-weight:500; font-size:3.9rem; line-height:.85;
  padding:.42rem .6rem 0 0; color:var(--gold); }}
details.longread {{ margin-top:2.4rem; border-top:1px solid var(--ink); border-bottom:1px solid var(--ink); }}
details.longread summary {{ list-style:none; cursor:pointer; display:grid; grid-template-columns:auto 1fr auto; align-items:baseline; gap:1.6rem; padding:1.3rem 0; }}
details.longread summary::-webkit-details-marker {{ display:none; }}
.lr-k {{ font-family:var(--label); font-size:.6rem; letter-spacing:.28em; text-transform:uppercase; color:var(--gold); white-space:nowrap; }}
.lr-title {{ font-family:var(--display); font-weight:500; font-size:1.45rem; line-height:1.35; color:var(--ink); word-break:keep-all; }}
.lr-more {{ font-family:var(--label); font-size:.6rem; letter-spacing:.24em; text-transform:uppercase; color:var(--ink); border-bottom:1px solid var(--gold); padding-bottom:2px; white-space:nowrap; }}
.lr-more::after {{ content:" ⟶"; }}
details.longread[open] .lr-more {{ font-size:0; border:none; }}
details.longread[open] .lr-more::after {{ content:"Close ×"; font-size:.6rem; }}
.lr-body {{ max-width:720px; margin:0 auto; padding:1.4rem 0 3rem; }}
.lr-dek {{ font-family:var(--display); font-style:italic; font-size:1.35rem; line-height:1.6; color:var(--ink-soft); margin:0 0 2rem; text-align:center; word-break:keep-all; }}
.lr-p {{ font-family:var(--body); font-weight:300; font-size:1.06rem; line-height:2.05; color:var(--ink); margin:0 0 1.4rem; text-align:justify; word-break:keep-all; }}
.lr-p b {{ font-weight:600; }}
.lr-quote {{ margin:2.4rem -3rem; padding:1.6rem 0; border:none; border-top:1px solid var(--gold); border-bottom:1px solid var(--gold);
  font-family:var(--display); font-weight:500; font-size:1.7rem; line-height:1.45; color:var(--ink); text-align:center; word-break:keep-all; }}
.lr-watch {{ margin-top:2.4rem; background:var(--paper-deep); padding:1.6rem 1.8rem; }}
.lr-watch ol {{ margin:.9rem 0 0; padding-left:1.3rem; }}
.lr-watch li {{ font-family:var(--body); font-weight:300; font-size:.95rem; line-height:1.8; color:var(--ink-soft); margin:.3rem 0; word-break:keep-all; }}
.lr-watch li::marker {{ font-family:var(--display); color:var(--gold); }}

/* Referee's note */
.review {{ margin-top:2.4rem; padding:2rem 2.2rem; border:1px solid var(--rule); position:relative; }}
.review::before {{ content:''; position:absolute; inset:5px; border:1px solid rgba(207,197,178,.5); pointer-events:none; }}
.rv-verdict {{ font-family:var(--display); font-style:italic; font-size:1.45rem; line-height:1.5; color:var(--ink); margin:.8rem 0 1.4rem; word-break:keep-all; }}
.rv-cols {{ display:grid; grid-template-columns:1fr 1fr; gap:2.6rem; }}
.rv-h {{ font-family:var(--display); font-size:1.1rem; color:var(--ink); padding-bottom:.4rem; border-bottom:1px solid var(--ink); }}
.review ul {{ margin:.6rem 0 0; padding-left:1rem; }}
.review li {{ font-family:var(--body); font-weight:300; font-size:.92rem; line-height:1.8; color:var(--ink-soft); margin:.35rem 0; word-break:keep-all; }}
.review li::marker {{ color:var(--gold); }}
.review li b {{ font-weight:600; color:var(--ink); }}
.rv-us {{ margin-top:1.6rem; padding-top:1.2rem; border-top:1px solid var(--rule); }}
.rv-us p {{ font-family:var(--body); font-weight:300; font-size:.98rem; line-height:1.9; color:var(--ink); margin:.5rem 0 0; word-break:keep-all; }}


/* Streamlit 기본 제목 스타일·앵커 아이콘 무력화 */
[data-testid="stHeaderActionElements"], .stApp h1 a, .stApp h2 a, .stApp h3 a, .stApp h4 a {{ display:none !important; }}
.stApp h1.mast-title {{ font-family:var(--display) !important; font-weight:300 !important; font-size:clamp(3.2rem,8.5vw,7.4rem) !important;
  line-height:.95 !important; letter-spacing:-.015em !important; padding:0 !important; margin:2.2rem 0 .6rem !important; color:var(--ink) !important; }}
.stApp h1.mast-title em {{ font-family:var(--display) !important; font-style:italic !important; font-weight:300 !important; color:var(--gold) !important; }}
.stApp h3.ins-head {{ font-family:var(--display) !important; font-weight:400 !important; font-style:italic !important; font-size:1.95rem !important; line-height:1.3 !important; padding:0 !important; }}
.stApp h3.art-title {{ font-family:var(--display) !important; font-weight:500 !important; font-size:2.05rem !important; line-height:1.2 !important; padding:0 !important; }}
.stApp .study-head h3 {{ font-family:var(--display) !important; font-weight:500 !important; font-size:2.3rem !important; line-height:1.2 !important; padding:0 !important; }}
.stApp .idea h4, .stApp .need h4, .stApp .locked h4 {{ font-family:var(--display) !important; font-weight:500 !important; padding:0 !important; }}
.stApp .idea h4 {{ font-size:1.42rem !important; }} .stApp .need h4 {{ font-size:1.35rem !important; }} .stApp .locked h4 {{ font-size:1.7rem !important; color:var(--paper) !important; }}
.stApp .read-row h5 {{ font-family:var(--display) !important; font-weight:500 !important; font-size:1.28rem !important; padding:0 !important; }}
.stApp blockquote {{ font-family:var(--display) !important; }}

/* Colophon */
.colophon {{ margin-top:5.5rem; text-align:center; }}
.colophon .mark {{ font-family:var(--display); font-size:1.4rem; color:var(--gold); margin:1.6rem 0 .6rem; }}
.colophon p {{ font-family:var(--label); font-size:.58rem; letter-spacing:.26em; text-transform:uppercase; color:var(--mute); margin:.3rem 0; }}

@media (max-width: 900px) {{
  .block-container {{ padding:1.6rem 1.1rem 4rem; }}
  .ticker {{ grid-template-columns:repeat(2,1fr); }} .tk {{ border-bottom:1px solid var(--rule); }}
  .market {{ grid-template-columns:1fr; }} .m-head,.m-cap,.m-body,.m-chart {{ grid-column:1; grid-row:auto; }} .m-cap {{ margin-top:2.4rem; }}
  .article, .paper-body, .provocation, .ideas, .concept, .study-grid, .study-head {{ grid-template-columns:1fr; gap:2rem; }}
  .needs, .players, .hls, .rv-cols {{ grid-template-columns:1fr; }} .lr-quote {{ margin:2rem 0; font-size:1.4rem; }} details.longread summary {{ grid-template-columns:1fr; gap:.4rem; }}
  .needs, .players, .hls {{ grid-template-columns:1fr; }} .need, .need + .need, .player, .player + .player {{ padding-left:0; padding-right:0; border-right:none; border-bottom:1px solid var(--rule); }}
  .article.rev > .col-text {{ order:1; }} .article.rev > figure {{ order:2; }}
  .idea, .idea + .idea {{ padding:1.6rem 0; border-right:none; border-bottom:1px solid var(--rule); }}
  .read-row {{ grid-template-columns:2.2rem 1fr; }} .read-row .focus {{ grid-column:2; }}
  .paper-aside {{ border-left:none; padding-left:0; }}
  .day {{ border-right:none; padding-right:0; }}
  .mast-meta span:nth-child(3) {{ display:none; }}
}}
</style>"""


# ════════════════════════════════════════════════════════════════
#  Masthead / sections
# ════════════════════════════════════════════════════════════════
CONTENTS = [("I", "The Market"), ("II", "CMP Technology"), ("III", "Research"),
            ("IV", "The Lab Table"), ("V", "Daily Study")]


def masthead(now, issue_no, dedication):
    toc = "".join(f"<span><i>{n}</i>{t}</span>" for n, t in CONTENTS)
    return f"""
<header class="mast">
<div class="mast-meta"><span>Vol. {now.year - 2025} &nbsp;·&nbsp; No. {issue_no:03d}</span><span>{now.strftime('%A, %d %B %Y')}</span><span>Seoul Edition</span></div>
<div class="rule"></div>
<h1 class="mast-title">Morning <em>Briefing</em></h1>
<div class="mast-sub">The Semiconductor &amp; Nanotech Review</div>
<div class="rule-double"></div>
<div class="mast-ded">Privately curated for &nbsp;<b>{esc(dedication)}</b></div>
<div class="contents">{toc}</div>
</header>"""


def prelude():
    return """<div class="prelude"><div class="orn">◆ ◆ ◆</div>
<p>세계의 시장과 실험실에서 밤사이 일어난 일들을,<br>한 권의 아침으로 엮어 드립니다.</p></div>"""


def section(num, title, ko):
    return f"""<div class="sec"><span class="sec-num">{num}</span>
<div><div class="sec-title">{title}</div><div class="sec-ko">{esc(ko)}</div></div></div>"""


def colophon(issue_no, now):
    return f"""<div class="colophon"><div class="rule-double"></div><div class="mark">◆</div>
<p>Morning Briefing &nbsp;·&nbsp; Edition No. {issue_no:03d}</p>
<p>Compiled at {now.strftime('%H:%M')} KST &nbsp;·&nbsp; Market · Yahoo Finance &nbsp;·&nbsp; News · Google News &nbsp;·&nbsp; Papers · OpenAlex &nbsp;·&nbsp; Patents · Google Patents</p>
<p>Facts come from search results only &nbsp;·&nbsp; Summaries are AI-written, check the originals</p></div>"""


# ════════════════════════════════════════════════════════════════
#  I. Market
# ════════════════════════════════════════════════════════════════
def logo(uri, name):
    if uri:
        return f'<div class="logo" title="{esc(name)}"><img src="{uri}" alt="{esc(name)}"></div>'
    return f'<div class="logo"><span class="mono">{esc(name)}</span></div>'


def ticker(rows, logos):
    cells = []
    for r in rows:
        up = r["chg"] >= 0
        px = f"₩{r['price']:,.0f}" if r["cur"] == "₩" else f"${r['price']:,.2f}"
        cap = (f"시총 ₩{r['cap'] / 1000:,.0f}조" if r["cur"] == "₩" else f"Mkt. cap ${r['cap']:,.0f}B") if r["cap"] else ""
        cells.append(f"""<div class="tk"><div class="tk-head">{logo(logos.get(r['name']), r['name'])}<span class="tk-name">{esc(r['code'])}</span></div>
<div class="tk-px">{px}</div><div class="tk-chg {'up' if up else 'down'}">{'▲' if up else '▼'} {r['chg']:+.2f}%</div>
<div class="tk-cap">{cap}</div></div>""")
    return f'<div class="ticker">{"".join(cells)}</div>'


def movers(rows, logos):
    if not rows:
        return ""
    m = max(abs(r["chg"]) for r in rows) * 1.6 or 1
    out = []
    for r in rows:
        w = abs(r["chg"]) / m * 100
        cls = "up" if r["chg"] >= 0 else "down"
        bar = f'<i class="bar {cls}" style="width:{w:.1f}%"></i>'
        val = f'<span class="mv-val {cls}">{r["chg"]:+.2f}%</span>'
        neg = val + bar if cls == "down" else ""
        pos = bar + val if cls == "up" else ""
        out.append(f"""<div class="mv-row"><div class="mv-id">{logo(logos.get(r['name']), r['name'])}<div class="code">{esc(r['code'])}</div></div>
<div class="mv-track"><div class="mv-half neg">{neg}</div><div class="mv-axis"></div><div class="mv-half pos">{pos}</div></div></div>""")
    return f"""<div class="movers">{''.join(out)}</div>
<div class="mv-scale"><span></span><div><span>−{m:.1f}%</span><span>0</span><span>+{m:.1f}%</span></div></div>"""


def market(insight, rows, logos, now):
    """2행 그리드: 1행 = 헤드라인 | 차트 제목,  2행 = 목록 | 차트  → 두 괘선이 같은 높이에 놓임"""
    bullets = insight.get("bullets", []) if isinstance(insight, dict) else [insight]
    head = insight.get("headline", "") if isinstance(insight, dict) else ""
    lis = "".join(f'<li><span class="n">{i + 1:02d}</span><div class="prose">{md(b)}</div></li>' for i, b in enumerate(bullets))
    cap = '<div class="chart-cap"><span>Daily Movement</span><span>전일 대비 등락</span></div>' if rows else ""
    return f"""<div class="market">
<div class="m-head"><div class="kicker">Editor's Note</div><h3 class="ins-head">{md(head)}</h3></div>
<div class="m-cap">{cap}</div>
<div class="m-body"><ol class="ins-list">{lis}</ol><div class="sig">— The Desk, {now.strftime('%d.%m.%Y')}</div></div>
<div class="m-chart">{movers(rows, logos)}</div></div>
{longread(insight.get("longread") if isinstance(insight, dict) else None)}"""


# ════════════════════════════════════════════════════════════════
#  Cross-section diagram (CMP 단면 도식)
# ════════════════════════════════════════════════════════════════
def _mat(m):
    m = (m or "").lower()
    table = [
        (("cu", "copper", "구리"), ("url(#cu{u})", "#6E3F1C", None)),
        (("tan", "ta/", "ta ", "tin", "barrier", "배리어"), ("#3E3A36", "#1E1B18", None)),
        (("low-k", "lowk", "sioc", "sicoh"), ("#D3CEDA", "#9E98A8", "dot")),
        (("sicn", "sin", "nitride", "질화"), ("#A3ADA4", "#6F7A71", None)),
        (("sio2", "oxide", "teos", "산화막", "dielectric", "유전"), ("#ECE6D8", "#B9AE98", "hatch")),
        (("poly",), ("#B1A592", "#7E735F", None)),
        (("ru", "ruthenium"), ("#7F8A96", "#4E5862", None)),
        (("co", "cobalt"), ("#6E7F8D", "#46535E", None)),
        (("mo", "molyb"), ("#8D8F8A", "#5D5F5A", None)),
        (("w", "tungsten", "텅스텐"), ("#8C9196", "#5B6066", None)),
        (("si", "silicon", "실리콘", "substrate", "기판"), ("#3F4A54", "#232A31", None)),
    ]
    for keys, val in table:
        for k in keys:
            if (k == m) or (len(k) > 2 and k in m) or m.startswith(k + " ") or m.startswith(k + "/"):
                return val
    return ("#C4BAA6", "#8C8475", None)


def stack_svg(d, uid="a"):
    d = d or {}
    layers = (d.get("layers") or [])[:6]
    if not layers:
        return ""
    rnd = random.Random(uid)
    W, x0, x1, lx = 580, 20, 330, 356
    defs = f"""<defs>
<linearGradient id="cu{uid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#D08A55"/><stop offset=".45" stop-color="#B87333"/><stop offset="1" stop-color="#7E4520"/></linearGradient>
<pattern id="hx{uid}" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="7" stroke="#B9AE98" stroke-width=".7"/></pattern>
<pattern id="dt{uid}" width="6" height="6" patternUnits="userSpaceOnUse"><circle cx="3" cy="3" r=".9" fill="#8F889A"/></pattern>
<pattern id="rm{uid}" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2="6" stroke="{GOLD}" stroke-width="1.4" opacity=".75"/></pattern>
<pattern id="pd{uid}" width="16" height="12" patternUnits="userSpaceOnUse"><ellipse cx="5" cy="4" rx="2.6" ry="1.6" fill="#B8A684"/><ellipse cx="12" cy="9" rx="1.8" ry="1.1" fill="#B8A684"/></pattern>
<marker id="ar{uid}" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker>
</defs>"""
    g = []

    def label(y, name, sub, emph=False):
        g.append(f'<line x1="{x1 + 6}" y1="{y:.1f}" x2="{lx - 8}" y2="{y:.1f}" stroke="{MUTE}" stroke-width=".6"/>')
        g.append(f'<circle cx="{x1 + 6}" cy="{y:.1f}" r="2" fill="{GOLD if emph else INK}"/>')
        g.append(f'<text x="{lx}" y="{y - 2:.1f}" font-family="KoPubBatang, Noto Serif KR, Noto Serif CJK KR, serif" font-size="15" font-weight="{600 if emph else 500}" fill="{INK}">{esc(clip(name, 14))}</text>')
        if sub:
            g.append(f'<text x="{lx}" y="{y + 14:.1f}" font-family="Jost, KoPubDotum, Noto Sans CJK KR, sans-serif" font-size="10.5" letter-spacing="1.3" fill="{GOLD if emph else MUTE}">{esc(clip(sub, 22)).upper()}</text>')

    # ── 연마부: 하중 → 패드 → 슬러리
    show_pad = d.get("show_pad", True)
    y = 6
    if show_pad:
        cx = (x0 + x1) / 2
        g.append(f'<line x1="{cx}" y1="6" x2="{cx}" y2="30" stroke="{INK}" stroke-width="1.2" marker-end="url(#ar{uid})"/>')
        g.append(f'<text x="{cx + 10}" y="22" font-family="Cormorant Garamond, serif" font-style="italic" font-size="15" fill="{INK}">Downforce P</text>')
        y = 38
        g.append(f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="42" fill="#D9CBB0"/>')
        g.append(f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="42" fill="url(#pd{uid})"/>')
        g.append(f'<line x1="{x0}" y1="{y + 42}" x2="{x1}" y2="{y + 42}" stroke="#9C8A66" stroke-width="1"/>')
        label(y + 21, d.get("pad", "연마 패드"), "Polishing Pad")
        g.append(f'<line x1="{x0 + 14}" y1="{y + 21}" x2="{x0 + 74}" y2="{y + 21}" stroke="{INK}" stroke-width="1" marker-end="url(#ar{uid})"/>')
        g.append(f'<text x="{x0 + 80}" y="{y + 25}" font-family="Cormorant Garamond, serif" font-style="italic" font-size="14" fill="{INK}">v</text>')
        y += 42
        ab = (d.get("abrasive") or "").lower()
        pf, ps = (("#E8CF98", GOLD) if ("ceria" in ab or "ceo" in ab or "세리아" in ab)
                  else ("#DCDCDC", "#9A9A9A") if ("alumina" in ab or "al2o3" in ab)
                  else ("#F6F2E9", "#B3A890"))
        g.append(f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="30" fill="rgba(163,134,79,.10)"/>')
        for _ in range(26):
            r = rnd.uniform(2.6, 5.6)
            g.append(f'<circle cx="{rnd.uniform(x0 + 6, x1 - 6):.1f}" cy="{rnd.uniform(y + 6, y + 24):.1f}" r="{r:.1f}" fill="{pf}" stroke="{ps}" stroke-width=".8"/>')
        label(y + 15, d.get("abrasive", "슬러리"), "Slurry · Abrasive", emph=True)
        y += 30 + 6

    # ── 막 적층
    rel = [max(float(l.get("thickness", 1) or 1), .3) for l in layers]
    avail = 300
    hs = [max(34, r / sum(rel) * avail) for r in rel]
    stop = d.get("polish_stop_after")
    stop_y = None
    for i, (L, h) in enumerate(zip(layers, hs)):
        fill, edge, tex = _mat(L.get("material", ""))
        fill = fill.format(u=uid)
        pattern = (L.get("pattern") or "solid").lower()
        if pattern == "inlaid":
            hfill, hedge, htex = _mat(L.get("host", "SiO2"))
            g.append(f'<rect x="{x0}" y="{y:.1f}" width="{x1 - x0}" height="{h:.1f}" fill="{hfill.format(u=uid)}"/>')
            if htex:
                g.append(f'<rect x="{x0}" y="{y:.1f}" width="{x1 - x0}" height="{h:.1f}" fill="url(#{"hx" if htex == "hatch" else "dt"}{uid})"/>')
            n = 5
            pitch = (x1 - x0) / n
            lw = pitch * .48
            for k in range(n):
                fx = x0 + pitch * k + (pitch - lw) / 2
                dip = 4 if L.get("dishing") else 0
                bar = .14 * h
                # 배리어 라이너 + 금속 배선(디싱 시 오목한 상단)
                g.append(f'<path d="M{fx - 2:.1f},{y:.1f} L{fx - 2:.1f},{y + h - bar + 2:.1f} L{fx + lw + 2:.1f},{y + h - bar + 2:.1f} L{fx + lw + 2:.1f},{y:.1f} Z" fill="#3E3A36"/>')
                g.append(f'<path d="M{fx:.1f},{y:.1f} Q{fx + lw / 2:.1f},{y + dip * 2:.1f} {fx + lw:.1f},{y:.1f} L{fx + lw:.1f},{y + h - bar:.1f} L{fx:.1f},{y + h - bar:.1f} Z" fill="{fill}" stroke="{edge}" stroke-width=".5"/>')
            sub = f"{L.get('material', '')} in {L.get('host', '')}"
        else:
            g.append(f'<rect x="{x0}" y="{y:.1f}" width="{x1 - x0}" height="{h:.1f}" fill="{fill}"/>')
            if tex:
                g.append(f'<rect x="{x0}" y="{y:.1f}" width="{x1 - x0}" height="{h:.1f}" fill="url(#{"hx" if tex == "hatch" else "dt"}{uid})"/>')
            sub = L.get("material", "")
        if L.get("remove"):
            g.append(f'<rect x="{x0}" y="{y:.1f}" width="{x1 - x0}" height="{h:.1f}" fill="url(#rm{uid})"/>')
        g.append(f'<line x1="{x0}" y1="{y + h:.1f}" x2="{x1}" y2="{y + h:.1f}" stroke="{INK}" stroke-width=".5" opacity=".35"/>')
        role = L.get("role", "")
        label(y + h / 2, L.get("name", ""), f"{sub} · {role}" if role else sub, emph=bool(L.get("remove")))
        y += h
        if stop is not None and i == int(stop):
            stop_y = y
    if stop_y:
        g.append(f'<line x1="{x0 - 4}" y1="{stop_y:.1f}" x2="{x1 + 4}" y2="{stop_y:.1f}" stroke="{GOLD}" stroke-width="1.6" stroke-dasharray="5 4"/>')
        g.append(f'<rect x="{x0 + 6}" y="{stop_y - 9:.1f}" width="104" height="16" fill="{PAPER}"/>')
        g.append(f'<text x="{x0 + 12}" y="{stop_y + 3:.1f}" font-family="Jost, sans-serif" font-size="9.5" letter-spacing="1.8" fill="{GOLD}">POLISH STOP</text>')
    g.append(f'<rect x="{x0}" y="{y:.1f}" width="{x1 - x0}" height="10" fill="#2B333A" opacity=".25"/>')
    H = y + 18
    return f'<svg viewBox="0 0 {W} {H:.0f}" xmlns="http://www.w3.org/2000/svg" role="img">{defs}{"".join(g)}</svg>'


def flow_svg(toc, uid="t"):
    """논문 Graphical-Abstract 대체 도식: Problem → Approach → Outcome"""
    toc = toc or {}
    W, H, pw, gap = 900, 206, 262, 57
    out = [f'<defs><marker id="fa{uid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{GOLD}"/></marker></defs>']
    panels = [("I · PROBLEM", toc.get("problem", "")), ("II · APPROACH", toc.get("approach", "")), ("III · OUTCOME", toc.get("outcome", ""))]
    for k, (kick, text) in enumerate(panels):
        x = 10 + k * (pw + gap)
        dark = k == 2
        bg = INK if dark else PAPER
        fg = PAPER if dark else INK
        out.append(f'<rect x="{x}" y="10" width="{pw}" height="{H - 20}" fill="{bg}" stroke="{INK if not dark else INK}" stroke-width="1"/>')
        out.append(f'<rect x="{x + 6}" y="16" width="{pw - 12}" height="{H - 32}" fill="none" stroke="{GOLD}" stroke-opacity=".55" stroke-width=".8"/>')
        out.append(f'<text x="{x + pw / 2}" y="46" text-anchor="middle" font-family="Jost, sans-serif" font-size="10.5" letter-spacing="2.6" fill="{GOLD}">{kick}</text>')
        if dark and toc.get("outcome_figure"):
            out.append(f'<text x="{x + pw / 2}" y="106" text-anchor="middle" font-family="Cormorant Garamond, serif" font-size="50" fill="{GOLD}">{esc(clip(toc["outcome_figure"], 10))}</text>')
            ty = 142
        else:
            ty = 84
        for j, line in enumerate(wrap(text, 15)[:4 if not dark else 2]):
            out.append(f'<text x="{x + pw / 2}" y="{ty + j * 25}" text-anchor="middle" font-family="KoPubBatang, Noto Serif KR, Noto Serif CJK KR, serif" font-size="15.5" fill="{fg}">{esc(line)}</text>')
        if k < 2:
            ax = x + pw + 8
            out.append(f'<line x1="{ax}" y1="{H / 2}" x2="{ax + gap - 16}" y2="{H / 2}" stroke="{GOLD}" stroke-width="1.4" marker-end="url(#fa{uid})"/>')
    return f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img">{"".join(out)}</svg>'


# ════════════════════════════════════════════════════════════════
#  II. CMP technology
# ════════════════════════════════════════════════════════════════
def points(items):
    lis = []
    for p in items or []:
        if isinstance(p, dict):
            lis.append(f'<li><span class="pt-k">{esc(p.get("label", ""))}</span><div class="prose">{md(p.get("text", ""))}</div></li>')
        else:
            lis.append(f'<li><span class="pt-k">·</span><div class="prose">{md(p)}</div></li>')
    return f'<ul class="points">{"".join(lis)}</ul>'


def figs(items):
    if not items:
        return ""
    return '<div class="figs">' + "".join(
        f'<div><div class="fig-v">{esc(f.get("value", ""))}</div><div class="fig-l">{esc(f.get("label", ""))}</div></div>' for f in items[:3]) + "</div>"


def curve_svg(c, uid="c"):
    """개념 곡선 도식 (Preston 직선, Stribeck 곡선, 제타전위–pH 등)"""
    import math
    c = c or {}
    shape = (c.get("shape") or "linear").lower()
    W, H, L, R, T, B = 580, 330, 64, 24, 34, 58
    fx = {
        "linear": lambda t: .08 + .84 * t,
        "saturating": lambda t: .08 + .84 * (1 - math.exp(-3.4 * t)) / (1 - math.exp(-3.4)),
        "sigmoid": lambda t: .08 + .84 / (1 + math.exp(-11 * (t - .5))),
        "decreasing": lambda t: .92 - .84 * t,
        "valley": lambda t: .12 + .78 * math.exp(-7 * t) + .55 * t ** 2.2,
        "peak": lambda t: .1 + .8 * math.exp(-((t - .5) / .2) ** 2),
        "threshold": lambda t: .1 if t < .32 else .1 + .82 * (t - .32) / .68,
    }.get(shape, lambda t: .08 + .84 * t)
    px = lambda t: L + t * (W - L - R)
    py = lambda v: H - B - v * (H - T - B)
    g = []
    for k, rg in enumerate((c.get("regions") or [])[:4]):
        a, b = float(rg.get("from", 0)), float(rg.get("to", 1))
        g.append(f'<rect x="{px(a):.1f}" y="{T}" width="{px(b) - px(a):.1f}" height="{H - T - B}" fill="{PAPER_DEEP if k % 2 == 0 else "rgba(163,134,79,.09)"}"/>')
        g.append(f'<text x="{(px(a) + px(b)) / 2:.1f}" y="{T + 18}" text-anchor="middle" font-family="KoPubBatang, Noto Serif KR, Noto Serif CJK KR, serif" font-size="13" fill="{INK_SOFT}">{esc(clip(rg.get("label", ""), 12))}</text>')
    pts = [(px(i / 80), py(fx(i / 80))) for i in range(81)]
    path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    g.append(f'<path d="{path} L{px(1):.1f},{py(0):.1f} L{px(0):.1f},{py(0):.1f} Z" fill="rgba(163,134,79,.12)"/>')
    g.append(f'<path d="{path}" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>')
    for m in (c.get("marks") or [])[:3]:
        t = float(m.get("at", .5))
        x, y = px(t), py(fx(t))
        ty = y - 34 if y > T + 60 else y + 40
        g.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{ty + (8 if ty < y else -14):.1f}" stroke="{GOLD}" stroke-width=".9"/>')
        g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{PAPER}" stroke="{GOLD}" stroke-width="2"/>')
        g.append(f'<text x="{x:.1f}" y="{ty:.1f}" text-anchor="middle" font-family="Cormorant Garamond, KoPubBatang, Noto Serif KR, serif" font-style="italic" font-size="16" fill="{INK}">{esc(clip(m.get("label", ""), 14))}</text>')
    g.append(f'<line x1="{L}" y1="{H - B}" x2="{W - R}" y2="{H - B}" stroke="{INK}" stroke-width="1"/>')
    g.append(f'<line x1="{L}" y1="{T}" x2="{L}" y2="{H - B}" stroke="{INK}" stroke-width="1"/>')
    g.append(f'<text x="{(L + W - R) / 2}" y="{H - 18}" text-anchor="middle" font-family="Cormorant Garamond, KoPubBatang, Noto Serif KR, serif" font-style="italic" font-size="18" fill="{INK}">{esc(c.get("x_label", ""))}</text>')
    g.append(f'<text x="22" y="{(T + H - B) / 2}" text-anchor="middle" transform="rotate(-90 22 {(T + H - B) / 2})" font-family="Cormorant Garamond, KoPubBatang, Noto Serif KR, serif" font-style="italic" font-size="18" fill="{INK}">{esc(c.get("y_label", ""))}</text>')
    return f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img">{"".join(g)}</svg>'


def _frame(svg, idx, title, caption, kind=None):
    head = kind or f"Plate {ROMAN[idx % 10]}"
    no = kind.upper() if kind else f"FIG. {idx + 1}"
    return f"""<figure class="plate"><div class="plate-box"><div class="plate-frame">
<div class="plate-title">{head} &nbsp;·&nbsp; {esc(title)}</div>{svg}</div></div>
<figcaption><span class="fig-no">{no}</span>{md(caption)}</figcaption></figure>"""


def plate(diagram, idx, uid):
    d = diagram or {}
    svg = stack_svg(d, uid)
    if not svg:
        return ""
    return f"""<figure class="plate"><div class="plate-box"><div class="plate-frame">
<div class="plate-title">Plate {ROMAN[idx % 10]} &nbsp;·&nbsp; {esc(d.get('title', 'Cross-section'))}</div>{svg}</div></div>
<figcaption><span class="fig-no">FIG. {idx + 1}</span>{md(d.get('caption', ''))}</figcaption></figure>"""


def _refmarks(refs, news):
    out = []
    for r in refs or []:
        try:
            n = news[int(r) - 1]
        except (ValueError, IndexError, TypeError):
            continue
        out.append(f'<a class="refm" href="{esc(n["link"])}" target="_blank" title="{esc(n["title"])}">{int(r)}</a>')
    return "".join(out)


def players(items, news):
    if not items:
        return ""
    cards = "".join(f"""<div class="player"><div class="pl-role">{esc(p.get('role', ''))}</div><div class="pl-name">{esc(p.get('name', ''))}{_refmarks(p.get('refs'), news)}</div>
<div class="pl-act">{md(p.get('activity', ''))}</div></div>""" for p in items[:4])
    return f"""<div class="who"><div class="who-head"><span>Who's Working On It</span><span class="kicker">개발 중인 기업</span></div>
<div class="players">{cards}</div></div>"""


def references(refs, news):
    rows = []
    for r in refs or []:
        try:
            n = news[int(r) - 1]
        except (ValueError, IndexError, TypeError):
            continue
        rows.append(f"""<a class="ref-row" href="{esc(n['link'])}" target="_blank"><span class="ref-n">{int(r)}</span>
<span class="ref-t">{esc(n['title'])}</span><span class="ref-s">{esc(n['source'])} · {esc(n['date'])}</span></a>""")
    return f'<div class="refs"><div class="kicker">References</div>{"".join(rows)}</div>' if rows else ""


def tech_article(i, t, news=None):
    news = news or []
    return f"""<div class="tech-block"><article class="article {'rev' if i % 2 else ''}">
<div class="col-text"><div class="kicker art-no">Dossier No. {i + 1:02d} &nbsp;·&nbsp; {esc(t.get('tag', 'CMP'))}</div>
<h3 class="art-title">{md(t.get('title', ''))}</h3><p class="lede">{md(t.get('lede', ''))}</p>
{points(t.get('points'))}{figs(t.get('key_figures'))}{references(t.get('refs'), news)}</div>
{plate(t.get('diagram'), i, f'tech{i}')}</article>{players(t.get('players'), news)}{longread(t.get('longread'))}</div>"""


def pulse(needs, news):
    """II 섹션 서두: 업계 니즈 3가지 + 최신 헤드라인 (실제 뉴스 링크)"""
    cards = "".join(f"""<div class="need"><div class="kicker">Need {k + 1:02d}</div><h4>{md(n.get('need', ''))}</h4>
<div class="pain"><span>현장의 고민</span>{md(n.get('pain', ''))}</div><div class="need-refs">{_refmarks(n.get('refs'), news)}</div></div>"""
                    for k, n in enumerate((needs or [])[:3]))
    heads = "".join(f"""<a class="hl" href="{esc(n['link'])}" target="_blank"><span class="hl-n">{k + 1}</span><span class="hl-d">{esc(n['date'][5:].replace('-', '.'))}</span>
<span class="hl-t">{esc(n['title'])}</span><span class="hl-s">{esc(n['source'])}</span></a>""" for k, n in enumerate((news or [])[:8]))
    head_block = f"""<div class="sub-k" style="margin-top:2.4rem"><span>Latest Headlines</span><span class="kicker">최근 14일 CMP 뉴스</span></div>
<div class="hls">{heads}</div>""" if heads else ""
    return f"""<div class="pulse"><div class="pulse-head"><span class="kicker">Industry Pulse</span><span class="pulse-ko">지금 CMP 업계가 원하는 것과 고민</span></div>
<div class="needs">{cards}</div>{head_block}</div>"""


# ════════════════════════════════════════════════════════════════
#  III. Papers
# ════════════════════════════════════════════════════════════════
def verified_badge(v, src="OpenAlex"):
    return f'<span class="badge ok">✓ {src}</span>' if v else '<span class="badge">Unverified</span>'


def paper_article(i, p, toc_img=None):
    authors = p.get("authors_list") or []
    corr = p.get("corresponding_display") or p.get("corresponding_author", "")
    others = [a for a in authors if a != corr][:2]
    co = f'<span class="co">with {esc(", ".join(others))}{" et al." if len(authors) > 3 else ""}</span>' if others else ""
    lbl = p.get("corresponding_label", "Corresponding")
    if toc_img:
        fig = f'<img src="{toc_img}" alt="TOC graphic">'
        cap = '<span class="fig-no">TOC</span>Publisher graphic'
    else:
        fig = flow_svg(p.get("toc"), f"p{i}")
        cap = '<span class="fig-no">GRAPHICAL ABSTRACT</span>핵심 흐름 재구성 도식'
    doi = p.get("doi", "")
    link = f'<a class="link" href="https://doi.org/{esc(doi)}" target="_blank">Read the paper ↗</a>' if doi else ""
    doi_txt = f'<div class="fig-l" style="margin-top:1rem">DOI {esc(doi)}</div>' if doi else ""
    return f"""<article class="paper">
<div class="paper-meta"><span class="jr">{esc(p.get('journal', ''))}</span><span class="yr">{esc(p.get('year', ''))}</span>
<span class="if">Cited by {esc(p.get('cited_by', 0))}</span>{verified_badge(p.get('verified'))}</div>
<h3 class="art-title">{esc(p.get('title', ''))}</h3>
<div class="corr"><span class="lbl">{esc(lbl)}</span><span class="nm">{esc(corr)}</span><span class="af">{esc(p.get('affiliation', ''))}</span>{co}</div>
<figure class="toc"><div class="toc-box"><div class="inner">{fig}</div></div><figcaption>{cap}</figcaption></figure>
<div class="paper-body"><div>{points(p.get('points'))}</div>
<aside class="paper-aside"><div class="kicker" style="margin-bottom:1rem">Key Figures</div>{figs(p.get('key_figures'))}{doi_txt}{link}</aside></div>
{review(p.get('review'))}</article>"""


# ════════════════════════════════════════════════════════════════
#  IV. Lab table (brainstorm)
# ════════════════════════════════════════════════════════════════
def lab_table(b):
    b = b or {}
    cards = []
    for k, it in enumerate((b.get("ideas") or [])[:3]):
        rows = "".join(f"<dt>{lab}</dt><dd>{md(it.get(key, ''))}</dd>" for lab, key in
                       [("가설 · Hypothesis", "hypothesis"), ("왜 지금 · Why now", "why_now"),
                        ("첫 실험 · First experiment", "first_experiment"), ("리스크 · Risk", "risk")] if it.get(key))
        cards.append(f'<div class="idea"><div class="kicker">Idea {k + 1:02d}</div><h4>{md(it.get("title", ""))}</h4><dl>{rows}</dl></div>')
    qs = "".join(f"<li><span>{md(q)}</span></li>" for q in b.get("questions") or [])
    return f"""<div class="lab">
<div class="provocation"><div><div class="kicker">Today's Provocation</div><blockquote>{md(b.get('provocation', ''))}</blockquote></div>
<div class="prose">{md(b.get('context', ''))}</div></div>
<div class="ideas">{''.join(cards)}</div>
<div class="qs"><div class="kicker">Questions for the Team</div><ol>{qs}</ol></div></div>"""


# ════════════════════════════════════════════════════════════════
#  V. Daily study
# ════════════════════════════════════════════════════════════════
def _reading(k, r):
    acts = [verified_badge(r.get("verified"))]
    if r.get("doi"):
        acts.append(f'<a class="link" href="https://doi.org/{esc(r["doi"])}" target="_blank">DOI ↗</a>')
    by = " · ".join(x for x in [esc(r.get("authors", "")), esc(r.get("journal", "")), esc(r.get("year", ""))] if x)
    if r.get("cited_by"):
        by += f" · Cited by {r['cited_by']:,}"
    return f"""<div class="read-row"><div class="idx">{k + 1:02d}</div>
<div><span class="badge solid">{esc(r.get('type', 'Paper'))}</span><h5>{esc(r.get('title', ''))}</h5><div class="by">{by}</div><div class="acts">{''.join(acts)}</div></div>
<div class="focus"><span class="kicker">읽을 포인트</span>{md(r.get('focus', ''))}</div></div>"""


def _patent(k, p):
    num = p.get("number", "")
    acts = ['<span class="badge ok">✓ Google Patents</span>' if p.get("verified") else '<span class="badge">Unverified</span>']
    if num:
        acts.append(f'<a class="link" href="https://patents.google.com/patent/{esc(re.sub(r"[^A-Za-z0-9]", "", num))}" target="_blank">Open ↗</a>')
    by = " · ".join(x for x in [esc(p.get("assignee", "")), esc(p.get("year", ""))] if x)
    return f"""<div class="read-row"><div class="idx">{k + 1:02d}</div>
<div><span class="pat-no">{esc(num)}</span><h5>{esc(p.get('title', ''))}</h5><div class="by">{by}</div><div class="acts">{''.join(acts)}</div></div>
<div class="focus"><span class="kicker">핵심 청구 · 볼 포인트</span>{md(p.get('key_claim', ''))}</div></div>"""


def daily_study(s, day_no, total_days):
    s = s or {}
    c = s.get("concept") or {}
    eq = f'<div class="equation">{esc(c["equation"])}<small>{esc(c.get("equation_note", ""))}</small></div>' if c.get("equation") else ""
    if c.get("diagram"):
        dd = c["diagram"]
        diag = _frame(stack_svg(dd, "study"), 0, dd.get("title", "Cross-section"), dd.get("caption", ""), "Concept")
    elif c.get("curve"):
        cv = c["curve"]
        diag = _frame(curve_svg(cv, "study"), 0, cv.get("title", ""), cv.get("caption", ""), "Concept")
    else:
        diag = ""
    why = points(s.get("why_it_matters"))
    empty = '<div class="empty">검색 결과가 없어 오늘은 비워 둡니다. 확인되지 않은 자료는 싣지 않습니다.</div>'
    reads = "".join(_reading(k, r) for k, r in enumerate(s.get("readings") or [])) or empty
    pats = "".join(_patent(k, p) for k, p in enumerate(s.get("patents") or [])) or empty
    plan = "".join(f'<li><div class="t">{esc(p.get("time", ""))} &nbsp;·&nbsp; {esc(p.get("minutes", ""))} MIN</div><div class="d">{md(p.get("task", ""))}</div></li>'
                   for p in s.get("plan") or [])
    checks = "".join(f'<details class="check"><summary>{md(q.get("q", ""))}</summary><div>{md(q.get("a", ""))}</div></details>'
                     for q in s.get("self_check") or [])
    return f"""<div class="study">
<div class="study-head"><div class="day">Day<em>{day_no}</em>of {total_days}</div>
<div><div class="kicker">The Curriculum · CMP Fundamentals</div><h3>{md(s.get('theme', ''))}</h3>{why}</div></div>
<div class="concept"><div><div class="kicker">Key Concept</div><h3 class="art-title" style="margin-top:.7rem">{md(c.get('title', ''))}</h3>{eq}{points(c.get('points'))}</div>
<div>{diag}</div></div>
<div class="sub-k"><span>Reading List</span><span class="kicker">오늘 읽을 논문</span></div>{reads}
<div class="sub-k"><span>Patents to Study</span><span class="kicker">오늘 볼 특허</span></div>{pats}
<div class="study-grid"><div><div class="sub-k"><span>Study Plan</span><span class="kicker">하루 일정</span></div><ul class="plan">{plan}</ul></div>
<div><div class="sub-k"><span>Self-Check</span><span class="kicker">확인 문제</span></div>{checks}</div></div></div>"""


# ════════════════════════════════════════════════════════════════
#  Archive (사이드바 목록) · Notices
# ════════════════════════════════════════════════════════════════
def archive_nav(entries, current):
    if not entries:
        return '<div class="arch"><div class="arch-title">The Archive</div><div class="arch-empty">아직 발행된 호가 없습니다.</div></div>'
    rows, month = [], None
    for e in entries:
        m = e["date"][:7]
        if m != month:
            month = m
            y, mo = m.split("-")
            rows.append(f'<div class="arch-month">{["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][int(mo)]} {y}</div>')
        on = " on" if e["date"] == current else ""
        note = '<span class="arch-note" title="노트 있음">✎</span>' if e.get("has_note") else ""
        rows.append(f"""<a class="arch-item{on}" href="?d={e['date']}" target="_self">
<span class="arch-date">{e['date'][5:].replace('-', '.')} {note}</span>
<span class="arch-sum">{esc(e.get('summary') or e.get('theme', ''))}</span>
<span class="arch-theme">{esc(e.get('theme', ''))}</span></a>""")
    return f'<div class="arch"><div class="arch-title">The Archive</div><div class="arch-sub">연구 노트 · {len(entries)}호</div>{"".join(rows)}</div>'


def notices(items):
    if not items:
        return ""
    return '<div class="notices">' + "".join(f"<span>· {esc(n)}</span>" for n in items) + "</div>"


def viewing_banner(date_str, is_today):
    if is_today:
        return ""
    return f"""<div class="past-banner"><span class="kicker">Archive Edition</span>
<span>{esc(date_str.replace('-', '.'))} 호를 보고 있습니다</span><a class="link" href="?" target="_self">오늘 호로 ↗</a></div>"""


def locked_panel():
    return """<div class="locked"><div class="lock-mark">◆</div><div class="kicker">Private · 비공개</div>
<h4>연구 아이디어와 노트는 잠겨 있습니다</h4>
<p>왼쪽 사이드바 맨 아래 <b>Private Access</b>에 비밀번호를 입력하면 열립니다.</p></div>"""


# ════════════════════════════════════════════════════════════════
#  The Long Read · Referee's Note
# ════════════════════════════════════════════════════════════════
def longread(lr):
    lr = lr or {}
    paras = lr.get("paragraphs") or []
    if not paras:
        return ""
    body = []
    for k, p in enumerate(paras):
        body.append(f'<p class="lr-p{" dropcap" if k == 0 else ""}">{md(p)}</p>')
        if k == 1 and lr.get("pull_quote"):
            body.append(f'<blockquote class="lr-quote">{md(lr["pull_quote"])}</blockquote>')
    watch = "".join(f"<li>{md(w)}</li>" for w in lr.get("watch") or [])
    watch = f'<div class="lr-watch"><div class="kicker">What to Watch</div><ol>{watch}</ol></div>' if watch else ""
    mins = max(2, round(sum(len(p) for p in paras) / 500))
    return f"""<details class="longread"><summary><span class="lr-k">The Long Read · {mins} min</span>
<span class="lr-title">{md(lr.get('title', ''))}</span><span class="lr-more">Continue reading</span></summary>
<div class="lr-body"><p class="lr-dek">{md(lr.get('dek', ''))}</p>{''.join(body)}{watch}</div></details>"""


def review(rv):
    rv = rv or {}
    if not rv.get("verdict"):
        return ""
    li = lambda xs: "".join(f"<li>{md(x)}</li>" for x in xs or [])
    return f"""<div class="review"><div class="kicker">Referee's Note</div><p class="rv-verdict">{md(rv['verdict'])}</p>
<div class="rv-cols"><div><div class="rv-h">Strengths</div><ul>{li(rv.get('strengths'))}</ul></div>
<div><div class="rv-h">Limits · 의심할 점</div><ul>{li(rv.get('limits'))}</ul></div></div>
<div class="rv-us"><span class="kicker">For Our Lab</span><p>{md(rv.get('for_us', ''))}</p></div></div>"""
