# easy-lazy-morning

Ann's personal morning briefing agent for ZaloPay Telco marketing.
Runs at 10:15 AM weekdays — pulls dashboard data, reads comms, sends briefing to Outlook.

## Prerequisites

- Docker (for local testing and deployment)
- GreenNode IAM Service Account
- Azure AD app with MS Graph permissions (Mail.Read, Calendars.Read, Chat.Read, Mail.Send)
- Tableau credentials for atlas.vng.com.vn
- (Optional) Google service account for Sheets API
- (Optional) Lark App ID + Secret

## Setup

1. Copy env template:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. Configure LLM (GreenNode AIP recommended):
   ```
   LLM_API_KEY=your-aip-key
   LLM_BASE_URL=https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1
   LLM_MODEL=your-model
   ```

## Run via Docker

```bash
docker build -t easy-lazy-morning .
docker run --env-file .env -p 8080:8080 easy-lazy-morning
```

Test trigger:
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"trigger": "manual"}'
```

Health check:
```bash
curl http://localhost:8080/health
```

## Schedule

Cron: `15 10 * * 1-5` — 10:15 AM Monday–Friday (Asia/Ho_Chi_Minh)

## Deploy

Use `/agentbase-deploy` to build, push, and deploy to AgentBase Runtime.
