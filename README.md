# 🌅 Easy Lazy Morning — AI Daily Briefing Agent

> Built for GreenNode Claw-a-thon 2026 | ZaloPay Telco & Global Marketing

## What it does

**Easy Lazy Morning** is a personal AI agent that runs every weekday at 10:15 AM and automatically delivers a structured 3-page morning briefing to the marketer's inbox — before the workday begins.

Every morning it:
1. Scrapes 4 internal Tableau dashboards (Telco MPU, Global SP KPI, TikTok Shop, Promotion Cost) via browser automation over VPN
2. Reads Outlook emails, calendar, and Teams messages from the last 24h
3. Analyzes KPIs using dual-check logic: vs Same Period Last Month (SPLM) + Historical Pacing Curve forecast
4. Cross-references a live SOP sheet for BAU tasks due today
5. Composes a 3-page briefing and sends it via Microsoft Outlook

## Problem it solves

A marketing manager at ZaloPay spends 30–45 minutes each morning manually checking dashboards, emails, and messages before they can plan their day. Easy Lazy Morning compresses this to zero active effort.

## Architecture

```
Local (VPN on) → Browser scrapes Tableau dashboards
              → Microsoft 365 MCP reads Outlook/Teams/Calendar
              → Google Drive MCP reads KPI targets + SOP
              → LangChain agent analyzes + composes briefing
              → Sends 3-page email via Outlook
              → Deployed on GreenNode AgentBase
```

## KPI Analysis Logic

Two independent checks per metric. Final status = worst of the two.

| Check | Method | 🟢 | 🟡 | 🔴 |
|-------|--------|----|----|-----|
| Check A | vs Same Period Last Month | ≥ 0% | -5% to 0% | < -5% |
| Check B | Historical Pacing Curve EOM forecast | ≥ 95% on-track | 85–94% | < 85% |

**Historical Pacing Curve** (not linear): reads 3 months of daily actuals → calculates expected % of monthly total by day N → projects EOM accordingly.

## Briefing Format

- **Page 1 — Telco Performance:** MPU MTD, Projected EOM, FPU, Cost/User, sub-category breakdown (Airtime, Data, Digital Code, Postpaid, OutApp), Promo budget
- **Page 2 — Global & TikTok:** SP payment volume, Telco share, TikTok MPU/FPU/TPV, WoW trend
- **Page 3 — Consolidated Workplan:** Meetings, BAU tasks due today, ad-hoc tasks from email/Teams, suggested daily schedule

## Dashboards

| Dashboard | URL |
|-----------|-----|
| Telco MPU Performance | `https://atlas.vng.com.vn/#/site/ZLPDataServices/views/OverallMPUPerformance/OverallMPUbyUserType` |
| Global SP KPI | `https://atlas.vng.com.vn/#/site/ZLPDataServices/views/SPKPIDashboard/SPKPIDashboard` |
| TikTok Payment Monitoring | `https://atlas.vng.com.vn/#/site/ZLPDataServices/views/TikTokPaymentMonitoring/TikTokPaymentMonitoring` |
| Promotion Cost Summary | `https://atlas.vng.com.vn/#/site/ZLPDataServices/views/PromotionSummary/PromotionSummary` |

## Tech Stack

- **GreenNode AgentBase** — cloud deployment platform (VNG)
- **LangChain** — agent orchestration
- **Microsoft Graph API** — Outlook email, calendar, Teams
- **Claude in Chrome** — browser automation for VPN-protected Tableau dashboards
- **Google Drive MCP** — KPI targets and SOP sheet
- **Docker** — containerized deployment

## Setup

### Prerequisites
- VPN connected to VNG corporate network (for Tableau dashboards)
- Microsoft 365 credentials (Outlook/Teams)
- GreenNode AgentBase account (`GREENNODE_CLIENT_ID` + `GREENNODE_CLIENT_SECRET`)

### Environment Variables
```
LLM_MODEL=
LLM_BASE_URL=
LLM_API_KEY=
MS_TENANT_ID=
MS_CLIENT_ID=
MS_CLIENT_SECRET=
MS_USER_EMAIL=nhint6@vng.com.vn
LARK_APP_ID=
LARK_APP_SECRET=
```

### Run via Docker
```bash
docker build -t easy-lazy-morning .
docker run --env-file .env -p 8080:8080 easy-lazy-morning
```

### Deploy to GreenNode AgentBase
```bash
# Via Claude Code
/agentbase-wizard
```

## Schedule

Runs automatically at **10:15 AM, Monday–Friday** (VPN connects at 10:00 AM, 15-min buffer).
Cron: `15 10 * * 1-5`

## Agent Endpoint

```
https://endpoint-e90e7faa-d43e-4d4e-802f-3d6296a7135c.agentbase-runtime.aiplatform.vngcloud.vn/health
```

## Files

| File | Description |
|------|-------------|
| `SKILL.md` | Agent skill definition — all 11 steps |
| `config.json` | KPI thresholds, dashboard URLs, BAU tasks, schedules |
| `main.py` | LangChain agent server (GreenNode AgentBase format) |
| `Dockerfile` | Container definition for AgentBase deployment |
| `requirements.txt` | Python dependencies |

---

*Easy Lazy Morning 🤖 | ZaloPay Marketing | GreenNode Claw-a-thon 2026*
