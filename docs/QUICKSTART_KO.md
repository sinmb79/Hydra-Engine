# HYDRA Engine 빠른 시작 가이드

이 문서는 "처음 받은 사람이 10분 안에 테스트와 기본 실행까지 해보는 것"을 목표로 합니다.

## 1. 준비물

- Python 3.11 이상
- Git
- Docker / Docker Compose

## 2. 설치

```bash
git clone https://github.com/sinmb79/Hydra-Engine.git
cd Hydra-Engine
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

패키지 설치:

```bash
pip install -e .[dev]
```

## 3. 환경 변수

```bash
cp .env.example .env
```

최소 예시:

```env
HYDRA_API_KEY=my-local-demo-key
HYDRA_PROFILE=lite
REDIS_URL=redis://localhost:6379
```

## 4. 정상 동작 확인

```bash
pytest -q
```

테스트가 모두 통과하면 기본 코드 상태는 정상입니다.

## 5. Lite 프로필 실행

```bash
docker compose -f docker-compose.lite.yml up --build
```

다른 터미널에서 헬스체크:

```bash
curl http://127.0.0.1:8000/health
```

## 6. 필수 API 예제

### 6.1 활성 시장 확인

```bash
curl -H "X-HYDRA-KEY: my-local-demo-key" http://127.0.0.1:8000/markets
```

### 6.2 저장된 심볼 목록 확인

```bash
curl -H "X-HYDRA-KEY: my-local-demo-key" http://127.0.0.1:8000/data/symbols
```

### 6.3 백테스트 실행

```bash
curl -X POST http://127.0.0.1:8000/backtest/run \
  -H "Content-Type: application/json" \
  -H "X-HYDRA-KEY: my-local-demo-key" \
  -d '{
    "market": "binance",
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "since": 1704067200000,
    "until": 1706745600000
  }'
```

## 7. CLI 예제

```bash
python -m hydra.cli.app status
python -m hydra.cli.app market list-markets
python -m hydra.cli.app market enable binance --mode paper
python -m hydra.cli.app kill
```

## 8. 추천 사용 순서

1. 테스트 통과 확인
2. Lite 프로필 실행
3. 시장 설정 확인
4. 데이터 조회
5. 백테스트 실행
6. 전략/실거래 확장 여부 판단

## 9. 주의사항

- 실거래 키를 넣기 전에 먼저 paper 모드로 확인하세요.
- API 키, 계정번호, 개인 설정은 `.env` 또는 로컬 전용 파일에만 저장하세요.
- FastAPI Swagger UI는 기본 비활성화 상태입니다. API 사용법은 `docs/API_REFERENCE_KO.md`를 참고하세요.
