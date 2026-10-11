# Morning Briefing — 설치 안내

매일 아침 05:40에 GitHub이 자동으로 그날 호를 만들고, Streamlit 웹앱이 어디서든 보여 줍니다.

| 구분 | 어디에 저장 | 누가 볼 수 있나 |
|---|---|---|
| 시황 · CMP 동향 · 뉴스 · 논문 · 공부 자료 | 공개 저장소 `morning-briefing` | 링크를 아는 누구나 |
| Lab Table 연구 아이디어 · 노트 · 폰트 | 비공개 저장소 `morning-briefing-private` | 나만 (앱에서 비밀번호 입력 후) |

처음 한 번만 아래 7단계를 따라 하면 됩니다. 30분 정도 걸립니다.

---

## 1. GitHub 가입

[github.com](https://github.com) 에서 가입합니다. 아래에서 `내아이디` 라고 쓴 곳에는 GitHub 아이디를 넣으세요.

## 2. 공개 저장소 만들기 — 코드와 공개 자료

1. 오른쪽 위 **+** → **New repository**
2. Repository name: `morning-briefing` / **Public** 선택 → **Create repository**
3. 화면의 **uploading an existing file** 링크를 클릭
4. 받은 `morning-briefing.zip` 의 압축을 풀고, 나온 `morning-briefing` 폴더 **안의 모든 것**을 끌어다 놓기
   (`.github`, `.streamlit` 같은 점(.) 폴더도 함께. 윈도우 탐색기에서 안 보이면 **보기 → 표시 → 숨긴 항목** 체크)
   - 폰트, `notes/`, `private/`, `.streamlit/secrets.toml` 은 들어 있지 않으니 따로 올리지 마세요.

5. 아래 **Commit changes** 클릭

## 3. 비공개 저장소 만들기 — 아이디어 · 노트 · 폰트

1. 다시 **+** → **New repository**
2. Repository name: `morning-briefing-private` / **Private** 선택 → **Create repository**
3. 탐색기에서 `fonts` 라는 폴더를 새로 만들고 KoPubWorld `.otf` 파일 6개를 넣기
4. 저장소 화면의 **uploading an existing file** → `fonts` **폴더째** 끌어다 놓기 → **Commit changes**

## 4. 비공개 저장소 열쇠(토큰) 만들기

앱과 자동 발행이 비공개 저장소에 아이디어를 쓰고 읽을 때 쓰는 열쇠입니다.

1. 오른쪽 위 프로필 사진 → **Settings** → 왼쪽 맨 아래 **Developer settings**
2. **Personal access tokens → Fine-grained tokens → Generate new token**
3. 설정
   - Token name: `morning-briefing`
   - Expiration: **1 year** 등 원하는 기간 (만료되면 같은 방법으로 새로 만들어 교체)
   - Repository access: **Only select repositories** → `morning-briefing-private` **하나만** 선택
   - Permissions → Repository permissions → **Contents: Read and write**
4. **Generate token** → `github_pat_...` 로 시작하는 값을 복사해 메모장에 잠시 보관 (다시 볼 수 없음)

## 5. 자동 발행 설정 (공개 저장소)

`morning-briefing` 저장소에서:

1. **Settings → Actions → General** → 맨 아래 *Workflow permissions* → **Read and write permissions** → Save
2. **Settings → Secrets and variables → Actions → New repository secret** 으로 하나씩 추가

| Name | Secret 값 |
|---|---|
| `GEMINI_API_KEY` | Gemini API 키 |
| `GEMINI_MODEL` | `gemini-3.8-flash` (쓰는 모델명) |
| `RESEARCH_FOCUS` | 예: `고제거율(RR)과 저결함(Defect)의 동시 달성` |
| `GH_PRIVATE_REPO` | `내아이디/morning-briefing-private` |
| `GH_TOKEN_PRIVATE` | 4단계에서 복사한 `github_pat_...` |

   여기 넣은 값은 저장소가 공개여도 **아무에게도 보이지 않습니다.**

3. **Actions** 탭 → 왼쪽 **Daily Edition** → **Run workflow** → 초록 버튼 → 2~4분 뒤 초록 체크가 뜨면 성공
   - `editions/` 폴더에 오늘 날짜 파일이 생기고, 비공개 저장소 `ideas/` 에 아이디어 파일이 생깁니다.
   - 빨간 X가 뜨면 클릭해서 오류 화면을 캡처해 주세요.

## 6. 웹앱 올리기 (Streamlit Community Cloud, 무료)

1. [share.streamlit.io](https://share.streamlit.io) → **Continue with GitHub** 로 로그인
2. **Create app → Deploy a public app from GitHub**
   - Repository: `내아이디/morning-briefing` / Branch: `main` / Main file path: `app.py`
   - App URL: 원하는 주소 (예: `yong-briefing`)
3. **Advanced settings → Secrets** 칸에 `secrets.toml.example` 내용을 붙여 넣고 값 채우기
   - `APP_PASSWORD` 는 나만 아는 새 비밀번호로
4. **Deploy** → 1~3분 뒤 앱이 열립니다

## 7. 사용하기

- 주소를 휴대폰·회사 PC 북마크에 저장해 두면 어디서든 볼 수 있습니다.
- 왼쪽 사이드바 맨 아래 **Private Access** 에 비밀번호를 넣으면 Lab Table, 노트, ✎ 표시가 열립니다.
- 노트의 **Save Notes** 를 누르면 비공개 저장소 `notes/날짜.md` 에 저장됩니다.
- 매일 05:40 무렵 새 호가 자동으로 쌓입니다. GitHub 사정으로 10~30분 늦을 수 있습니다.

---

### 자주 묻는 것

- **연구 초점을 바꾸고 싶어요** → 공개 저장소 Settings → Secrets 에서 `RESEARCH_FOCUS` 수정
- **오늘 호를 다시 만들고 싶어요** → Actions → Daily Edition → Run workflow (같은 날짜 파일을 덮어씀)
- **내 PC에서도 돌리고 싶어요** → 지금처럼 `streamlit run app.py`. 비밀 설정이 없으면 아이디어·노트는 PC의 `private/` 폴더에 저장되고, 잠금 없이 열립니다.
- **공개 범위 확인** → 공개 저장소에는 아이디어·노트·연구 초점·API 키·폰트가 없습니다. `editions/*.json` 을 열어 보면 `brainstorm` 항목이 없는 것을 확인할 수 있습니다.
