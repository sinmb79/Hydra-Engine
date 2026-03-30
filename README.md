# HYDRA Engine

HYDRA Engine은 **로컬 우선(Local-first)** 철학으로 설계된 자동매매 엔진입니다.
데이터 수집 → 지표 계산 → 레짐 분류 → 시그널 생성 → 백테스트 → 실거래까지 하나의 저장소에서 관리합니다.

> **이 프로젝트는 교육·연구·실험용입니다.**
> 실거래 수익을 보장하지 않으며, 사용에 따른 모든 책임은 사용자 본인에게 있습니다.
> 반드시 [DISCLAIMER.md](DISCLAIMER.md)를 먼저 읽으세요.

---

## 목차

1. [포함된 기능](#1-포함된-기능)
2. [사용 철학 — 어떻게 접근할 것인가](#2-사용-철학--어떻게-접근할-것인가)
3. [준비물 설치](#3-준비물-설치)
4. [처음 시작하기 (5단계)](#4-처음-시작하기-5단계)
5. [테스트 실행](#5-테스트-실행)
6. [Docker로 전체 파이프라인 실행](#6-docker로-전체-파이프라인-실행)
7. [API 사용법](#7-api-사용법)
8. [CLI 사용법](#8-cli-사용법)
9. [Docker 프로필 선택](#9-docker-프로필-선택)
10. [자주 발생하는 문제 (FAQ)](#10-자주-발생하는-문제-faq)
11. [문서](#11-문서)
12. [라이선스](#12-라이선스)

---

## 1. 포함된 기능

| 모듈 | 설명 |
|------|------|
| FastAPI 서버 | REST API로 모든 기능 제어 |
| OHLCV 수집기 | 거래소에서 캔들 데이터 수집, SQLite/TimescaleDB 저장 |
| 지표 계산 엔진 | RSI, MACD, Bollinger Band 등 자동 계산 |
| 레짐 분류 엔진 | 시장 상태(추세/횡보/변동성) 분류 |
| 전략 시그널 엔진 | 매수/매도 시그널 생성 |
| 보조 데이터 수집 | 오더북, 이벤트 일정, 감성 점수 |
| 인메모리 백테스트 | 수집된 데이터로 전략 성과 검증 |
| Kill Switch | 긴급 전 포지션 청산 |
| 주문 큐 | 안전한 주문 처리 파이프라인 |
| 리스크 엔진 | 포지션 및 리스크 관리 |
| CLI 도구 | 터미널에서 모든 기능 제어 |
| Telegram 알림 | 주요 이벤트 실시간 알림 |

---

## 2. 사용 철학 — 어떻게 접근할 것인가

HYDRA는 **한 번에 모든 기능을 켜는 프로젝트가 아닙니다.**

```
1단계: 테스트 실행으로 코드 정상 확인
2단계: 데이터 수집 (거래소 API 키 없어도 공개 데이터 가능)
3단계: 지표·레짐·시그널 계산 확인
4단계: API/CLI로 상태 관찰
5단계: 백테스트로 전략 검증
6단계: (충분한 검증 후) 실거래 연결
```

처음 사용하는 분은 **1~4단계**부터 시작하는 것을 강력히 권장합니다.

---

## 3. 준비물 설치

### 필수 소프트웨어

| 소프트웨어 | 버전 | 설치 링크 |
|-----------|------|----------|
| Python | 3.11 이상 | https://www.python.org/downloads/ |
| Git | 최신 | https://git-scm.com/ |
| Docker Desktop | 최신 | https://www.docker.com/products/docker-desktop |

> Docker Desktop을 설치하면 Docker와 Docker Compose가 함께 설치됩니다.

### 설치 확인

터미널(명령 프롬프트 / PowerShell / Terminal)에서 아래 명령을 실행해 버전을 확인합니다.

```bash
python --version      # Python 3.11.x 이상이어야 함
git --version
docker --version
docker compose version
```

---

## 4. 처음 시작하기 (5단계)

### 4.1 저장소 다운로드

```bash
git clone https://github.com/sinmb79/Hydra-Engine.git
cd Hydra-Engine
```

### 4.2 Python 가상환경 생성 및 활성화

가상환경은 이 프로젝트 전용 Python 환경을 만들어 다른 프로젝트와 충돌하지 않게 합니다.

```bash
python -m venv .venv
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

> PowerShell에서 실행 오류가 발생하면 먼저 아래 명령을 실행하세요:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

활성화되면 터미널 앞에 `(.venv)`가 표시됩니다.

### 4.3 패키지 설치

```bash
pip install -e .[dev]
```

> 처음 설치 시 수분이 걸릴 수 있습니다.

### 4.4 환경 변수 설정

`.env.example` 파일을 복사해 `.env`를 만듭니다.

**macOS / Linux:**
```bash
cp .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

생성된 `.env` 파일을 텍스트 에디터로 열어 아래 항목을 수정합니다.

```env
# 반드시 변경하세요 — 이 값이 API 접근 비밀번호입니다
HYDRA_API_KEY=여기에-랜덤-문자열-입력

# 프로필: lite(입문) / pro(중급) / expert(고급)
HYDRA_PROFILE=lite

# Redis 주소 (Docker 사용 시 기본값 유지)
REDIS_URL=redis://localhost:6379
```

> **HYDRA_API_KEY**는 API 호출 시 인증에 사용됩니다.
> 아무 문자열이나 사용할 수 있습니다. 예: `my-hydra-secret-2024`

### 4.5 테스트 실행으로 정상 확인

```bash
pytest -q
```

모든 테스트가 통과하면 준비 완료입니다.

---

## 5. 테스트 실행

```bash
# 전체 테스트
pytest -q

# 특정 파일만
pytest tests/test_backtest_runner.py -v

# 상세 출력
pytest -v
```

---

## 6. Docker로 전체 파이프라인 실행

Docker Desktop이 실행 중인지 확인한 후 아래 명령을 실행합니다.

```bash
docker compose -f docker-compose.lite.yml up --build
```

> 첫 실행 시 이미지 빌드로 수분이 걸립니다.

### 실행 확인

새 터미널을 열고 헬스체크를 합니다.

```bash
curl http://127.0.0.1:8000/health
```

아래와 같은 응답이 오면 정상입니다.

```json
{"status": "ok"}
```

### 종료

```bash
# Ctrl+C 로 중지 후
docker compose -f docker-compose.lite.yml down
```

---

## 7. API 사용법

모든 API 호출은 `/health`를 제외하고 `X-HYDRA-KEY` 헤더를 포함해야 합니다.

```bash
curl -H "X-HYDRA-KEY: 여기에-API-키" http://127.0.0.1:8000/엔드포인트
```

### 7.1 헬스체크 (인증 불필요)

```bash
curl http://127.0.0.1:8000/health
```

### 7.2 활성 시장 확인

```bash
curl -H "X-HYDRA-KEY: my-hydra-secret-2024" \
  http://127.0.0.1:8000/markets
```

### 7.3 수집 중인 심볼 확인

```bash
curl -H "X-HYDRA-KEY: my-hydra-secret-2024" \
  http://127.0.0.1:8000/data/symbols
```

### 7.4 캔들(OHLCV) 데이터 조회

```bash
curl -G http://127.0.0.1:8000/data/candles \
  -H "X-HYDRA-KEY: my-hydra-secret-2024" \
  --data-urlencode "market=binance" \
  --data-urlencode "symbol=BTC/USDT" \
  --data-urlencode "timeframe=1h" \
  --data-urlencode "limit=100"
```

### 7.5 백테스트 실행

```bash
curl -X POST http://127.0.0.1:8000/backtest/run \
  -H "Content-Type: application/json" \
  -H "X-HYDRA-KEY: my-hydra-secret-2024" \
  -d '{
    "market": "binance",
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "since": 1704067200000,
    "until": 1706745600000,
    "initial_capital": 10000,
    "trade_amount_usd": 100,
    "commission_pct": 0.001
  }'
```

> `since`와 `until`은 Unix timestamp (밀리초) 입니다.
> 위 예시는 2024년 1월 1일 ~ 2024년 2월 1일 구간입니다.

### 7.6 포지션 / 손익 확인

```bash
curl -H "X-HYDRA-KEY: my-hydra-secret-2024" http://127.0.0.1:8000/positions
curl -H "X-HYDRA-KEY: my-hydra-secret-2024" http://127.0.0.1:8000/pnl
```

### 7.7 Kill Switch (주의: 전 포지션 청산)

```bash
curl -X POST "http://127.0.0.1:8000/killswitch?reason=manual_test" \
  -H "X-HYDRA-KEY: my-hydra-secret-2024"
```

> Kill Switch는 실거래 중 긴급 상황에서만 사용하세요.

전체 API 목록은 [docs/API_REFERENCE_KO.md](docs/API_REFERENCE_KO.md)를 참고하세요.

---

## 8. CLI 사용법

```bash
# 도움말
python -m hydra.cli.app --help

# 초기 설정 마법사
python -m hydra.cli.app setup

# 현재 상태 확인
python -m hydra.cli.app status

# 시장 목록 확인
python -m hydra.cli.app market list-markets

# 시장 활성화 (paper = 모의거래)
python -m hydra.cli.app market enable binance --mode paper

# Kill Switch (긴급 청산)
python -m hydra.cli.app kill
```

> `trade`, `strategy`, `module` 명령 일부는 현재 개발 예정 상태입니다.

---

## 9. Docker 프로필 선택

| 프로필 | 파일 | 데이터베이스 | 권장 대상 |
|--------|------|------------|----------|
| **lite** | `docker-compose.lite.yml` | SQLite | 처음 시작하는 분, 개인 PC |
| **pro** | `docker-compose.pro.yml` | TimescaleDB + Redis | 중간 규모 수집·분석 |
| **expert** | `docker-compose.expert.yml` | 고사양 확장 구성 | 대용량 데이터, 고성능 서버 |

처음 사용자는 **lite**부터 시작하세요.

```bash
# lite
docker compose -f docker-compose.lite.yml up --build

# pro (DB_PASSWORD 설정 필요)
docker compose -f docker-compose.pro.yml up --build

# expert
docker compose -f docker-compose.expert.yml up --build
```

---

## 10. 자주 발생하는 문제 (FAQ)

### Q: `pytest` 실행 시 ModuleNotFoundError가 발생해요

가상환경이 활성화되어 있는지 확인하세요.

```bash
# 가상환경 활성화 확인
# 터미널 앞에 (.venv)가 보여야 함

# 다시 설치
pip install -e .[dev]
```

### Q: Docker 실행 시 Redis 연결 오류가 발생해요

Docker Desktop이 실행 중인지 확인하세요. 그 다음 `.env` 파일의 `REDIS_URL`을 확인합니다.

Docker Compose 환경에서는 Redis가 컨테이너로 자동 실행되므로 기본값을 유지하세요.

```env
REDIS_URL=redis://redis:6379   # Docker Compose 내부
REDIS_URL=redis://localhost:6379  # 로컬 직접 실행
```

### Q: API 호출 시 403 오류가 발생해요

`X-HYDRA-KEY` 헤더가 `.env`의 `HYDRA_API_KEY`와 일치하는지 확인하세요.

```bash
curl -H "X-HYDRA-KEY: 설정한-키-값" http://127.0.0.1:8000/markets
```

### Q: `HYDRA_API_KEY가 기본값` 경고가 뜨는데 괜찮나요?

로컬 테스트 목적이면 무시할 수 있지만, 외부에 서버를 노출할 경우 반드시 변경하세요.
`.env` 파일에서 `HYDRA_API_KEY=change-me`를 다른 값으로 바꾸면 경고가 사라집니다.

### Q: Windows에서 PowerShell 실행 정책 오류가 발생해요

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q: Docker 빌드가 너무 느려요

처음 빌드는 수분이 걸립니다. 두 번째 실행부터는 캐시를 사용해 빠릅니다.
빌드 없이 실행하려면 `--build` 옵션을 제거하세요.

```bash
docker compose -f docker-compose.lite.yml up
```

---

## 11. 문서

| 문서 | 설명 |
|------|------|
| [docs/QUICKSTART_KO.md](docs/QUICKSTART_KO.md) | 10분 빠른 시작 가이드 |
| [docs/API_REFERENCE_KO.md](docs/API_REFERENCE_KO.md) | 전체 API 엔드포인트 레퍼런스 |
| [DISCLAIMER.md](DISCLAIMER.md) | 법적 고지 및 책임 한계 |

---

## 12. 안전 안내

- `.env` 파일과 API 키는 절대 Git에 올리지 마세요. (`.gitignore`에 이미 포함되어 있습니다)
- 실거래 전에는 반드시 paper 모드와 백테스트로 전략을 충분히 검증하세요.
- 기본적으로 로컬/사설 네트워크에서만 운용하는 것을 권장합니다.
- 거래소 API 키는 필요한 최소 권한만 부여하세요.

---

## 13. 라이선스

[MIT License](LICENSE)
