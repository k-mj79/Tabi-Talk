# 타비톡 (旅トーク, Tabi Talk)

> 일본을 여행하는 배낭족을 위한 **일본어 회화 RAG 챗봇**
> 한국어로 물어보면 일본어 문장 · 발음 · 일본인의 예상 답변까지 바로 알려줍니다.

## 1. 프로젝트 소개

일본어 초보 여행자가 현지에서 필요한 문장을 빠르게 익히고, 실제 일본인에게 들을 만한 답변까지 미리 접해 볼 수 있도록 만든 웹 챗봇입니다.
LangChain 기반 RAG(검색 증강 생성) 파이프라인으로 여행 회화 문구 문서를 검색해 답변에 활용하며, 화면은 ChatGPT와 비슷한 대화형 UI입니다.

- **대상 사용자**: 일본 여행 중인 일본어 초보 배낭여행자
- **핵심 가치**: 질문 한 번으로 "말할 문장 + 발음 + 들을 문장" 확보

## 2. 주요 기능

| 기능 | 설명 |
|---|---|
| 일본어 번역 | 질문을 현장에서 바로 쓸 수 있는 정중한 일본어 한 문장으로 번역 (히라가나 읽기, 한글 발음 포함) |
| 예상 답변 5개 | 일본인이 답할 만한 유형을 일본어 · 한글 발음 · 한글 번역으로 제공 (듣기 연습) |
| 추천 문구 3~5개 | 같은 상황에서 함께 쓰면 좋은 연관 문구 |
| 발음 듣기 | 모든 문장의 🔊 버튼으로 브라우저 TTS 일본어 음성 재생 |
| 세션 기억 | 대화 세션이 저장되어 사이드바에서 과거 대화를 다시 열람·삭제 |
| 맥락 유지 | 같은 세션의 최근 대화를 반영해 후속 질문에 답변 |
| 반응형 · 다크모드 | 모바일 햄버거 메뉴, 시스템 라이트/다크 모드 자동 적용 |

## 3. 출력 예시

**질문**: 교토 A 호텔로 이동하려면 어느 전철역에서 내려야 하나요?

1. **번역 문장**: 일본어 번역 1문장 + 히라가나 읽기 + 한글 발음
2. **예상 답변 5개**: 일본인이 답할 수 있는 문장 (일본어 / 한글 발음 / 한글 번역)
3. **추천 문구 3~5개**: 연관 표현 (일본어 / 한글 발음 / 한글 번역)

## 4. 기술 스택

| 구분 | 사용 기술 |
|---|---|
| 백엔드 | FastAPI, Uvicorn |
| RAG | LangChain (LCEL), FAISS, OpenAI Embeddings |
| LLM | OpenAI Chat 모델 (기본 `gpt-4o-mini`) |
| 저장소 | SQLite (세션·메시지), FAISS 로컬 인덱스 |
| 프론트엔드 | HTML / CSS / JavaScript (빌드 없음) |
| 환경 | Python 3.11, Anaconda |

## 5. 프로젝트 구조

```
.
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI 서버, 세션 API, 정적 파일 서빙
│   └── rag.py             # 인덱스 생성, 리트리버, LangChain 체인
├── data/                  # RAG 지식 문서 (pdf / md / txt)
│   ├── basic_phrases.md   # 기본 여행 회화
│   └── travel_phrases.md  # 교통·숙소·길찾기·식당·응급 문구
├── static/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── .env                   # API 키 (깃에 올리지 않기)
├── requirements.txt
├── index/                 # (자동 생성) FAISS 인덱스
└── chat.db                # (자동 생성) 대화 기록
```

## 6. 챗봇 구조

```
[브라우저] ──질문──▶ [FastAPI /api/sessions/{id}/chat]
                          │
                          ├─ 1) DB에서 최근 6개 메시지 조회 (대화 기록)
                          ├─ 2) FAISS 리트리버로 유사 문구 Top-4 검색
                          ├─ 3) 프롬프트 | LLM | JsonOutputParser
                          └─ 4) 질문·답변 DB 저장 후 JSON 반환
[브라우저] ◀─ 번역 / 예상 답변 5개 / 추천 문구 렌더링
```

### LangChain 체인 구성

`prompt | llm | JsonOutputParser()` 형태의 LCEL 체인입니다.

- **프롬프트**: 시스템 메시지(일본어 회화 코치 역할, 출력 JSON 형식, 답변 5개·추천 3~5개 규칙) + 대화 기록 + 사용자 메시지(`[참고 문구]`, `[질문]`)
- **LLM**: `ChatOpenAI`에 JSON 모드를 적용해 구조화된 응답을 받음
- **출력 파서**: `translation`, `answers`, `suggestions` 구조의 딕셔너리로 변환
- **임베딩**: `text-embedding-3-small`

### 리트리버 적용 방식

- 문서를 **500자 단위, 100자 겹침**으로 분할해 FAISS에 저장
- 질문이 들어오면 유사도 상위 **4개 청크**를 `[참고 문구]`로 프롬프트에 삽입
- 참고 문구에 맞는 표현이 있으면 우선 활용하고, 없으면 LLM이 직접 생성
- 인덱스는 최초 실행 시 한 번 만들어 `index/`에 저장하고 이후 재사용

### 메모리 적용 방식

- LangChain 메모리 클래스 대신, **세션별로 SQLite에 저장한 대화에서 최근 6개 메시지**를 꺼내 `history`로 직접 주입
- AI 메시지는 번역된 일본어 한 문장만, 사용자 메시지는 질문 원문만 넣어 토큰 절약
- 서버를 재시작해도 대화가 유지되며, 브라우저는 마지막으로 연 세션 ID를 `localStorage`에 기억

## 7. 사용 방법 (Anaconda / Windows 기준)

### 7-1. 환경 준비

```bash
conda create -n jpchat python=3.11 -y
conda activate jpchat
pip install fastapi "uvicorn[standard]" langchain langchain-community langchain-openai langchain-text-splitters faiss-cpu pypdf python-dotenv
```

이미 `requirements.txt`가 있다면 `pip install -r requirements.txt`로 설치해도 됩니다.

### 7-2. 환경변수 설정

프로젝트 루트에 `.env` 파일을 만듭니다.

```
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
EMBED_MODEL=text-embedding-3-small
```

`LLM_MODEL`, `EMBED_MODEL`은 생략하면 기본값을 사용합니다.

### 7-3. 서버 실행

프로젝트 루트(`app/`, `static/`, `data/`가 보이는 위치)에서 실행합니다.

```bash
python -m uvicorn app.main:app --reload --port 8000
```

브라우저에서 `http://localhost:8000`에 접속합니다. API 목록은 `http://localhost:8000/docs`에서 확인할 수 있습니다.

### 7-4. 사용 순서

1. 왼쪽 위 **새 대화**를 누르거나 바로 질문 입력
2. 한국어로 여행 중 하고 싶은 말이나 질문을 입력 (Enter 전송, Shift+Enter 줄바꿈)
3. 일본어 번역, 예상 답변 5개, 추천 문구 확인
4. 🔊 버튼으로 발음을 들으며 따라 말하기
5. 왼쪽 목록에서 과거 대화 다시 열기, `✕`로 삭제

## 8. 회화 문구 데이터 추가하기

1. `data/` 폴더에 `pdf`, `md`, `txt` 파일을 추가합니다.
2. 문구는 아래 형식을 권장합니다.
   ```
   # 분류명
   - 日本語の文。(한글 발음) 한글 뜻
   ```
3. 루트의 `index/` 폴더를 삭제한 뒤 서버를 다시 실행하면 새 문서로 인덱스가 재생성됩니다.

> 기본 포함된 문구는 작성자가 만든 것이므로, 실제 서비스 전에는 일본어 감수를 권장합니다.

## 9. API 요약

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/sessions` | 세션 목록 |
| POST | `/api/sessions` | 새 세션 생성 |
| GET | `/api/sessions/{id}` | 세션의 대화 내용 조회 |
| DELETE | `/api/sessions/{id}` | 세션 삭제 |
| POST | `/api/sessions/{id}/chat` | 질문 전송 `{"message": "..."}` → 번역 · 답변 · 추천 JSON |

## 10. 자주 발생하는 문제

| 증상 | 원인과 해결 |
|---|---|
| `uvicorn: command not found` | 가상환경이 활성화되지 않음. `python -m uvicorn ...` 방식으로 실행 |
| `FileNotFoundError` (SSL 인증서) | `SSL_CERT_FILE`이 없는 파일을 가리킴. certifi 경로로 교체 후 재활성화<br>`conda env config vars set SSL_CERT_FILE="<환경경로>\Lib\site-packages\certifi\cacert.pem" -n jpchat` |
| 화면은 뜨는데 버튼이 동작하지 않음 | `index.html`의 `<script src>` 이름과 `static/`의 JS 파일 이름이 다름 (`GET ... 404` 로그 확인) |
| `ModuleNotFoundError: No module named 'app'` | 프로젝트 루트가 아닌 곳에서 실행함 |
| `OPENAI_API_KEY` 오류 | `.env` 파일이 루트에 없거나 키가 비어 있음 |
| 문구를 수정했는데 반영되지 않음 | `index/` 폴더 삭제 후 서버 재시작 |
| `address already in use` | `--port 8001` 등 다른 포트 사용 |

## 11. 한계와 개선 계획

- **사용자 구분 없음**: 로그인이 없어 세션 목록이 접속자 전체에 공유됨 → 쿠키 또는 로그인 도입
- **스트리밍 없음**: 응답을 한 번에 받음 → 단계별 스트리밍 응답 적용
- **문구 데이터 규모**: 샘플 수준 → 실제 회화집 PDF 및 지역별(교토, 오사카, 도쿄) 문구 확장
- **사실 확인 한계**: 역·경로 같은 정보는 번역·연습용이므로 지도 앱이나 현지 안내로 확인 필요
- **발음 표기**: 한글 발음은 근사치이므로 🔊 음성과 함께 확인

## 12. 참고

- 2일차 수업 노트북(RAG 파이프라인: PDF 로드 → 청크 분할 → 임베딩 → FAISS → LCEL 체인)을 기반으로 제작했습니다.
- 상업적 배포 시 OpenAI API 사용 정책과 비용을 확인하세요.
