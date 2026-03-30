# HYDRA Engine 빠른 시작 가이드

**목표:** 이 문서를 따라하면 10~15분 안에 테스트 통과 및 서버 기동까지 완료할 수 있습니다.

---

## 1단계: 저장소 다운로드

```bash
git clone https://github.com/sinmb79/Hydra-Engine.git
cd Hydra-Engine
```

---

## 2단계: Python 가상환경 설정

```bash
python -m venv .venv
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

터미널 앞에 `(.venv)` 가 표시되면 활성화 성공입니다.

```bash
pip install -e .[dev]
```

---

## 3단계: 환경 변수 설정

**macOS / Linux:**
```bash
cp .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

`.env` 파일을 열고 `HYDRA_API_KEY` 를 변경합니다:

```env
HYDRA_API_KEY=my-secret-key-2024
HYDRA_PROFILE=lite
REDIS_URL=redis://localhost:6379
```

> `HYDRA_API_KEY` 는 API 호출 시 사용하는 비밀번호입니다. 아무 문자열이나 가능합니다.

---

## 4단계: 테스트 실행

```bash
pytest -q
```

전체 테스트가 통과하면 코드 상태가 정상입니다.

실패하는 테스트가 있으면:
- 가상환경이 활성화되어 있는지 확인
- `pip install -e .[dev]` 를 다시 실행

---

## 5단계: Docker로 서버 실행

Docker Desktop이 실행 중인지 먼저 확인합니다.

```bash
docker compose -f docker-compose.lite.yml up --build
```

새 터미널 창을 열고 헬스체크:

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status": "ok"}
```

이 응답이 오면 서버가 정상 실행 중입니다.

---

## 6단계: 기본 API 호출 테스트

이후 모든 API 호출에는 `X-HYDRA-KEY` 헤더를 붙입니다.

### 시장 확인

```bash
curl -H "X-HYDRA-KEY: my-secret-key-2024" \
  http://127.0.0.1:8000/markets
```

### 저장된 심볼 목록

```bash
curl -H "X-HYDRA-KEY: my-secret-key-2024" \
  http://127.0.0.1:8000/data/symbols
```

### 캔들 데이터 조회

```bash
curl -G http://127.0.0.1:8000/data/candles \
  -H "X-HYDRA-KEY: my-secret-key-2024" \
  --data-urlencode "market=binance" \
  --data-urlencode "symbol=BTC/USDT" \
  --data-urlencode "timeframe=1h" \
  --data-urlencode "limit=50"
```

### 백테스트 실행

```bash
curl -X POST http://127.0.0.1:8000/backtest/run \
  -H "Content-Type: application/json" \
  -H "X-HYDRA-KEY: my-secret-key-2024" \
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

---

## 7단계: 권장 사용 순서

```
테스트 통과 확인
    ↓
시장 설정 확인 (GET /markets)
    ↓
데이터 수집 상태 확인 (GET /data/symbols)
    ↓
캔들 데이터 조회 (GET /data/candles)
    ↓
백테스트 실행 (POST /backtest/run)
    ↓
전략 성과 분석
    ↓
(충분한 검증 후) 실거래 연결
```

---

## CLI 빠른 참조

```bash
python -m hydra.cli.app --help              # 전체 도움말
python -m hydra.cli.app setup               # 초기 설정 마법사
python -m hydra.cli.app status              # 현재 상태
python -m hydra.cli.app market list-markets # 시장 목록
python -m hydra.cli.app market enable binance --mode paper  # 모의거래 활성화
```

---

## 문제가 생겼을 때

| 증상 | 확인할 것 |
|------|----------|
| `ModuleNotFoundError` | 가상환경 활성화 여부, `pip install -e .[dev]` 재실행 |
| `403 Invalid API key` | `.env`의 `HYDRA_API_KEY`와 헤더 값 일치 여부 |
| Redis 연결 오류 | Docker Desktop 실행 여부, `REDIS_URL` 설정 |
| 포트 8000 이미 사용 중 | 다른 프로세스 확인 후 종료 |

더 자세한 내용은 [README.md](../README.md) 의 FAQ 섹션을 참고하세요.
