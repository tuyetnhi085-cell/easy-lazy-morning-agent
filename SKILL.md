# Easy Lazy Morning — Daily Briefing Agent v2.0

> Ann's personal morning agent for ZaloPay Telco & Global marketing.
> Runs each morning: Ann uploads dashboard PDF → agent analyzes KPIs, reads comms, compiles 3-page briefing.

---

## Trigger

Run this skill when:
- The scheduled morning task fires (cron: `15 10 * * 1-5` — 10:15 AM weekdays, after VPN connects at 10:00)
- User says "run my morning brief" / "easy lazy morning" / "morning update"

---

## Prerequisites (must be active)

- **Gmail MCP** connected to tuyetnhi085@gmail.com (email + Google Calendar)
- **Microsoft 365 MCP** connected (Teams messages only)

---

## Step 1 — Request Dashboard PDF from Ann

**Ask Ann to upload today's dashboard PDF:**

> "Chào Ann! Để chạy morning brief, bạn upload file PDF dashboard hôm nay nhé (Telco MPU + Global SP KPI + TikTok + Promo Budget). Kéo thả file vào đây là được 📎"

Wait for Ann to upload the PDF file. Once received, read and extract all numbers visible:

| Dashboard | What to extract |
|-----------|----------------|
| **Telco MPU** | MTD total + sub-cats (Airtime, Data, Digital Code, OutApp, Postpaid): MPU, NPU, FPU, Retain. Daily MTD series if visible. |
| **Promo Budget** | Spend MTD, TPV, %Cost/TPV, CPU — row: Digital Services / Telco |
| **TikTok** | MPU MTD, FPU, NPU, TPV, D-1 daily PU, MoM% by segment (Shop/Live/Ads) |
| **Global SP KPI** | SP Volume MTD, EOM forecast, target, Telco share % |

**If Ann says skip / no PDF available:**
Note "⚠️ Dashboard PDF not provided — brief will use last known data from config.json" and continue.

---

## Step 3 — KPI Analysis: Green / Yellow / Red

One check per metric: Historical Pacing Curve → EOM Projection.

---

### Check — Historical Curve Forecast (EOM Projection)

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

### Status Thresholds

| on_track_pct | Status |
|---|---|
| ≥ 95% | 🟢 Green |
| 85–94% | 🟡 Yellow |
| < 85% | 🔴 Red |

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

## Step 4 — Read Gmail (last 24h)

Use Gmail MCP to read **tuyetnhi085@gmail.com**, afterDateTime=yesterday.
Skip the dashboard PDF email already processed in Step 1.

**Triage rule — only flag as action item if ANY of:**
- Email sent **directly to tuyetnhi085@gmail.com** (To field, not CC/BCC)
- Email **@mentions** Ann by name (@Nhi, @nhint6, @Nhi Nìm Tuyết)
- Ann is the **only or primary recipient** with a clear ask

**Everything else → ⬜ FYI** (group together at the bottom, one line each).

Group action items:
- 🔴 Reply/act today: direct ask, deadline today, approval request
- 🟡 Note & plan: direct ask with flexible deadline

---

## Step 5 — Check Today's Calendar

Use **Google Calendar** via Gmail MCP (tuyetnhi085@gmail.com) — list all events today with time, room, attendees, prep note if needed.

---

## Step 6 — Read Microsoft Teams Messages (last 24h)

Use `chat_message_search`.

**Triage rule — only flag as action item if:**
- **Direct message (DM)** sent specifically to Ann
- Ann is **@mentioned** in a group/channel message

**Everything else → ⬜ FYI** (group together, one line each).

Group action items:
- 🔴 Needs same-day response
- 🟡 Respond within 1–2 days

If Teams connector unavailable → note "⚠️ Teams skipped" and continue.

---

## Step 7 — Read Lark/Feishu Messages (last 24h)

Call Lark API with credentials from AgentBase identity.

**Triage rule — only flag as action item if:**
- **Direct message** to Ann
- Ann is **@mentioned** in a group

**Everything else → ⬜ FYI** (group together, one line each).

If token missing → note "⚠️ Lark skipped" and continue.

---

## Step 8 — Load BAU Tasks & Build Today's Work Schedule

**Primary source:** Read the live SOP sheet via Google Drive MCP:
`https://docs.google.com/spreadsheets/d/1Cukt2MAPnDSnYT-l5OtQkqVc5pYBQ0etx5z7TF4Wzko/edit`

**Fallback:** Read `config.json → bau_tasks` if the sheet is unavailable.

### 8a — Daily tasks (flag every day)
- Dashboard performance check — already done in Step 1 (PDF from Gmail)
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

⚡ AD-HOC TASKS (direct messages / @mentions only):
  🔴 Must do today:
    1. [Task] — Source: [DM/@ email/Teams/Lark]
  🟡 Should do today:
    2. [Task]
  📬 FYI (CC'd, group messages not @, newsletters):
    - [one-liner summary x N items]

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

## Step 10 — Save Brief as File

Save the completed 3-page brief as:
`morning-brief-[YYYY-MM-DD].md` in the Downloads folder.

Surface the file as a card so Ann can open it directly.

---

## Step 11 — Adaptive Intraday Updates

If re-triggered during the day:
1. Re-run Steps 4, 6, 7 only (skip dashboards)
2. Append "⚡ URGENT UPDATE — [HH:MM]" to Page 3 task list
3. Re-prioritize workplan with new information
4. Save updated brief as a new file card

---

## Error Handling

| Situation | Behavior |
|-----------|----------|
| Dashboard PDF not received | Use last known data from config.json, flag ⚠️ |
| Historical data unavailable | Fall back to linear forecast, flag accuracy warning |
| Gmail MCP not connected | Skip Steps 3–4, note in Page 3 |
| Microsoft 365 not connected | Skip Step 6, note in Page 3 |
| Lark token missing | Skip Step 7, note in Page 3 |
| Google Sheets unavailable | Use config.json targets, no historical curve |

---

## Configuration

All thresholds, URLs, credentials, and **monthly baseline tasks** live in: `easy-lazy-morning/config.json`

## Related Skills

- `/agentbase-wizard` — deploy to GreenNode AgentBase
- `/schedule` — set up local morning cron trigger
- `/agentbase-identity` — store Lark API token and Microsoft credentials
