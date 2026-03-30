# HYDRA Engine API 레퍼런스

## 인증

`/health`를 제외한 모든 엔드포인트는 아래 헤더를 요구합니다.

```http
X-HYDRA-KEY: <HYDRA_API_KEY>
```

`.env`에 설정한 `HYDRA_API_KEY` 값을 사용합니다.

**인증 실패 시 응답:**
```json
HTTP 403
{"detail": "Invalid or missing API key. Set X-HYDRA-KEY header."}
```

---

## 엔드포인트 목록

### 1. 헬스체크

#### `GET /health`

서버 상태를 확인합니다. **인증 불필요.**

```bash
curl http://127.0.0.1:8000/health
```

**응답:**
```json
{"status": "ok"}
```

---

### 2. 시스템

#### `GET /status`

서버 프로필, 가동 시간 등 시스템 상태를 조회합니다.

```bash
curl -H "X-HYDRA-KEY: my-key" http://127.0.0.1:8000/status
```

#### `GET /modules`

각 모듈(수집기, 지표 엔진 등)의 활성 상태를 조회합니다.

```bash
curl -H "X-HYDRA-KEY: my-key" http://127.0.0.1:8000/modules
```

---

### 3. 시장 관리

#### `GET /markets`

현재 설정된 시장 목록과 활성 상태를 반환합니다.

```bash
curl -H "X-HYDRA-KEY: my-key" http://127.0.0.1:8000/markets
```

**응답 예시:**
```json
[
  {"market_id": "binance", "active": true, "mode": "paper"},
  {"market_id": "upbit", "active": false, "mode": "paper"}
]
```

#### `POST /markets/{market_id}/enable`

시장을 활성화합니다.

```bash
curl -X POST \
  -H "X-HYDRA-KEY: my-key" \
  http://127.0.0.1:8000/markets/binance/enable
```

#### `POST /markets/{market_id}/disable`

시장을 비활성화합니다.

```bash
curl -X POST \
  -H "X-HYDRA-KEY: my-key" \
  http://127.0.0.1:8000/markets/binance/disable
```

---

### 4. 데이터

#### `GET /data/symbols`

수집 중이거나 저장된 시장/심볼/타임프레임 목록을 반환합니다.

```bash
curl -H "X-HYDRA-KEY: my-key" http://127.0.0.1:8000/data/symbols
```

**응답 예시:**
```json
[
  {"market": "binance", "symbol": "BTC/USDT", "timeframe": "1h"},
  {"market": "binance", "symbol": "ETH/USDT", "timeframe": "1h"}
]
```

#### `GET /data/candles`

OHLCV 캔들 데이터를 조회합니다.

**쿼리 파라미터:**

| 파라미터 | 필수 | 설명 | 예시 |
|---------|------|------|------|
| `market` | 필수 | 거래소 ID | `binance` |
| `symbol` | 필수 | 심볼 | `BTC/USDT` |
| `timeframe` | 필수 | 타임프레임 | `1h`, `4h`, `1d` |
| `limit` | 선택 | 캔들 수 (기본 200, 최대 1000) | `100` |
| `since` | 선택 | 시작 시간 (Unix ms) | `1704067200000` |

```bash
curl -G http://127.0.0.1:8000/data/candles \
  -H "X-HYDRA-KEY: my-key" \
  --data-urlencode "market=binance" \
  --data-urlencode "symbol=BTC/USDT" \
  --data-urlencode "timeframe=1h" \
  --data-urlencode "limit=100"
```

**응답 예시:**
```json
[
  {
    "timestamp": 1704067200000,
    "open": 42000.0,
    "high": 42500.0,
    "low": 41800.0,
    "close": 42300.0,
    "volume": 1234.56
  }
]
```

---

### 5. 지표 / 레짐 / 시그널

#### `GET /indicators`

가장 최근 계산된 지표 값을 반환합니다.

#### `GET /indicators/list`

계산 가능한 지표 목록을 반환합니다.

#### `GET /regime`

현재 시장 레짐(상태) 분류 결과를 반환합니다.

> 레짐 예시: `trending_up`, `trending_down`, `sideways`, `high_volatility`

#### `GET /regime/list`

레짐 히스토리 목록을 반환합니다.

#### `GET /signal`

가장 최근 전략 시그널을 반환합니다.

> 시그널 예시: `{"signal": "buy", "confidence": 0.72}`

#### `GET /signal/list`

시그널 히스토리 목록을 반환합니다.

```bash
curl -H "X-HYDRA-KEY: my-key" http://127.0.0.1:8000/indicators
curl -H "X-HYDRA-KEY: my-key" http://127.0.0.1:8000/regime
curl -H "X-HYDRA-KEY: my-key" http://127.0.0.1:8000/signal
```

---

### 6. 포지션 / 손익

#### `GET /positions`

현재 보유 포지션 목록을 반환합니다.

```bash
curl -H "X-HYDRA-KEY: my-key" http://127.0.0.1:8000/positions
```

**응답 예시:**
```json
[
  {
    "symbol": "BTC/USDT",
    "side": "long",
    "size": 0.01,
    "entry_price": 42000.0,
    "unrealized_pnl": 30.0
  }
]
```

#### `GET /pnl`

누적 손익 정보를 반환합니다.

```bash
curl -H "X-HYDRA-KEY: my-key" http://127.0.0.1:8000/pnl
```

#### `POST /pnl/reset-daily`

일일 손익을 초기화합니다.

```bash
curl -X POST -H "X-HYDRA-KEY: my-key" http://127.0.0.1:8000/pnl/reset-daily
```

---

### 7. 리스크 엔진

#### `GET /risk`

현재 리스크 상태(포지션 한도, 사용률 등)를 반환합니다.

```bash
curl -H "X-HYDRA-KEY: my-key" http://127.0.0.1:8000/risk
```

#### `POST /killswitch`

> **경고: 이 엔드포인트는 모든 포지션을 즉시 청산을 시도합니다. 신중하게 사용하세요.**

긴급 상황에서 전 포지션 청산을 트리거합니다.

```bash
curl -X POST "http://127.0.0.1:8000/killswitch?reason=emergency" \
  -H "X-HYDRA-KEY: my-key"
```

**파라미터:**
- `reason` (선택): 청산 사유 메모 (로그에 기록됨)

---

### 8. 백테스트

#### `POST /backtest/run`

수집된 캔들 데이터를 기반으로 전략을 백테스트합니다.

**요청 본문:**

```json
{
  "market": "binance",
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "since": 1704067200000,
  "until": 1706745600000,
  "initial_capital": 10000,
  "trade_amount_usd": 100,
  "commission_pct": 0.001
}
```

| 필드 | 필수 | 설명 |
|------|------|------|
| `market` | 필수 | 거래소 ID |
| `symbol` | 필수 | 심볼 |
| `timeframe` | 필수 | 타임프레임 |
| `since` | 필수 | 시작 시간 (Unix ms) |
| `until` | 필수 | 종료 시간 (Unix ms) |
| `initial_capital` | 선택 | 초기 자본 (기본 10000 USD) |
| `trade_amount_usd` | 선택 | 1회 거래 금액 (기본 100 USD) |
| `commission_pct` | 선택 | 수수료율 (기본 0.001 = 0.1%) |

```bash
curl -X POST http://127.0.0.1:8000/backtest/run \
  -H "Content-Type: application/json" \
  -H "X-HYDRA-KEY: my-key" \
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

**응답 예시:**
```json
{
  "market": "binance",
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "initial_capital": 10000,
  "final_capital": 10850.0,
  "total_return_pct": 8.5,
  "total_trades": 24,
  "win_rate": 0.583,
  "max_drawdown_pct": -4.2,
  "sharpe_ratio": 1.35,
  "avg_pnl_usd": 35.4,
  "trades": [...],
  "equity_curve": [...]
}
```

> **Unix timestamp 변환 팁:**
> - 2024-01-01 00:00:00 UTC → `1704067200000`
> - 2024-02-01 00:00:00 UTC → `1706745600000`

---

### 9. 보조 데이터

#### `GET /orderbook`

최근 수집된 오더북 스냅샷을 반환합니다.

#### `GET /events`

수집된 크립토 이벤트 일정(상장, 하드포크 등)을 반환합니다.

#### `GET /sentiment`

감성 분석 점수를 반환합니다. (-1.0 = 매우 부정, +1.0 = 매우 긍정)

```bash
curl -H "X-HYDRA-KEY: my-key" http://127.0.0.1:8000/orderbook
curl -H "X-HYDRA-KEY: my-key" http://127.0.0.1:8000/events
curl -H "X-HYDRA-KEY: my-key" http://127.0.0.1:8000/sentiment
```

---

## 주요 HTTP 오류 코드

| 코드 | 의미 | 원인 |
|------|------|------|
| `403` | 인증 실패 | API 키 누락 또는 불일치 |
| `503` | 서비스 초기화 중 | 서버 기동 직후, 잠시 후 재시도 |
| `422` | 요청 형식 오류 | 필수 파라미터 누락 또는 타입 오류 |
| `500` | 서버 내부 오류 | 로그 확인 필요 |

---

## 권장 호출 순서

처음 사용할 때는 아래 순서로 호출해 각 단계가 정상인지 확인합니다.

```
1. GET /health          → 서버 정상 확인
2. GET /markets         → 시장 설정 확인
3. GET /data/symbols    → 수집 데이터 확인
4. GET /data/candles    → 캔들 데이터 조회
5. POST /backtest/run   → 백테스트 실행
6. GET /positions       → 포지션 확인
7. GET /pnl             → 손익 확인
```

실거래 관련 동작은 충분한 검증(백테스트, paper 모드) 이후에만 진행하세요.
