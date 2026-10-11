"""
Morning Briefing — 데이터 수집 · 편집 · 저장 파이프라인
Streamlit 없이도 실행됩니다:  python pipeline.py   (환경변수 GEMINI_API_KEY 필요)

원칙: 사실(뉴스·논문·특허·서지정보)은 모두 실제 검색 결과에서 가져오고,
      Gemini는 검색 결과를 '요약·해석'만 합니다. 목록에 없는 논문·특허는 만들 수 없습니다.
"""
import base64
import html
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests

import store

BASE = Path(__file__).parent
EDITIONS = BASE / "editions"
KST = ZoneInfo("Asia/Seoul")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}

COMPANIES = [  # 표시명, 티커, 통화, 로고용 도메인
    ("TSMC", "TSM", "$", "tsmc.com"),
    ("ASML", "ASML", "$", "asml.com"),
    ("Intel", "INTC", "$", "intel.com"),
    ("SK Hynix", "000660.KS", "₩", "skhynix.com"),
    ("Samsung", "005930.KS", "₩", "samsung.com"),
    ("AMAT", "AMAT", "$", "appliedmaterials.com"),
]

# (한글 주제, 논문 검색어, 특허 검색어)
SYLLABUS = [
    ("Preston 방정식과 제거율 모델링", "Preston equation material removal rate chemical mechanical polishing", "chemical mechanical polishing removal rate model"),
    ("실리카 연마입자: 합성·입도·분산", "colloidal silica abrasive chemical mechanical polishing", "colloidal silica polishing slurry"),
    ("세리아 연마입자의 chemical tooth 메커니즘", "ceria abrasive chemical tooth polishing mechanism", "ceria polishing slurry"),
    ("STI CMP와 고선택비 첨가제", "shallow trench isolation CMP selectivity additive ceria", "shallow trench isolation polishing composition selectivity"),
    ("Cu CMP: 산화제·착화제·부식억제제", "copper chemical mechanical polishing inhibitor complexing agent", "copper polishing composition corrosion inhibitor"),
    ("배리어(Ta/TaN, Co, Ru) CMP", "barrier layer CMP tantalum cobalt ruthenium slurry", "barrier polishing slurry tantalum"),
    ("W CMP와 Fe 촉매 화학", "tungsten chemical mechanical polishing iron catalyst", "tungsten polishing composition iron"),
    ("패드 소재·컨디셔닝과 표면 거칠기", "CMP pad conditioning surface roughness polyurethane", "chemical mechanical polishing pad"),
    ("마이크로 스크래치 결함의 생성 기전", "CMP scratch defect formation mechanism", "polishing slurry scratch reduction"),
    ("디싱·이로전과 패턴 밀도 효과", "CMP dishing erosion pattern density", "polishing dishing erosion"),
    ("제타전위와 콜로이드 안정성 (DLVO)", "zeta potential slurry stability CMP abrasive", "polishing slurry dispersion stability"),
    ("Post-CMP 세정과 잔류 입자 제거", "post-CMP cleaning particle removal", "post chemical mechanical polishing cleaning composition"),
    ("엔드포인트 검출: 광학·마찰·와전류", "CMP endpoint detection", "chemical mechanical polishing endpoint detection"),
    ("하이브리드 본딩용 Cu/유전체 CMP", "hybrid bonding copper CMP dielectric recess", "hybrid bonding polishing copper"),
    ("Low-k·SiCN 유전체 CMP", "low-k dielectric chemical mechanical polishing", "low-k dielectric polishing composition"),
    ("연마입자 응집과 대형입자(LPC) 관리", "large particle count CMP slurry agglomeration", "polishing slurry large particles filtration"),
    ("트라이볼로지: Stribeck 곡선과 윤활 영역", "Stribeck curve chemical mechanical polishing tribology", "polishing friction lubrication pad"),
    ("계면활성제·고분자 첨가제의 흡착 거동", "polymer additive adsorption CMP slurry surfactant", "polishing composition polymer additive"),
    ("Mo·Ru 등 차세대 배선 금속 CMP", "molybdenum ruthenium chemical mechanical polishing interconnect", "molybdenum polishing composition"),
    ("CMP 공정 모니터링과 가상 계측(VM)", "virtual metrology chemical mechanical polishing machine learning", "chemical mechanical polishing monitoring machine learning"),
    ("SiC·GaN 화합물 반도체 CMP", "silicon carbide chemical mechanical polishing", "silicon carbide polishing slurry"),
    ("슬러리 여과·공급 시스템과 품질 관리", "CMP slurry filtration delivery", "polishing slurry filter supply"),
]

NEWS_QUERIES = [
    ('"CMP slurry" OR "CMP pad" OR "CMP consumables"', "en"),
    ('"chemical mechanical planarization" OR "chemical mechanical polishing" semiconductor', "en"),
    ('"hybrid bonding" CMP OR "backside power" CMP', "en"),
    ("CMP 슬러리 OR CMP 패드", "ko"),
    ("반도체 CMP 공정", "ko"),
]

PAPER_QUERIES = [
    "chemical mechanical polishing slurry abrasive",
    "chemical mechanical planarization nanoparticle",
    "CMP slurry ceria silica defect removal rate",
]


# ════════════════════════════════════════════════════════════════
#  공통
# ════════════════════════════════════════════════════════════════
def clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", str(s or ""))).strip()


def _get(url, **kw):
    kw.setdefault("timeout", 15)
    kw.setdefault("headers", UA)
    return requests.get(url, **kw)


def data_uri(content: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(content).decode()}"


def logo_uri(name: str, domain: str):
    """1순위: logos/ 폴더의 공식 로고 파일 → 2순위: 웹 아이콘"""
    key = re.sub(r"[^a-z0-9]", "", name.lower())
    for ext, mime in (("svg", "image/svg+xml"), ("png", "image/png"), ("webp", "image/webp"), ("jpg", "image/jpeg")):
        f = BASE / "logos" / f"{key}.{ext}"
        if f.exists():
            return data_uri(f.read_bytes(), mime)
    try:
        r = _get(f"https://www.google.com/s2/favicons?domain={domain}&sz=256", timeout=6)
        if r.status_code == 200 and len(r.content) > 300:
            return data_uri(r.content, r.headers.get("Content-Type", "image/png"))
    except Exception:
        pass
    return None


# ════════════════════════════════════════════════════════════════
#  1) 주가
# ════════════════════════════════════════════════════════════════
def fetch_stocks():
    import yfinance as yf
    rows = []
    for name, tk, cur, _ in COMPANIES:
        try:
            t = yf.Ticker(tk)
            hist = t.history(period="5d")
            if len(hist) >= 2:
                c, p = hist["Close"].iloc[-1], hist["Close"].iloc[-2]
                rows.append({"name": name, "code": tk.split(".")[0], "price": float(c),
                             "chg": float((c - p) / p * 100), "cap": (t.info.get("marketCap") or 0) / 1e9, "cur": cur})
        except Exception:
            pass
    return rows


# ════════════════════════════════════════════════════════════════
#  2) 뉴스 — Google News RSS (최근 14일)
# ════════════════════════════════════════════════════════════════
def fetch_news(max_items=24):
    out, seen = [], set()
    for q, lang in NEWS_QUERIES:
        loc = "hl=ko&gl=KR&ceid=KR:ko" if lang == "ko" else "hl=en-US&gl=US&ceid=US:en"
        try:
            r = _get(f"https://news.google.com/rss/search?q={quote(q + ' when:14d')}&{loc}")
            root = ET.fromstring(r.content)
        except Exception:
            continue
        for it in root.iter("item"):
            title = clean(it.findtext("title"))
            src = clean(it.findtext("source"))
            if src and title.endswith(" - " + src):
                title = title[: -len(src) - 3]
            key = re.sub(r"\W+", "", title.lower())[:60]
            if not title or key in seen:
                continue
            seen.add(key)
            try:
                dt = parsedate_to_datetime(it.findtext("pubDate")).astimezone(KST)
            except Exception:
                dt = None
            out.append({"title": title, "source": src, "link": it.findtext("link") or "",
                        "date": dt.strftime("%Y-%m-%d") if dt else "", "lang": lang})
    out.sort(key=lambda n: n["date"], reverse=True)
    return out[:max_items]


# ════════════════════════════════════════════════════════════════
#  3) 논문 — OpenAlex (실존 논문만, 교신저자·소속·피인용수 포함)
# ════════════════════════════════════════════════════════════════
def _abstract(inv):
    if not inv:
        return ""
    pos = sorted((i, w) for w, idx in inv.items() for i in idx)
    return " ".join(w for _, w in pos)


def _work(w):
    auths = w.get("authorships") or []
    names = [a["author"]["display_name"] for a in auths if a.get("author")]
    corr = next((a for a in auths if a.get("is_corresponding")), None)
    label = "Corresponding"
    if not corr and auths:
        corr, label = auths[-1], "Senior Author"
    inst = ((corr or {}).get("institutions") or [{}])
    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "")
    return {
        "title": clean(w.get("title") or w.get("display_name")),
        "journal": src, "year": str(w.get("publication_year") or ""),
        "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
        "authors_list": names,
        "corresponding_display": (corr or {}).get("author", {}).get("display_name", ""),
        "corresponding_label": label,
        "affiliation": inst[0].get("display_name", "") if inst else "",
        "cited_by": w.get("cited_by_count", 0),
        "abstract": _abstract(w.get("abstract_inverted_index"))[:1800],
        "openalex": w.get("id", ""), "verified": True,
    }


ERRORS = []  # 검색 실패 이유 (Actions 로그와 notices에 표시)


def openalex(search, filt="", sort="relevance_score:desc", n=15):
    """OpenAlex 검색. 실패하면 이유를 ERRORS에 남기고, 429(사용량 초과)면 잠시 쉬었다 한 번 재시도"""
    import time
    p = {"search": search, "per-page": n, "sort": sort}
    if filt:
        p["filter"] = filt
    key = store.cfg("OPENALEX_API_KEY")
    if key:
        p["api_key"] = key
    for attempt in range(2):
        try:
            r = _get("https://api.openalex.org/works", params=p, timeout=25)
            if r.status_code == 429 and attempt == 0:
                time.sleep(5)
                continue
            if r.status_code != 200:
                ERRORS.append(f"OpenAlex {r.status_code}: {r.text[:120]}")
                return []
            return [_work(w) for w in r.json().get("results", []) if w.get("title")]
        except Exception as e:
            ERRORS.append(f"OpenAlex 오류: {type(e).__name__} {str(e)[:100]}")
            return []
    ERRORS.append("OpenAlex 429: 사용량 한도 초과")
    return []


def past_dois(exclude_date=""):
    seen = set()
    for f in EDITIONS.glob("*.json"):
        if f.stem == exclude_date:
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            for p in d.get("data", {}).get("papers", []) + d.get("data", {}).get("study", {}).get("readings", []):
                if p.get("doi"):
                    seen.add(p["doi"].lower())
        except Exception:
            pass
    return seen


def pick_papers(today, k=2):
    since = (today - timedelta(days=540)).strftime("%Y-%m-%d")
    seen, pool, keys = past_dois(today.strftime("%Y-%m-%d")), [], set()
    for q in PAPER_QUERIES:
        for w in openalex(q, f"from_publication_date:{since},has_abstract:true,type:article", n=25):
            key = (w["doi"] or w["title"]).lower()
            if key not in keys and key not in seen and len(w["abstract"]) > 300:
                keys.add(key)
                pool.append(w)
    if not pool:  # 2차: 기간 3년, 초록 필터 없이 넓혀서 다시
        since3 = (today - timedelta(days=3 * 365)).strftime("%Y-%m-%d")
        for w in openalex("chemical mechanical polishing", f"from_publication_date:{since3}", n=40):
            key = (w["doi"] or w["title"]).lower()
            if key not in keys and key not in seen and len(w["abstract"]) > 200:
                keys.add(key)
                pool.append(w)
    if not pool:
        return []
    start = today.timetuple().tm_yday % len(pool)
    return (pool[start:] + pool[:start])[:k]


def pick_readings(query):
    three_y = (datetime.now(KST) - timedelta(days=3 * 365)).strftime("%Y-%m-%d")
    picks, keys = [], set()
    for label, filt, sort in (("Seminal", "", "cited_by_count:desc"),
                              ("Review", "type:review", "cited_by_count:desc"),
                              ("Recent", f"from_publication_date:{three_y},has_abstract:true", "relevance_score:desc")):
        for w in openalex(query, filt, sort, n=6):
            key = (w["doi"] or w["title"]).lower()
            if key not in keys:
                keys.add(key)
                w["type"] = label
                w["authors"] = (w["authors_list"][0] + (" et al." if len(w["authors_list"]) > 1 else "")) if w["authors_list"] else ""
                picks.append(w)
                break
    return picks


# ════════════════════════════════════════════════════════════════
#  4) 특허 — Google Patents 검색 (비공식 엔드포인트, 실패하면 빈 목록)
# ════════════════════════════════════════════════════════════════
def search_patents(query, k=2):
    inner = f"q=({query})&num=20&type=PATENT"
    try:
        r = _get(f"https://patents.google.com/xhr/query?url={quote(inner, safe='')}&exp=")
        if r.status_code != 200:
            ERRORS.append(f"Google Patents {r.status_code}")
            return []
        j = r.json()
    except Exception as e:
        ERRORS.append(f"Google Patents 오류: {type(e).__name__}")
        return []
    res, owners = [], set()
    for cl in (j.get("results") or {}).get("cluster", []):
        for it in cl.get("result", []):
            p = it.get("patent") or {}
            num = p.get("publication_number", "")
            owner = clean(p.get("assignee"))
            if not num or owner in owners:
                continue
            owners.add(owner)
            res.append({"number": num, "title": clean(p.get("title")), "assignee": owner,
                        "year": (p.get("priority_date") or p.get("publication_date") or "")[:4],
                        "snippet": clean(p.get("snippet"))[:900], "verified": True})
    # 최근 출원 우선
    res.sort(key=lambda x: x["year"], reverse=True)
    return res[:k]


# ════════════════════════════════════════════════════════════════
#  5) TOC 이미지 — 출판사 og:image 시도 (막히면 None)
# ════════════════════════════════════════════════════════════════
def toc_image(doi):
    if not doi:
        return None
    try:
        r = _get(f"https://doi.org/{doi}", timeout=10, allow_redirects=True)
        m = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', r.text) or \
            re.search(r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"', r.text)
        if not m:
            return None
        img = _get(m.group(1), timeout=10)
        ctype = img.headers.get("Content-Type", "")
        if img.status_code == 200 and ctype.startswith("image/") and 2_000 < len(img.content) < 3_000_000:
            return data_uri(img.content, ctype.split(";")[0])
    except Exception:
        pass
    return None


# ════════════════════════════════════════════════════════════════
#  6) Gemini 편집
# ════════════════════════════════════════════════════════════════
SCHEMA = r"""
{
  "edition_summary": "오늘 호를 한 줄로 (25자 이내, 아카이브 목록에 표시됨)",
  "market_insight": {"headline": "25자 내외 헤드라인", "bullets": ["**핵심어** — 설명, 핵심 구절 ==밑줄== (3~4개)"],
                     "longread": {"title": "장문 제목", "dek": "부제 한 문장", "paragraphs": ["문단 4~6개, 각 3~5문장"], "pull_quote": "가장 날카로운 한 문장", "watch": ["앞으로 지켜볼 신호 3개"]}},
  "industry_needs": [{"need": "업계가 원하는 것 (20자 이내)", "pain": "현장의 고민 한 줄", "refs": [3, 7]}],
  "cmp_tech": [{
    "tag": "분류 2~3단어", "title": "제목, 핵심어 **굵게**", "lede": "한 문장 요약",
    "points": [{"label": "배경|핵심 기술|효과|시사점", "text": "개조식 한 줄"}],
    "key_figures": [{"value": "≤ 0.5 nm", "label": "Dishing"}],
    "refs": [1, 4],
    "players": [{"name": "회사명", "role": "슬러리|패드|장비|소자|소재", "activity": "이 주제와 관련된 활동 한 줄", "refs": [4]}],
    "longread": {"title": "장문 제목", "dek": "부제 한 문장", "paragraphs": ["문단 4~6개, 각 3~5문장"], "pull_quote": "가장 날카로운 한 문장", "watch": ["앞으로 지켜볼 신호 3개"]},
    "diagram": {"title": "도식 제목", "abrasive": "연마입자", "pad": "패드", "polish_stop_after": 1,
      "layers": [{"name": "층 이름 12자 이내", "material": "Cu|TaN|SiO2|SiN|SiCN|low-k|W|Co|Ru|Mo|poly-Si|Si", "role": "역할 10자 이내", "thickness": 1.0, "remove": true},
                 {"name": "Cu 배선", "material": "Cu", "host": "SiO2", "pattern": "inlaid", "dishing": true, "role": "배선", "thickness": 1.5}],
      "caption": "그림 설명 한 문장, **굵게**"}
  }],
  "papers": [{"ref": "P1", "toc": {"problem": "15자", "approach": "20자", "outcome": "15자", "outcome_figure": "대표 수치"},
              "points": [{"label": "문제|접근|결과|시사점", "text": "개조식 한 줄"}],
              "key_figures": [{"value": "수치", "label": "의미"}],
              "review": {"verdict": "심사위원의 한 줄 평", "strengths": ["강점 2~3개"], "limits": ["한계·빠진 대조군·의심할 점 2~3개"],
                         "for_us": "우리 슬러리 연구에 옮긴다면 무엇을, 어떤 조건에서 먼저 검증할지 3~4문장"}}],
  "brainstorm": {"provocation": "도발적 질문", "context": "2문장",
                 "ideas": [{"title": "", "hypothesis": "", "why_now": "", "first_experiment": "", "risk": ""}],
                 "questions": ["팀 토론 질문"]},
  "study": {
    "why_it_matters": [{"label": "왜|연결", "text": "개조식 한 줄"}],
    "concept": {"title": "", "equation": "", "equation_note": "", "points": [{"label": "의미|한계|확장", "text": ""}],
                "curve": {"title": "", "shape": "linear|saturating|sigmoid|decreasing|valley|peak|threshold", "x_label": "", "y_label": "",
                          "regions": [{"from": 0.0, "to": 0.3, "label": "10자 이내"}], "marks": [{"at": 0.5, "label": "12자 이내"}], "caption": ""},
                "diagram": null},
    "readings": [{"ref": "R1", "focus": "읽을 때 볼 포인트, **굵게**"}],
    "patents": [{"ref": "T1", "key_claim": "핵심 청구 구조와 볼 포인트"}],
    "plan": [{"time": "08:30", "minutes": 20, "task": "구체적 학습 행동"}],
    "self_check": [{"q": "", "a": ""}]
  }
}"""


def build_prompt(rows, news, papers, readings, patents, focus, theme):
    news_txt = "\n".join(f"[{i + 1}] ({n['date']}, {n['source']}) {n['title']}" for i, n in enumerate(news)) or "없음"
    pap_txt = "\n\n".join(f"[P{i + 1}] {p['title']} ({p['journal']}, {p['year']})\nAbstract: {p['abstract']}" for i, p in enumerate(papers)) or "없음"
    rd_txt = "\n\n".join(f"[R{i + 1}] ({r['type']}) {r['title']} ({r['journal']}, {r['year']})\nAbstract: {r['abstract'][:900] or '초록 없음'}" for i, r in enumerate(readings)) or "없음"
    pt_txt = "\n\n".join(f"[T{i + 1}] {p['number']} / {p['assignee']} / {p['title']}\n요약: {p['snippet']}" for i, p in enumerate(patents)) or "없음"
    stock_txt = "\n".join(f"{r['name']}: {r['chg']:+.2f}%" for r in rows) or "없음"
    return f"""
당신은 반도체 CMP 분야의 세계 최고 분석가이자 하이엔드 매거진 에디터이며, 신입 연구원을 키우는 수석 연구위원입니다.
독자: KC Tech CMP 슬러리 R&D팀 연구원. 아래 [자료]만 근거로, JSON 스키마를 정확히 따라 한국어로 작성하세요.

[절대 규칙]
- 사실 정보는 [자료]에 있는 것만 사용. 자료에 없는 수치·기업 활동·논문·특허를 만들어 내지 마세요.
- refs에는 근거가 된 뉴스 번호를 넣으세요. 근거가 없으면 빈 배열.
- papers는 [P1]~ 각각에 대해 하나씩, 초록 내용만으로 작성 (ref 값 유지). 초록에 없는 수치는 key_figures에 넣지 마세요.
- study.readings는 [R1]~ 각각에, study.patents는 [T1]~ 각각에 하나씩 대응.
- players는 뉴스 근거가 있거나, 그 기업의 공개된 주력 사업으로 널리 알려진 경우만. 활동 문장은 보수적으로.

[문체 — The Heisenberg Report 수준의 깊이]
- 컨센서스를 옮겨 적지 말 것. 매 꼭지마다 "시장(또는 업계)이 무엇을 놓치고 있는가"를 묻는다.
- 1차 효과에서 멈추지 말고 2차·3차 효과까지 사슬로 잇는다.
  예: HBM 적층 수 증가 → 웨이퍼당 CMP 스텝 증가 → 세리아 수요와 결함 허용치의 동시 압박 → 슬러리 업체의 가격 결정력.
- 거시(금리·환율·capex 사이클) ↔ 산업(파운드리·메모리·장비) ↔ 소재 과학(계면 화학, 트라이볼로지, 콜로이드)을 한 흐름으로 연결.
- 메커니즘은 물리·화학 수준까지 내려간다: 왜 그런지를 반응식, 에너지 장벽, 속도론, 접촉역학으로 설명.
- 단정 대신 조건과 확률로 말하고, 반대 시나리오(무엇이 틀리면 이 논지가 깨지는가)를 반드시 함께 쓴다.
- 문장은 밀도 있고 절제된 문어체. "혁신적", "게임 체인저", "주목된다", "~할 것으로 보인다" 같은 상투어와 번역투, 하이픈으로 붙인 복합 형용사 금지.
- 사실(수치·기업 활동·논문 결과)은 [자료]에 있는 것만. 해석과 추론은 자유롭게 하되 사실처럼 꾸미지 말 것.
- 문체 예시: "메모리 3사의 동반 약세를 수요 둔화로 읽는 것은 절반만 맞다. 증설 속도가 늦춰지는 동안 적층 수는 오히려 늘고 있고,
  이는 웨이퍼 한 장이 통과해야 하는 평탄화 스텝이 늘어난다는 뜻이다. 장비 주문은 줄어도 소모품의 시간은 줄지 않는다."

[작성 규칙]
- bullets·points 같은 요약층은 개조식 한 줄(60자 이내). 깊이는 longread와 review에서 충분히 펼칠 것.
- longread는 market_insight 1편, cmp_tech 각 1편. 문단마다 하나의 논점, 마지막 문단은 반대 시나리오. 가장 중요한 구절 ==밑줄==, 핵심 용어 **굵게** (항목당 각 1회 이하).
- industry_needs 3건, cmp_tech 2건(각 players 2~4개), ideas 3건, questions 3건, plan 3단계, self_check 3문항.
- cmp_tech.diagram.layers: 위(연마면)→아래(기판) 3~5층, 제거되는 층 remove: true, 배선층은 pattern "inlaid"+host, polish_stop_after는 연마가 멈추는 층 인덱스.
- brainstorm은 이 연구 초점에 맞춰: "{focus}"
- study는 오늘의 공부 주제 "{theme}"에 대해 작성하고, concept.curve로 핵심 관계를 그래프화.

[자료 1: 주가 등락]
{stock_txt}

[자료 2: 최근 14일 CMP 관련 뉴스]
{news_txt}

[자료 3: 오늘의 논문 (OpenAlex)]
{pap_txt}

[자료 4: 오늘 공부할 문헌]
{rd_txt}

[자료 5: 오늘 공부할 특허]
{pt_txt}

[JSON 스키마]
{SCHEMA}

오직 JSON만 출력하세요.
"""


def call_gemini(api_key, model_name, prompt):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
    raw = model.generate_content(prompt).text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)


def _merge(found, written, prefix):
    """검색 결과(사실)에 Gemini의 요약을 ref로 결합. 사실 필드는 검색 결과가 우선"""
    by_ref = {str(w.get("ref", "")).upper(): w for w in written or []}
    out = []
    for i, f in enumerate(found):
        w = by_ref.get(f"{prefix}{i + 1}") or (written[i] if written and i < len(written) else {})
        merged = {**{k: v for k, v in w.items() if k != "ref"}, **f}
        merged.pop("abstract", None)
        merged.pop("snippet", None)
        out.append(merged)
    return out


# ════════════════════════════════════════════════════════════════
#  7) 전체 실행 · 저장 · 목록
# ════════════════════════════════════════════════════════════════
def theme_for(date):
    return SYLLABUS[date.timetuple().tm_yday % len(SYLLABUS)]


def build_edition(api_key, model_name="gemini-3.8-flash", focus=None, theme=None, log=print):
    now = datetime.now(KST)
    focus = focus or store.cfg("RESEARCH_FOCUS") or "CMP 슬러리의 성능과 결함의 균형"
    theme = theme or theme_for(now)
    ko, paper_q, patent_q = theme
    notices = []

    log("주가를 불러오는 중")
    rows = fetch_stocks()
    log("CMP 뉴스를 검색하는 중")
    news = fetch_news()
    if not news:
        notices.append("뉴스 검색 결과를 가져오지 못했습니다.")
    log("논문을 검색하는 중 (OpenAlex)")
    papers = pick_papers(now)
    readings = pick_readings(paper_q)
    if not papers:
        notices.append("오늘의 논문 검색 결과가 없습니다." + (f" ({ERRORS[-1]})" if ERRORS else ""))
    log("특허를 검색하는 중 (Google Patents)")
    patents = search_patents(patent_q)
    if not patents:
        notices.append("특허 검색에 실패했습니다." + (f" ({ERRORS[-1]})" if ERRORS else ""))

    log("Gemini가 편집하는 중")
    data = call_gemini(api_key, model_name, build_prompt(rows, news, papers, readings, patents, focus, ko))

    data["papers"] = _merge(papers, data.get("papers"), "P")
    study = data.setdefault("study", {})
    study["theme"] = ko
    study["readings"] = _merge(readings, study.get("readings"), "R")
    study["patents"] = _merge(patents, study.get("patents"), "T")
    data["news"] = news

    log("TOC 그래픽을 찾는 중")
    tocs = [toc_image(p.get("doi")) for p in data["papers"]]

    # ── 공개/비공개 분리: 연구 아이디어는 비공개 저장소로만 ──
    date = now.strftime("%Y-%m-%d")
    brainstorm = data.pop("brainstorm", {})
    log("연구 아이디어를 비공개 저장소에 보관하는 중")
    store.write(f"ideas/{date}.json", json.dumps(brainstorm, ensure_ascii=False, indent=1), f"ideas {date}")

    ed = {"date": date, "generated_at": now.isoformat(timespec="minutes"),
          "summary": data.get("edition_summary", ""), "theme": ko,
          "day": SYLLABUS.index(theme) + 1, "total_days": len(SYLLABUS),
          "rows": rows, "tocs": tocs, "notices": notices, "data": data}
    save_edition(ed)
    return ed


def save_edition(ed):
    EDITIONS.mkdir(exist_ok=True)
    (EDITIONS / f"{ed['date']}.json").write_text(json.dumps(ed, ensure_ascii=False, indent=1), encoding="utf-8")


def load_edition(date_str):
    f = EDITIONS / f"{date_str}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    repo = store.cfg("PUBLIC_REPO")  # 앱이 아직 최신 커밋을 못 받았을 때 GitHub에서 직접
    if repo:
        try:
            r = _get(f"https://raw.githubusercontent.com/{repo}/main/editions/{date_str}.json", timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
    return None


def list_editions():
    items = []
    for f in sorted(EDITIONS.glob("*.json"), reverse=True):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            items.append({"date": d.get("date", f.stem), "summary": d.get("summary", ""), "theme": d.get("theme", "")})
        except Exception:
            pass
    return items


if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("환경변수 GEMINI_API_KEY 를 설정하세요.")
    ed = build_edition(key, os.environ.get("GEMINI_MODEL") or "gemini-3.8-flash")
    print("saved:", EDITIONS / f"{ed['date']}.json", "|", ed["summary"])
    for n in ed["notices"]:
        print("notice:", n)
    for e in dict.fromkeys(ERRORS):
        print("search error:", e)
