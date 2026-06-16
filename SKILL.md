# Easy Lazy Morning — Daily Briefing Agent v2.0

> Ann's personal morning agent for ZaloPay Telco & Global marketing.
> Runs each morning to pull dashboard data, analyze KPIs, read comms, and send a 3-page briefing to Outlook.

---

## Trigger

Run this skill when:
- The scheduled morning task fires (cron: `15 10 * * 1-5` — 10:15 AM weekdays, after VPN connects at 10:00)
- User says "run my morning brief" / "easy lazy morning" / "morning update"

---

## Prerequisites (must be active)

- VPN connected to VNG corporate network (required for atlas.vng.com.vn dashboards)
- Microsoft 365 MCP connected (Outlook email, Teams, Calendar)
- Google Drive MCP connected (MKT plan Google Sheets)
- Claude in Chrome: browser open and logged into atlas.vng.com.vn

---

## Step 1 — Read Plan Targets & Historical Data from Google Sheets

Use Google Drive MCP to read from both planning sheets.

**Telco MKT Plan:** `https://docs.google.com/spreadsheets/d/1DK7nI3CuTFHCWUtbAvvl5P8SDt6Y6uoF_bcrE3DEixc/`

**TikTok MKT Plan:** `https://docs.google.com/spreadsheets/d/1DK7nI3CuTFHCWUtbAvvl5P8SDt6Y6uoF_bcrE3DEixc/`

Extract for EACH metric (Telco MPU, TikTok MPU, FPU, Cost/user):
- Monthly plan target (current month)
- **Historical daily actuals for the past 3 months** — used to build the forecast curve
- Monthly baseline tasks scheduled for this month (recurring: reports, campaign launches, reviews)
- Deadlines or milestones this week

If the sheet is unavailable, use `config.json` targets as fallback. Note forecast accuracy will be reduced.

---

## Step 2 — Scrape All Dashboards via Browser Automation

Navigate to each dashboard, wait for full load, extract all visible numbers.

### Dashboard Group A — TELCO

**Telco MPU Performance**
URL: `https://atlas.vng.com.vn/#/site/ZLPDataServices/views/OverallMPUPerformance/OverallMPUbyUserType`

Extract (filter: Team=Digital Services, Category=Telco):
- MTD MPU total + by sub-category (Airtime, Data, Digital Code, Postpaid, OutApp)
- NPU, FPU (exclude NPU), Retain per sub-category
- Cut-off date shown on dashboard

**Promotion Cost Summary** (Telco portion)
URL: `https://atlas.vng.com.vn/#/site/ZLPDataServices/views/PromotionSummary/PromotionSummary`

Extract:
- Total promo spend MTD (Telco)
- Cost/user ratio vs plan
- Budget consumed % and remaining
- Any campaigns approaching budget cap

---

### Dashboard Group B — GLOBAL & TIKTOK

**Global SP KPI**
URL: `https://atlas.vng.com.vn/#/site/ZLPDataServices/views/SPKPIDashboard/SPKPIDashboard`

Extract:
- Overall SP payment volume MTD
- Telco category contribution % of total SP
- Top performing SP categories
- MoM trend flag

**TikTok Payment Monitoring**
URL: `https://atlas.vng.com.vn/#/site/ZLPDataServices/views/TikTokPaymentMonitoring/TikTokPaymentMonitoring`

Extract:
- TikTok MPU MTD (total)
- TikTok FPU and NPU
- TPV (total payment volume)
- WoW and MoM trend
- Any anomaly or drop flags on dashboard

---

**If VPN not active or dashboards return login page:**
Skip Step 2, note "⚠️ Dashboard unavailable — VPN not connected", continue from Step 3.

---

## Step 3 — KPI Analysis: Green / Yellow / Red

Run two checks per metric. Final status = worst of the two.

---

### Check A — vs Same Period Last Month (SPLM)

Compare today's MTD actual vs same calendar day last month.

```
splm_gap_pct = (MTD_actual_this_month - MTD_actual_same_day_last_month)
               / MTD_actual_same_day_last_month * 100
```

- 🟢 ≥ 0% (at or above last month)
- 🟡 -5% to 0% (slightly behind, watch)
- 🔴 < -5% (meaningfully below last month)

---

### Check B — Historical Curve Forecast (EOM Projection)

**⚠️ Do NOT use simple linear projection.** Performance within a month is non-linear:
- Early month (day 1–7): ramp-up, lower daily numbers
- Mid month (day 8–20): peak performance window
- Late month (day 21+): uplift fatigue, diminishing returns, lower daily numbers

**Correct method — Historical Pacing Curve:**

```
Step 1: Pull daily actuals for same month last year (or last 3 months if YoY unavailable)
Step 2: For each historical month, calculate % of final monthly total achieved by day N
        historical_pacing[day_N] = sum(day_1..day_N) / monthly_total * 100
Step 3: Average across 3 months → expected_pacing_pct[today]
Step 4: projected_eom = MTD_actual_today / expected_pacing_pct[today] * 100
Step 5: on_track_pct = projected_eom / monthly_kpi_target * 100
```

**Example:** If historically by day 13, we achieve 47% of monthly total, and today's MTD = 1.16M with target 2M:
- Expected MTD at day 13 = 2M × 47% = 940K
- Actual = 1.16M → running 23% ahead of historical pace 🟢
- Projected EOM = 1.16M / 0.47 = 2.47M

Report both: `Projected EOM` AND `vs historical pace`.

Status thresholds:
- 🟢 on_track_pct ≥ 95%
- 🟡 85–94%
- 🔴 < 85%

If historical data unavailable → fall back to linear projection but flag: "⚠️ Using linear projection — historical data unavailable, accuracy reduced."

---

### Combined Status

| Check A (SPLM) | Check B (Forecast) | Final |
|---|---|---|
| 🟢 | 🟢 | 🟢 Green |
| 🟡 | 🟢 | 🟡 Yellow |
| 🟢 | 🟡 | 🟡 Yellow |
| 🔴 | any | 🔴 Red |
| any | 🔴 | 🔴 Red |

---

### Standalone Alerts (run for all metrics regardless of status)

- FPU WoW drop > 10% → 🔴 flag with investigation prompts
- Cost/user > 130% of plan → 🔴 budget alert
- TikTok campaign budget alert email received → 🔴 flag with campaign name
- Notification CR% < 0.48% baseline → flag

---

### For each 🔴, propose 2–3 actions:
- Activate emergency push notification campaign
- Accelerate airtime/data/TikTok voucher redemption push
- Escalate to partner for co-funding or promotion extension
- Reallocate budget from lower-performing scheme
- A/B test notification content to recover CR%

---

## Step 4 — Read Outlook Emails (last 24h)

Use `outlook_email_search` — filter by action keywords: "please", "cần", "urgent", "by EOD", "deadline", "confirm", "approval", "action required"

Group: 🔴 Reply today / 🟡 Read and note / ⬜ FYI

---

## Step 5 — Check Today's Calendar

Use `outlook_calendar_search` — list all meetings with time, attendees, prep notes needed.

---

## Step 6 — Read Microsoft Teams Messages (last 24h)

Use `chat_message_search` — DMs and @mentions. Flag same-day responses needed.

---

## Step 7 — Read Lark/Feishu Messages (last 24h)

Call Lark API with credentials from AgentBase identity.
If token missing → note "⚠️ Lark skipped" and continue.

---

## Step 8 — Load BAU Tasks & Build Today's Work Schedule

**Primary source:** Read the live SOP sheet via Google Drive MCP:
`https://docs.google.com/spreadsheets/d/1Cukt2MAPnDSnYT-l5OtQkqVc5pYBQ0etx5z7TF4Wzko/edit`

**Fallback:** Read `config.json → bau_tasks` if the sheet is unavailable.

### 8a — Daily tasks (flag every day)
- Dashboard performance check (atlas.vng.com.vn — already done in Step 2)
- Noti for tomorrow: must be set before **18:00 today**. Check if today's noti was already sent.

### 8b — Weekly tasks (flag on Monday)
- If today is **Monday**: flag TikTok Shop external perf check (Hạnh's update) + Traveloka email to PIC.

### 8c — Monthly-by-date tasks (cross-reference today's date)

| Day of month | What's due |
|---|---|
| 15th | Send NEXT month's external plan → TikTok Shop (Lark + email) + Traveloka (email) + FA approval request |
| 20th | Lock NEXT month's internal plan → FA final email + update Global sheet + request data analysis email |
| 25–26th | Register: Noti slots / Home Headers / Social booking / UGC / Request design banners (Trello, SLA 3d) |
| 26th | Request user segment from ZDS (SLA 3d, email [Global Marketing] Request lấy tập...) |
| 27th | Send all Ops setup Jira requests (SLA 3d) + camp renewals + self-managed CRM setup + ads requests |
| 29th | Monthly report: analyze M performance, draft M+1 plan |

**Logic:**
1. If today = due date → flag as 🔴 **Due today**
2. If today is within 3 days before due date → flag as 🟡 **Due soon (N days)**
3. If today is past due date → flag as 🔴 **Overdue**
4. Otherwise → include in monthly overview only (don't clutter Page 3)

### 8d — Custom deadlines
Check `config.json → bau_tasks → custom_deadlines` for any one-off due dates.

**Key context:** These BAU tasks form the background schedule every month. Ad-hoc tasks from email/Teams/KPI alerts (Steps 4–6) are prioritized ON TOP of — not instead of — these standing commitments.

---

## Step 9 — Compose the 3-Page Morning Briefing

**Subject:** 🌅 Morning Brief — [Weekday, Date] | Telco [🟢/🟡/🔴] | Global [🟢/🟡/🔴]

---

### 📄 PAGE 1 — TELCO

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 PAGE 1 — TELCO PERFORMANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MPU MTD:    [actual]  /  Proj EOM: [projected]  /  Target: [plan]
            vs SPLM: [gap%]  |  vs hist pace: [+/-X%]  [🟢/🟡/🔴]

FPU:        [this week] vs last week [change%]  [🟢/🔴]
Cost/User:  [actual] vs plan [ratio%]  [🟢/🔴]

Sub-category breakdown:
  Airtime      [MPU]  FPU:[x]  NPU:[x]  Retain:[x]
  Data         [MPU]  FPU:[x]  NPU:[x]  Retain:[x]
  Digital Code [MPU]  FPU:[x]  NPU:[x]  Retain:[x]
  Postpaid     [MPU]  FPU:[x]  NPU:[x]  Retain:[x]
  OutApp       [MPU]  FPU:[x]  NPU:[x]  Retain:[x]

Promo Budget:
  Spend MTD: [x]  /  Budget: [x]  /  Remaining: [x]  ([%] consumed)
  [🔴 Budget alert if any campaign approaching cap]

[🔴 Actions if Red:]
• [Metric] — [Reason] — [Top 2 actions]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 📄 PAGE 2 — GLOBAL & TIKTOK

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 PAGE 2 — GLOBAL & TIKTOK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GLOBAL SP KPI:
  SP Volume MTD:  [actual]  MoM: [trend%]
  Telco share:    [%] of total SP  [vs last month: +/-x%]

TIKTOK SHOP:
  MPU MTD:    [actual]  /  Proj EOM: [projected]  /  Target: [plan]
              vs SPLM: [gap%]  |  vs hist pace: [+/-x%]  [🟢/🟡/🔴]
  FPU:        [x]   NPU: [x]   TPV: [x]
  WoW trend:  [+/-x%]

[🔴 Actions if Red:]
• [Metric] — [Reason] — [Top 2 actions]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 📄 PAGE 3 — TASK CONSOLIDATION

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🗓️ PAGE 3 — CONSOLIDATED WORKPLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 MEETINGS TODAY ([N] meetings):
  [HH:MM] — [Title] — [Attendees] — [prep note if needed]

📋 MONTHLY BASELINE (week [N] of [M]):
  ✅ Done:    [completed baseline tasks this month]
  🔲 This week: [baseline tasks due this week]
  ⚠️ Overdue: [any baseline tasks past due]

⚡ AD-HOC TASKS TODAY (from email + Teams + KPI alerts):
  🔴 Must do today:
    1. [Task] — Source: [email/Teams/KPI]
    2. [Task]
  🟡 Should do today:
    3. [Task]
    4. [Task]
  📬 Can defer:
    5. [Task] — defer to [day]

🗓️ SUGGESTED SCHEDULE:
  10:15–11:00  [highest priority task]
  11:00–12:00  [second priority / meeting]
  14:00–15:00  [baseline task or follow-up]
  15:00–16:00  [third priority]
  EOD          [any report or deadline today]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Easy Lazy Morning 🤖 | ZaloPay Marketing
Auto-generated: [timestamp] | VPN: ✅/⚠️ | Dashboard: ✅/⚠️
```

---

## Step 10 — Send via Outlook

Send 3-page briefing to: **nhint6@vng.com.vn**

If send fails → save as `morning-brief-[YYYY-MM-DD].md` and surface as file card.

---

## Step 11 — Adaptive Intraday Updates

If re-triggered during the day:
1. Re-run Steps 4, 6, 7 only (skip dashboards)
2. Append "⚡ URGENT UPDATE — [HH:MM]" to Page 3 task list
3. Re-prioritize workplan with new information
4. Send short update: subject "⚡ Update [HH:MM]: [summary]"

---

## Error Handling

| Situation | Behavior |
|-----------|----------|
| VPN not active | Skip Step 2, note in all 3 pages |
| Historical data unavailable | Fall back to linear forecast, flag accuracy warning |
| Microsoft 365 not connected | Skip Steps 4–6, note in Page 3 |
| Lark token missing | Skip Step 7, note in Page 3 |
| Google Sheets unavailable | Use config.json targets, no historical curve |
| Outlook send fails | Save .md and surface to user |

---

## Configuration

All thresholds, URLs, credentials, and **monthly baseline tasks** live in: `easy-lazy-morning/config.json`

## Related Skills

- `/agentbase-wizard` — deploy to GreenNode AgentBase
- `/schedule` — set up local morning cron trigger
- `/agentbase-identity` — store Lark API token and Microsoft credentials
