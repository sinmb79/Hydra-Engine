# HYDRA n8n Integration / HYDRA n8n 연동

Meta description: n8n workflow for HYDRA health checks, loss alerts, and optional automatic kill-switch execution.
Labels: hydra, n8n, monitoring, telegram, fastapi, automation

## 한국어

이 연동이 존재하는 이유는 하나입니다. 거래 시스템에서 가장 위험한 실패는 대개 대형 장애가 아니라, 리스크가 조금씩 비정상으로 기울어도 아무도 눈치채지 못하는 상태입니다. 이 워크플로우는 매매를 자동화하지 않습니다. 대신 HYDRA API를 관측하고, 상태와 손익을 요약하고, 임계치를 넘기기 전에 사람과 시스템에 경고를 보냅니다.

역설적으로 말하면, 트레이딩 자동화에서 가장 가치 있는 자동화는 가속기가 아니라 브레이크인 경우가 많습니다.

### 포함 파일

- `workflow.json`: n8n에서 바로 import 가능한 HYDRA 모니터링 워크플로우
- `README.md`: 설치, 설정, 운영 가이드

### 워크플로우가 하는 일

1. 5분마다 실행되며, 수동 테스트 트리거도 함께 제공합니다.
2. HYDRA의 `/health`, `/status`, `/risk`, `/pnl` 엔드포인트를 호출합니다.
3. 서비스 상태, 일일 손익, 오픈 포지션, collector 상태를 묶어 경고 컨텍스트를 생성합니다.
4. 주의가 필요한 경우에만 Telegram 알림을 보냅니다.
5. 선택적으로 일일 손실 임계치가 깨졌을 때 `/killswitch`를 호출합니다.

### 왜 HTTP 방식인가

HYDRA는 이미 필요한 관측 API를 갖고 있습니다. 그래서 n8n이 내부 셸을 직접 제어하는 구조보다, 외부에서 관찰하고 오케스트레이션하는 구조가 더 안전합니다.

이 선택의 장점은 분명합니다.

- HYDRA는 실행과 리스크 엔진에 집중합니다.
- n8n은 스케줄링, 요약, 알림, 비상 제동에 집중합니다.
- 저장소에는 자동화가 추가되지만, 핵심 거래 로직은 오염되지 않습니다.

### 설정 방법

#### 1. 워크플로우 import

n8n에서:

1. **Workflows**로 이동합니다.
2. **Import from File**를 선택합니다.
3. `n8n/workflow.json`을 불러옵니다.

#### 2. 환경 변수 설정

n8n 실행 환경에 아래 값을 설정합니다.

```bash
HYDRA_BASE_URL=http://127.0.0.1:8000
HYDRA_API_KEY=replace-with-your-real-key
HYDRA_ALERT_LOSS_PCT=-0.03
HYDRA_AUTO_KILL_SWITCH=false
TELEGRAM_CHAT_ID=123456789
```

주의할 점:

- `HYDRA_BASE_URL`은 n8n 런타임에서 실제로 접근 가능한 HYDRA 주소여야 합니다.
- `HYDRA_ALERT_LOSS_PCT`는 문자열 `%`가 아니라 소수 비율입니다. `-0.03`은 `-3%`입니다.
- `HYDRA_AUTO_KILL_SWITCH=false`로 시작하면 알림 전용 모드로 운영할 수 있습니다.
- `HYDRA_API_KEY`는 HYDRA 쪽 `.env`에 설정된 값과 동일해야 합니다.

만약 n8n은 Docker 안에서 돌고 HYDRA는 Windows 호스트에서 실행 중이라면, `127.0.0.1` 대신 보통 아래처럼 잡아야 합니다.

```bash
HYDRA_BASE_URL=http://host.docker.internal:8000
```

#### 3. Telegram 자격 증명 연결

이 워크플로우는 n8n 기본 Telegram 노드로 알림을 전송합니다.

1. import한 워크플로우에서 Telegram 노드를 엽니다.
2. Telegram credential을 생성하거나 연결합니다.
3. `TELEGRAM_CHAT_ID`는 환경 변수로 유지해 두면 환경 이동 시 워크플로우 본문을 수정할 필요가 없습니다.

### 어떤 상황에서 경고하는가

아래 중 하나라도 성립하면 attention 상태로 간주합니다.

- `/health` 상태가 `ok`가 아님
- kill switch가 이미 활성화됨
- 일일 손익이 `HYDRA_ALERT_LOSS_PCT` 아래로 하락함
- collector 상태값 중 `error:`로 시작하는 항목이 있음
- 모니터링용 API 호출 자체가 실패함

자동 kill switch는 더 좁게 동작합니다.

- `HYDRA_AUTO_KILL_SWITCH=true`일 때만 실행됩니다.
- 일일 손실 임계치가 깨졌을 때만 실행됩니다.
- 이미 kill switch가 active인 경우 중복 실행하지 않습니다.
- 모니터링 호출 자체가 실패하는 상황에서는 블라인드 자동 실행을 피합니다.

### 권장 롤아웃

처음에는 반드시 alert-only 모드로 시작하는 편이 좋습니다.

1. 워크플로우를 import합니다.
2. `HYDRA_AUTO_KILL_SWITCH=false`로 둡니다.
3. 수동 실행으로 Telegram 메시지가 잘 오는지 확인합니다.
4. 몇 사이클 자동 실행을 관찰합니다.
5. 알림 문구와 조건이 기대와 맞을 때만 auto kill을 켭니다.

### 최소 변경 원칙

이 연동은 가장 작은 단위로 추가됐습니다.

- `hydra/` 코드 변경 없음
- 거래 실행 로직 변경 없음
- 별도 webhook handler 없음

자동화가 엔진 바깥에 머물수록, 엔진은 더 신뢰하기 쉬워집니다.

## English

This integration exists for one reason: in trading systems, the most dangerous failure is often not a dramatic outage but a quiet normalization of risk. The workflow does not automate trading. It watches HYDRA's API, summarizes health and PnL, and escalates before drift becomes damage.

The counterintuitive truth is the useful one: in trading infrastructure, the most valuable automation is often the brake, not the accelerator.

### Included files

- `workflow.json`: import-ready HYDRA monitoring workflow for n8n
- `README.md`: setup and operating guide

### What the workflow does

1. Runs every 5 minutes, with a manual trigger for testing.
2. Calls HYDRA's `/health`, `/status`, `/risk`, and `/pnl` endpoints.
3. Builds an alert context from service health, daily PnL, open positions, and collector state.
4. Sends Telegram notifications only when attention is required.
5. Optionally calls `/killswitch` when the daily loss threshold is breached.

### Why HTTP instead of shell execution

HYDRA already exposes the required API surface. That makes an external orchestration pattern safer than letting n8n control the engine through host shell commands.

The separation is intentional:

- HYDRA remains the execution and risk engine.
- n8n becomes the scheduling, summarization, alerting, and emergency brake layer.
- The repository gains automation without contaminating trading logic.

### Setup

#### 1. Import the workflow

In n8n:

1. Open **Workflows**.
2. Choose **Import from File**.
3. Import `n8n/workflow.json`.

#### 2. Configure environment variables

Set these in the n8n runtime:

```bash
HYDRA_BASE_URL=http://127.0.0.1:8000
HYDRA_API_KEY=replace-with-your-real-key
HYDRA_ALERT_LOSS_PCT=-0.03
HYDRA_AUTO_KILL_SWITCH=false
TELEGRAM_CHAT_ID=123456789
```

Important notes:

- `HYDRA_BASE_URL` must be reachable from the n8n runtime.
- `HYDRA_ALERT_LOSS_PCT` is a decimal ratio, not a percentage string. `-0.03` means `-3%`.
- `HYDRA_AUTO_KILL_SWITCH=false` keeps the workflow in alert-only mode.
- `HYDRA_API_KEY` must match the key HYDRA loads from its own `.env`.

If n8n runs in Docker while HYDRA runs on the Windows host, `127.0.0.1` is usually wrong. In that case, use:

```bash
HYDRA_BASE_URL=http://host.docker.internal:8000
```

#### 3. Attach Telegram credentials

The workflow uses the built-in n8n Telegram node for notifications.

1. Open either Telegram node in the imported workflow.
2. Create or attach a Telegram credential.
3. Keep `TELEGRAM_CHAT_ID` as an environment variable so the workflow remains portable across environments.

### When the workflow raises attention

It enters attention mode when any of the following becomes true:

- `/health` is no longer `ok`
- the kill switch is already active
- daily PnL falls below `HYDRA_ALERT_LOSS_PCT`
- a collector status starts with `error:`
- one of the monitoring API calls fails

Automatic kill-switch execution is intentionally narrower:

- it only runs when `HYDRA_AUTO_KILL_SWITCH=true`
- it only runs on a daily loss threshold breach
- it does not run if HYDRA already reports the kill switch as active
- it does not run when the monitoring calls themselves are failing

### Recommended rollout

Start in alert-only mode first:

1. Import the workflow.
2. Keep `HYDRA_AUTO_KILL_SWITCH=false`.
3. Run the manual trigger and confirm Telegram delivery.
4. Observe a few scheduled cycles.
5. Enable auto kill only after the alert wording and thresholds match your operating expectations.

### Minimal-change rule

This integration was added in the smallest viable way:

- no changes to `hydra/`
- no changes to execution logic
- no extra webhook handlers

When automation stays outside the engine, the engine stays easier to trust.
