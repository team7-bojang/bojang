# AI 보험 보장 분석 서비스

보험 가입 정보와 질병·입원 정보를 기반으로 청구 가능한 보험 보장을 탐색하고, 약관 근거와 함께 분석 결과를 제공하는 서비스입니다.

---

## 기술 스택

### Frontend

* React
* TypeScript
* Vite
* Tailwind CSS
* Axios
* React Router
* Supabase Auth

### Backend

* Flask
* Pydantic
* PostgreSQL (Supabase)
* pgvector
* OpenAI / Claude API

### Infrastructure

* GitHub Actions
* Vercel
* AWS EC2
* Supabase

---

## 프로젝트 구조

```text
bojang/

├── frontend/
├── backend/
├── supabase/
│   └── migrations/
├── data/
│   ├── policies/
│   ├── parsed/
│   ├── verified/
│   └── samples/
├── docs/
├── mocks/
├── prompts/
├── scripts/
├── tests/
│   └── golden/
├── package.json
├── pnpm-workspace.yaml
└── README.md
```

---

## 브랜치 전략

```text
main
develop
feature/*
```

### main

* 프로덕션 배포 브랜치
* 발표 및 안정 버전 관리

### develop

* 통합 개발 브랜치
* Merge 시 자동 배포

### feature/*

* 기능 개발 브랜치
* PR 후 develop 병합

예시

```text
feature/login
feature/policy-upload
feature/analysis
feature/report
```

---

## 개발 환경 설정

### 저장소 복제

```bash
git clone <repository-url>
cd bojang
```

---

## Frontend 실행

```bash
cd frontend

pnpm install

pnpm dev
```

기본 주소

```text
http://localhost:5173
```

---

## Backend 실행

```bash
cd backend

python -m venv .venv
```

Windows

```bash
source .venv/Scripts/activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

패키지 설치

```bash
pip install -r requirements.txt
```

> 의존성 추가/삭제는 `requirements.in`(직접 의존성)에서 하고
> `pip-compile requirements.in -o requirements.txt`로 잠금파일을 재생성합니다.

환경변수 설정 (루트 `.env.example` 참고)

```bash
cp ../.env.example .env
```

실행

```bash
python app/main.py
```

기본 주소

```text
http://localhost:5000
```

---

## 데이터 디렉토리

### policies

원본 보험 약관 PDF

```text
data/policies/
```

※ 원본 PDF는 Git에 커밋하지 않습니다.

### parsed

파싱 결과 원본

```text
data/parsed/
```

### verified

검수 완료 데이터

```text
data/verified/
```

### samples

예시 JSON 및 테스트 데이터

```text
data/samples/
```

---

## 약관 파싱

전체 파싱

```bash
python parse_policy.py <약관.pdf> --full
```

일부 구간 테스트

```bash
python parse_policy.py <약관.pdf> --full --max-ranges 5
```

특정 페이지 재추출

```bash
python parse_rider.py <약관.pdf> --pages 60-63
```

---

## 검수 원칙

* 원본 파싱 결과 삭제 금지
* 정액 보장은 claim_rule 사용 금지
* 실손 보장만 claim_rule 작성
* 검수 전 데이터는 verified=false 유지
* verified=true 이후 정밀 판정 가능

---

## 배포 전략

### Frontend

* Vercel

### Backend

* AWS EC2

### CI/CD

```text
feature/*
    ↓
develop
    ↓
자동 배포

main
    ↓
프로덕션 관리
```

---

## 팀 역할

| 담당  | 역할                 |
| --- | ------------------ |
| 진미경 | PM, 약관 기준 관리       |
| 이태경 | Judge, Rule Engine |
| 조윤  | RAG, Embedding     |
| 이서우 | Frontend           |

```
```
