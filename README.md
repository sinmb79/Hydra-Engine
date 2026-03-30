# HYDRA Engine

HYDRA Engine은 로컬 우선(Local-first) 철학으로 설계된 자동매매 엔진 프로젝트입니다.  
데이터 수집, 지표 계산, 레짐 분류, 시그널 생성, 보조 데이터 수집, 백테스트, FastAPI API, Typer CLI를 하나의 저장소에서 관리합니다.

이 저장소는 "실거래 수익 보장"을 목표로 하지 않습니다. 먼저 안전하게 실행하고, 충분히 검증하고, 필요할 때만 확장하는 것을 목표로 합니다.

## 1. 현재 포함된 기능

- FastAPI 기반 제어/API 서버
- Redis 기반 상태 공유
- OHLCV 수집기와 SQLite/TimescaleDB 저장소
- 지표 계산 엔진
- 레짐(Regime) 분류 엔진
- 전략 시그널 엔진
- 오더북 / 이벤트 / 감성 보조 데이터 수집
- 인메모리 백테스트 엔진
- Kill Switch, 주문 큐, 리스크 엔진, 설정 검증
- CLI 도구와 Docker Compose 프로필(lite / pro / expert)

## 2. 이 프로젝트를 어떻게 이해하면 좋은가

HYDRA는 한 번에 모든 기능을 다 켜는 프로젝트가 아닙니다.

1. 먼저 데이터를 수집합니다.
2. 지표와 레짐, 시그널을 계산합니다.
3. API나 CLI로 상태를 확인합니다.
4. 백테스트로 전략을 검증합니다.
5. 실거래는 마지막 단계에서 매우 조심스럽게 붙입니다.

현재 저장소에는 실거래로 연결되는 기반 코드가 일부 포함되어 있지만, 여러 CLI 명령은 아직 "예정" 상태의 placeholder를 포함합니다. 공개 배포용으로는 안전하게 시험, 학습, 백테스트, 데이터 파이프라인 검증부터 시작하는 것을 권장합니다.

## 3. 빠른 시작

가장 쉬운 시작 방법은 아래 두 가지입니다.

- 로컬 Python 환경에서 테스트부터 실행
- Docker Compose Lite 프로필로 전체 파이프라인 기동

### 3.1 요구 사항

- Python 3.11 이상
- Docker / Docker Compose
- Redis
- Git

### 3.2 저장소 준비

```bash
git clone https://github.com/sinmb79/Hydra-Engine.git
cd Hydra-Engine
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

패키지 설치:

```bash
pip install -e .[dev]
```

### 3.3 환경 변수 설정

`.env.example`를 복사해서 `.env`를 만드세요.

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

최소 필수 항목:

```env
HYDRA_API_KEY=change-me-to-a-random-secret
HYDRA_PROFILE=lite
REDIS_URL=redis://localhost:6379
```

`pro` 또는 `expert` 프로필에서는 `DB_PASSWORD`가 필요합니다.

## 4. 가장 먼저 해볼 것

### 4.1 테스트 실행

```bash
pytest -q
```

정상이라면 전체 테스트가 통과해야 합니다.

### 4.2 Lite 프로필로 실행

```bash
docker compose -f docker-compose.lite.yml up --build
```

서버 헬스체크:

```bash
curl http://127.0.0.1:8000/health
```

## 5. 주요 사용 흐름

### 5.1 활성 시장 확인

```bash
curl -H "X-HYDRA-KEY: change-me-to-a-random-secret" \
  http://127.0.0.1:8000/markets
```

### 5.2 수집 중인 심볼 확인

```bash
curl -H "X-HYDRA-KEY: change-me-to-a-random-secret" \
  http://127.0.0.1:8000/data/symbols
```

### 5.3 캔들 조회

```bash
curl -G http://127.0.0.1:8000/data/candles \
  -H "X-HYDRA-KEY: change-me-to-a-random-secret" \
  --data-urlencode "market=binance" \
  --data-urlencode "symbol=BTC/USDT" \
  --data-urlencode "timeframe=1h" \
  --data-urlencode "limit=200"
```

### 5.4 백테스트 실행

```bash
curl -X POST http://127.0.0.1:8000/backtest/run \
  -H "Content-Type: application/json" \
  -H "X-HYDRA-KEY: change-me-to-a-random-secret" \
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

### 5.5 Kill Switch

Kill Switch는 전 포지션 청산을 시도하는 고위험 명령입니다. 테스트 목적이 아니라면 함부로 사용하지 마세요.

CLI:

```bash
python -m hydra.cli.app kill
```

API:

```bash
curl -X POST "http://127.0.0.1:8000/killswitch?reason=manual_test" \
  -H "X-HYDRA-KEY: change-me-to-a-random-secret"
```

## 6. CLI 예시

```bash
python -m hydra.cli.app --help
python -m hydra.cli.app setup
python -m hydra.cli.app status
python -m hydra.cli.app market list-markets
python -m hydra.cli.app market enable binance --mode paper
python -m hydra.cli.app trade crypto binance BTC/USDT buy 0.01
```

주의:

- `trade`, `strategy`, `module` 일부 명령은 아직 placeholder 메시지를 출력합니다.
- 공개 버전 기준으로는 데이터 수집, 관찰, 백테스트 중심으로 사용하는 것이 안전합니다.

## 7. Docker 프로필

- `docker-compose.lite.yml`
  - SQLite 사용
  - 개인 PC / 테스트 / 입문용
- `docker-compose.pro.yml`
  - TimescaleDB + Redis
  - 중간 규모 수집/분석용
- `docker-compose.expert.yml`
  - 고사양 장비 / 확장 시나리오용

## 8. 문서

- 자세한 시작 가이드: [docs/QUICKSTART_KO.md](docs/QUICKSTART_KO.md)
- API 레퍼런스: [docs/API_REFERENCE_KO.md](docs/API_REFERENCE_KO.md)
- 법적 고지: [DISCLAIMER.md](DISCLAIMER.md)

## 9. 안전 안내

- 이 저장소는 교육, 연구, 실험용입니다.
- 실거래 전에는 반드시 paper 모드와 백테스트로 먼저 검증하세요.
- `.env`, API 키, 계정 정보는 절대 Git에 올리지 마세요.
- 기본적으로 로컬/사설 네트워크에서만 운용하는 것을 권장합니다.

## 10. 라이선스

이 저장소는 [MIT License](LICENSE)를 따릅니다.
