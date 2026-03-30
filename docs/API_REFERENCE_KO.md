# HYDRA Engine API 레퍼런스

모든 보호된 엔드포인트는 아래 헤더를 요구합니다.

```http
X-HYDRA-KEY: <HYDRA_API_KEY>
```

## 1. 헬스체크

### `GET /health`

인증 없이 호출할 수 있습니다.

```bash
curl http://127.0.0.1:8000/health
```

## 2. 시스템

### `GET /status`

서버 프로필과 상태를 조회합니다.

### `GET /modules`

활성 모듈 상태를 조회합니다.

## 3. 시장 관리

### `GET /markets`

현재 활성 시장 목록을 반환합니다.

### `POST /markets/{market_id}/enable`

시장 활성화

예시:

```bash
curl -X POST \
  -H "X-HYDRA-KEY: my-local-demo-key" \
  http://127.0.0.1:8000/markets/binance/enable
```

### `POST /markets/{market_id}/disable`

시장 비활성화

## 4. 데이터

### `GET /data/symbols`

수집 중이거나 저장된 시장/심볼/타임프레임 목록을 반환합니다.

### `GET /data/candles`

쿼리 파라미터:

- `market`
- `symbol`
- `timeframe`
- `limit` (기본 200, 최대 1000)
- `since` (선택)

예시:

```bash
curl -G http://127.0.0.1:8000/data/candles \
  -H "X-HYDRA-KEY: my-local-demo-key" \
  --data-urlencode "market=binance" \
  --data-urlencode "symbol=BTC/USDT" \
  --data-urlencode "timeframe=1h" \
  --data-urlencode "limit=100"
```

## 5. 지표 / 레짐 / 시그널

### `GET /indicators`
### `GET /indicators/list`
### `GET /regime`
### `GET /regime/list`
### `GET /signal`
### `GET /signal/list`

이 엔드포인트들은 최신 계산 결과를 확인할 때 사용합니다.

## 6. 포지션 / 손익 / 리스크

### `GET /positions`
### `GET /pnl`
### `POST /pnl/reset-daily`
### `GET /risk`
### `POST /killswitch`

`POST /killswitch`는 매우 위험한 명령이므로 테스트 목적이 아니라면 호출하지 마세요.

예시:

```bash
curl -X POST "http://127.0.0.1:8000/killswitch?reason=manual_test" \
  -H "X-HYDRA-KEY: my-local-demo-key"
```

## 7. 백테스트

### `POST /backtest/run`

요청 본문:

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

응답에는 아래 항목이 포함됩니다.

- 시장 / 심볼 / 타임프레임
- 초기 자본 / 최종 자본
- 체결 트레이드 목록
- equity curve
- 성과 지표(`total_return_pct`, `total_trades`, `win_rate`, `max_drawdown_pct`, `sharpe_ratio`, `avg_pnl_usd`)

## 8. 보조 데이터

### `GET /orderbook`
### `GET /events`
### `GET /sentiment`

각 엔드포인트는 최근 오더북, 이벤트 일정, 감성 점수를 조회하는 데 사용합니다.

## 9. 인증 실패 시

- 잘못된 API 키: `403 Invalid API key`
- 내부 초기화 전 호출: `503 Store not initialized` 등

## 10. 권장 호출 순서

1. `/health`
2. `/markets`
3. `/data/symbols`
4. `/data/candles`
5. `/backtest/run`

실거래 관련 동작은 충분한 검증 이후에만 진행하세요.
