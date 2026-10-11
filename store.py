"""
비공개 저장소 — 연구 아이디어(ideas/), 노트(notes/), 폰트(fonts/)

· GH_PRIVATE_REPO 와 GH_TOKEN_PRIVATE 가 설정되어 있으면 → 비공개 GitHub 저장소에 읽고 씀
· 설정이 없으면 → 이 폴더 안의 private/ 에 저장 (내 PC에서 쓸 때)
"""
import base64
import os
from pathlib import Path

import requests

BASE = Path(__file__).parent
LOCAL = BASE / "private"
API = "https://api.github.com"


def cfg(name, default=""):
    """환경변수 → Streamlit secrets 순서로 설정값을 찾음"""
    v = os.environ.get(name)
    if v:
        return v
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


def _remote():
    repo, token = cfg("GH_PRIVATE_REPO"), cfg("GH_TOKEN_PRIVATE")
    return (repo, token) if repo and token else (None, None)


def _headers(token, raw=False):
    return {"Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github.raw+json" if raw else "application/vnd.github+json"}


def mode():
    return "github" if _remote()[0] else "local"


def read(path):
    """텍스트 파일 읽기. 없으면 None"""
    repo, token = _remote()
    if not repo:
        f = LOCAL / path
        return f.read_text(encoding="utf-8") if f.exists() else None
    r = requests.get(f"{API}/repos/{repo}/contents/{path}", headers=_headers(token, raw=True), timeout=15)
    return r.content.decode("utf-8") if r.status_code == 200 else None


def read_bytes(path):
    repo, token = _remote()
    if not repo:
        f = LOCAL / path
        return f.read_bytes() if f.exists() else None
    r = requests.get(f"{API}/repos/{repo}/contents/{path}", headers=_headers(token, raw=True), timeout=60)
    return r.content if r.status_code == 200 else None


def write(path, text, message=None):
    repo, token = _remote()
    if not repo:
        f = LOCAL / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
        return True
    url = f"{API}/repos/{repo}/contents/{path}"
    cur = requests.get(url, headers=_headers(token), timeout=15)
    body = {"message": message or f"update {path}", "content": base64.b64encode(text.encode("utf-8")).decode()}
    if cur.status_code == 200:
        body["sha"] = cur.json().get("sha")
    r = requests.put(url, headers=_headers(token), json=body, timeout=20)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"비공개 저장소 저장 실패 ({r.status_code}): {r.text[:200]}")
    return True


def listdir(folder):
    """폴더 안 파일 이름 목록"""
    repo, token = _remote()
    if not repo:
        d = LOCAL / folder
        return sorted(p.name for p in d.glob("*") if p.is_file()) if d.exists() else []
    r = requests.get(f"{API}/repos/{repo}/contents/{folder}", headers=_headers(token), timeout=15)
    return sorted(i["name"] for i in r.json() if i.get("type") == "file") if r.status_code == 200 else []


def sync_fonts(dest):
    """비공개 저장소 fonts/ 의 KoPub 폰트를 static/ 으로 내려받음 (이미 있으면 건너뜀)"""
    dest = Path(dest)
    if mode() != "github":
        return
    dest.mkdir(exist_ok=True)
    for name in listdir("fonts"):
        target = dest / name
        if not target.exists() and name.lower().endswith((".otf", ".ttf", ".woff", ".woff2")):
            data = read_bytes(f"fonts/{name}")
            if data:
                target.write_bytes(data)
