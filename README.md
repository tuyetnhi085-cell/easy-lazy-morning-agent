# 🌅 Easy Lazy Morning — AI Daily Briefing Agent

> Built for GreenNode Claw-a-thon 2026 | ZaloPay Telco & Global Marketing

## What it does

**Easy Lazy Morning** is a personal AI agent that runs every weekday at 10:15 AM and automatically compiles a structured 3-page morning briefing — before the workday begins.

Every morning it:
1. Reads today's dashboard PDF sent by Ann to Gmail (Telco MPU, Global SP KPI, TikTok, Promo Budget)
2. Analyzes KPIs using Historical Pacing Curve forecast → EOM projection vs target
3. Reads Gmail emails (last 24h) with smart triage: DM/@mention = action item, rest = FYI
4. Reads Google Calendar for today's meetings and prep notes
5. Reads Microsoft Teams messages with the same triage logic
6. Cross-references a live SOP sheet for BAU tasks due today
7. Compiles a 3-page brief and saves it as a ready-to-read file

## Problem it solves

A marketing manager at ZaloPay spends 30–45 minutes each morning manually checking dashboards, emails, and messages before they can plan their day. Easy Lazy Morning compresses this to zero active effort — open the file, start working.

## Architecture

```
Gmail MCP (tuyetnhi085@gmail.com)
  → Dashboard PDF attachment (sent by Ann each morning)
  → Emails last 24h (smart triage)
  → Google Calendar events today

Microsoft 365 MCP
  → Teams messages last 24h (smart triage)

Google Drive MCP
  → Live SOP sheet (BAU tasks, KPI targets)

Claude Agent (GreenNode AgentBase)
  → KPI analysis: Historical Pacing Curve → EOM projection
  → Triage: flag action only if DM / @mention / direct recipient
  → Compose 3-page brief
  → Save as morning-brief-YYYY-MM-DD.md

Scheduled: cron 15 10 * * 1-5 (10:15 AM weekdays)
```

## KPI Analysis Logic

Single check per metric: Historical Pacing Curve EOM forecast.

**Method:** Pull 3 months of daily actuals → calculate expected % of monthly total achieved by day N → project EOM = MTD_actual / expected_pct × 100

| Status | Condition |
|--------|-----------|
| 🟢 Green | on_track_pct ≥ 95% |
| 🟡 Yellow | 85–94% |
| 🔴 Red | < 85% |

Non-linear deceleration curve:
- Days 1–10: ramp-up, lower daily numbers
- Days 11–20: peak performance window
- Days 21–30: ~35% lower than mid-month average

## Triage Logic

| Source | Flag as 🔴/🟡 action | ⬜ FYI |
|--------|----------------------|--------|
| Gmail | Direct To: Ann, @mention, sole recipient with ask | CC, BCC, group, newsletter |
| Teams | DM to Ann, @mention in group | All other channel messages |
| Lark | DM to Ann, @mention in group | All other messages |

## Briefing Format (3 pages)

**Page 1 — Telco Performance**
MPU MTD → Projected EOM → vs Target (🟢/🟡/🔴) | Sub-categories: Airtime, Data, Digital Code, OutApp, Postpaid | Promo budget: Spend, TPV, %Cost/TPV, CPU

**Page 2 — Global & TikTok**
Global SP Volume MTD → EOM forecast → Telco share % | TikTok: MPU, daily PU, FPU, TPV, MoM% | Proposed actions for 🔴 metrics

**Page 3 — Consolidated Workplan**
Meetings today | 🔴 Must-do (BAU due + action emails/DMs) | 🟡 Should-do | ⬜ FYI | Suggested hourly schedule 10:15→EOD

## Tech Stack

- **GreenNode AgentBase** — cloud deployment & scheduling (VNG)
- **Claude Agent SDK** — agent orchestration (via SKILL.md)
- **Gmail MCP** — dashboard PDF reading, email triage, Google Calendar
- **Microsoft 365 MCP** — Teams messages
- **Google Drive MCP** — KPI targets and SOP sheet
- **Docker** — containerized deployment

## Setup

### Prerequisites
- Gmail MCP connected to `tuyetnhi085@gmail.com`
- Microsoft 365 MCP connected (Teams only)
- Ann sends dashboard PDF to `tuyetnhi085@gmail.com` each morning before 10:15 AM
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

Runs automatically at **10:15 AM, Monday–Friday** (15-min buffer after VPN connects at 10:00 AM).
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
| `main.py` | Agent server (GreenNode AgentBase format) |
| `Dockerfile` | Container definition for AgentBase deployment |
| `requirements.txt` | Python dependencies |

---

*Easy Lazy Morning 🤖 | ZaloPay Marketing | GreenNode Claw-a-thon 2026*
