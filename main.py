import os
from datetime import datetime, timedelta, timezone

import requests
import msal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.config import get_config
from greennode_agentbase import GreenNodeAgentBaseApp, RequestContext, PingStatus
from greennode_agentbase.memory import MemoryClient
from greennode_agentbase.memory.models import MemoryRecordSearchRequest
from greennode_agent_bridge import AgentBaseMemoryEvents

load_dotenv()

app = GreenNodeAgentBaseApp()

# --- Config ---
LLM_MODEL = os.environ.get("LLM_MODEL", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
MEMORY_ID = os.environ.get("MEMORY_ID", "")
MEMORY_STRATEGY_ID = os.environ.get("MEMORY_STRATEGY_ID", "default")

MS_TENANT_ID = os.environ.get("MS_TENANT_ID", "")
MS_CLIENT_ID = os.environ.get("MS_CLIENT_ID", "")
MS_CLIENT_SECRET = os.environ.get("MS_CLIENT_SECRET", "")
MS_USER_EMAIL = os.environ.get("MS_USER_EMAIL", "nhint6@vng.com.vn")

TABLEAU_SERVER_URL = os.environ.get("TABLEAU_SERVER_URL", "https://atlas.vng.com.vn")
TABLEAU_SITE_ID = os.environ.get("TABLEAU_SITE_ID", "ZLPDataServices")
TABLEAU_USERNAME = os.environ.get("TABLEAU_USERNAME", "")
TABLEAU_PASSWORD = os.environ.get("TABLEAU_PASSWORD", "")

LARK_APP_ID = os.environ.get("LARK_APP_ID", "")
LARK_APP_SECRET = os.environ.get("LARK_APP_SECRET", "")
BRIEFING_TO = os.environ.get("BRIEFING_TO", "nhint6@vng.com.vn")

VN_TZ = timezone(timedelta(hours=7))

if not all([LLM_MODEL, LLM_BASE_URL, LLM_API_KEY]):
    raise ValueError("LLM_MODEL, LLM_BASE_URL, and LLM_API_KEY are required.")

llm = ChatOpenAI(model=LLM_MODEL, base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

memory_client = MemoryClient() if MEMORY_ID else None


# --- Auth helpers ---

def _get_actor_id() -> str:
    try:
        config = get_config()
        return config["configurable"].get("actor_id", "morning-briefing")
    except Exception:
        return "morning-briefing"


def _get_ms_token() -> str | None:
    if not all([MS_TENANT_ID, MS_CLIENT_ID, MS_CLIENT_SECRET]):
        return None
    try:
        msal_app = msal.ConfidentialClientApplication(
            MS_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{MS_TENANT_ID}",
            client_credential=MS_CLIENT_SECRET,
        )
        result = msal_app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        return result.get("access_token")
    except Exception:
        return None


def _get_lark_token() -> str | None:
    if not all([LARK_APP_ID, LARK_APP_SECRET]):
        return None
    try:
        resp = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": LARK_APP_ID, "app_secret": LARK_APP_SECRET},
            timeout=10,
        )
        return resp.json().get("tenant_access_token")
    except Exception:
        return None


def _get_tableau_token() -> tuple[str | None, str | None]:
    if not all([TABLEAU_USERNAME, TABLEAU_PASSWORD]):
        return None, None
    try:
        resp = requests.post(
            f"{TABLEAU_SERVER_URL}/api/3.19/auth/signin",
            json={
                "credentials": {
                    "name": TABLEAU_USERNAME,
                    "password": TABLEAU_PASSWORD,
                    "site": {"contentUrl": TABLEAU_SITE_ID},
                }
            },
            timeout=15,
        )
        creds = resp.json().get("credentials", {})
        return creds.get("token"), creds.get("site", {}).get("id")
    except Exception:
        return None, None


# ==================== TOOLS ====================

@tool
def recall_previous_context(query: str) -> str:
    """Recall relevant context from previous briefing runs: KPI history, pending emails, meeting prep, unresolved items.

    Args:
        query: What to look up — e.g. 'MTD MPU last week', 'pending action emails', 'FPU WoW'.
    """
    if not memory_client or not MEMORY_ID:
        return "Memory not configured."
    try:
        namespace = f"/strategies/{MEMORY_STRATEGY_ID}/actors/{_get_actor_id()}"
        results = memory_client.search_memory_records(
            id=MEMORY_ID,
            namespace=namespace,
            request=MemoryRecordSearchRequest(query=query, limit=20),
        )
        if not results:
            return "No previous context found."
        return "\n".join(f"- {r.memory}" for r in results)
    except Exception as e:
        return f"Memory recall failed: {e}"


@tool
def save_briefing_context(facts: str) -> str:
    """Save key facts from today's briefing to memory for use in future runs.

    Args:
        facts: Pipe-separated facts to save. Example:
               'MTD MPU 2026-06-14: 1,250,000 total|FPU this week: 45,200|Pending: reply to Minh re budget by EOD'
    """
    if not memory_client or not MEMORY_ID:
        return "Memory not configured."
    try:
        namespace = f"/strategies/{MEMORY_STRATEGY_ID}/actors/{_get_actor_id()}"
        fact_list = [f.strip() for f in facts.split("|") if f.strip()]
        memory_client.insert_memory_records_directly(
            id=MEMORY_ID,
            namespace=namespace,
            request=fact_list,
        )
        return f"Saved {len(fact_list)} facts to memory."
    except Exception as e:
        return f"Memory save failed: {e}"


@tool
def fetch_dashboard_data(dashboard_name: str) -> str:
    """Fetch KPI data from Tableau dashboard on atlas.vng.com.vn via REST API.

    Args:
        dashboard_name: One of: mpu_performance, sp_kpi, tiktok_payment, promo_cost
    """
    dashboard_map = {
        "mpu_performance": "OverallMPUbyUserType",
        "sp_kpi": "SPKPIDashboard",
        "tiktok_payment": "TikTokPaymentMonitoring",
        "promo_cost": "PromotionSummary",
    }
    view_name = dashboard_map.get(dashboard_name)
    if not view_name:
        return f"Unknown dashboard: {dashboard_name}. Use: mpu_performance, sp_kpi, tiktok_payment, promo_cost"

    token, site_id = _get_tableau_token()
    if not token:
        return f"⚠️ Dashboard '{dashboard_name}' unavailable — Tableau credentials not configured. Use last known values from memory."

    try:
        headers = {"X-Tableau-Auth": token, "Accept": "application/json"}
        views_resp = requests.get(
            f"{TABLEAU_SERVER_URL}/api/3.19/sites/{site_id}/views",
            headers=headers,
            params={"filter": f"viewUrlName:eq:{view_name}"},
            timeout=15,
        )
        views = views_resp.json().get("views", {}).get("view", [])
        if not views:
            return f"⚠️ View '{view_name}' not found on Tableau."

        view_id = views[0]["id"]
        data_resp = requests.get(
            f"{TABLEAU_SERVER_URL}/api/3.19/sites/{site_id}/views/{view_id}/data",
            headers=headers,
            timeout=20,
        )
        return data_resp.text[:3000] if data_resp.ok else f"⚠️ Data fetch failed: {data_resp.status_code}"
    except Exception as e:
        return f"⚠️ Dashboard error: {e}"


@tool
def read_outlook_emails() -> str:
    """Read Outlook emails from the last 24 hours. Flags action items by keyword."""
    token = _get_ms_token()
    if not token:
        return "⚠️ MS Graph unavailable — skipping email."

    since = (datetime.now(VN_TZ) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(
            f"https://graph.microsoft.com/v1.0/users/{MS_USER_EMAIL}/messages",
            headers=headers,
            params={
                "$filter": f"receivedDateTime ge {since}",
                "$select": "subject,from,receivedDateTime,bodyPreview,isRead",
                "$top": 25,
                "$orderby": "receivedDateTime desc",
            },
            timeout=15,
        )
        emails = resp.json().get("value", [])
        if not emails:
            return "No emails in last 24h."

        action_keywords = ["please", "cần", "urgent", "EOD", "deadline", "confirm", "approval", "review", "action required"]
        lines = []
        for e in emails:
            sender = e.get("from", {}).get("emailAddress", {}).get("name", "Unknown")
            subject = e.get("subject", "")
            preview = e.get("bodyPreview", "")[:150]
            received = e.get("receivedDateTime", "")[:16].replace("T", " ")
            flagged = any(k.lower() in subject.lower() or k.lower() in preview.lower() for k in action_keywords)
            flag = "🔴 ACTION" if flagged else "⬜ FYI"
            lines.append(f"{flag} | {received} | From: {sender}\nSubject: {subject}\nPreview: {preview}")
        return "\n---\n".join(lines)
    except Exception as e:
        return f"⚠️ Email error: {e}"


@tool
def read_calendar() -> str:
    """Read today's calendar meetings from Outlook."""
    token = _get_ms_token()
    if not token:
        return "⚠️ MS Graph unavailable — skipping calendar."

    now = datetime.now(VN_TZ)
    start = now.strftime("%Y-%m-%dT00:00:00+07:00")
    end = now.strftime("%Y-%m-%dT23:59:59+07:00")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(
            f"https://graph.microsoft.com/v1.0/users/{MS_USER_EMAIL}/calendarView",
            headers=headers,
            params={
                "startDateTime": start,
                "endDateTime": end,
                "$select": "subject,start,end,attendees,location,isOnlineMeeting,onlineMeetingUrl",
                "$orderby": "start/dateTime",
                "$top": 20,
            },
            timeout=15,
        )
        events = resp.json().get("value", [])
        if not events:
            return "No meetings today."

        lines = []
        for e in events:
            subject = e.get("subject", "")
            t_start = e.get("start", {}).get("dateTime", "")[:16].replace("T", " ")
            t_end = e.get("end", {}).get("dateTime", "")[:16].replace("T", " ")
            attendees = [a["emailAddress"]["name"] for a in e.get("attendees", [])[:6]]
            location = e.get("location", {}).get("displayName", "") or e.get("onlineMeetingUrl", "Teams")
            lines.append(f"{t_start}–{t_end} | {subject}\nAttendees: {', '.join(attendees)}\nLocation: {location}")
        return "\n---\n".join(lines)
    except Exception as e:
        return f"⚠️ Calendar error: {e}"


@tool
def read_teams_messages() -> str:
    """Read Microsoft Teams DMs and channel @mentions from the last 24 hours."""
    token = _get_ms_token()
    if not token:
        return "⚠️ MS Graph unavailable — skipping Teams."

    since = datetime.now(VN_TZ) - timedelta(hours=24)
    try:
        headers = {"Authorization": f"Bearer {token}"}
        chats_resp = requests.get(
            f"https://graph.microsoft.com/v1.0/users/{MS_USER_EMAIL}/chats",
            headers=headers,
            params={"$top": 10},
            timeout=15,
        )
        chats = chats_resp.json().get("value", [])
        lines = []
        for chat in chats[:6]:
            chat_id = chat.get("id")
            msgs_resp = requests.get(
                f"https://graph.microsoft.com/v1.0/chats/{chat_id}/messages",
                headers=headers,
                params={"$top": 5, "$orderby": "createdDateTime desc"},
                timeout=10,
            )
            for m in msgs_resp.json().get("value", []):
                created = m.get("createdDateTime", "")
                if created:
                    msg_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if msg_dt.astimezone(VN_TZ) < since:
                        continue
                sender = m.get("from", {}).get("user", {}).get("displayName", "Unknown")
                body = m.get("body", {}).get("content", "")[:200]
                lines.append(f"{sender}: {body}")

        return "\n---\n".join(lines) if lines else "No Teams messages in last 24h."
    except Exception as e:
        return f"⚠️ Teams error: {e}"


@tool
def read_lark_messages() -> str:
    """Read Lark/Feishu messages from the last 24 hours."""
    lark_token = _get_lark_token()
    if not lark_token:
        return "⚠️ Lark skipped — credentials not configured."

    try:
        since_ts = int((datetime.now(VN_TZ) - timedelta(hours=24)).timestamp())
        headers = {"Authorization": f"Bearer {lark_token}"}
        resp = requests.get(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            headers=headers,
            params={"start_time": str(since_ts), "page_size": 20},
            timeout=15,
        )
        items = resp.json().get("data", {}).get("items", [])
        if not items:
            return "No Lark messages in last 24h."

        lines = []
        for m in items:
            sender = m.get("sender", {}).get("id", "Unknown")
            body = m.get("body", {}).get("content", "")[:200]
            ts = m.get("create_time", "")
            lines.append(f"[{ts}] {sender}: {body}")
        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ Lark error: {e}"


@tool
def send_morning_briefing(subject: str, body: str) -> str:
    """Send the composed morning briefing email via Outlook.

    Args:
        subject: Email subject, e.g. '🌅 Morning Brief — Monday, 2026-06-14 | Telco MPU: 🟡'
        body: Full briefing content (plain text).
    """
    token = _get_ms_token()
    if not token:
        return "⚠️ Cannot send — MS Graph not configured."

    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": BRIEFING_TO}}],
            },
            "saveToSentItems": True,
        }
        resp = requests.post(
            f"https://graph.microsoft.com/v1.0/users/{MS_USER_EMAIL}/sendMail",
            headers=headers,
            json=payload,
            timeout=15,
        )
        if resp.status_code == 202:
            return f"✅ Briefing sent to {BRIEFING_TO}"
        return f"⚠️ Send failed ({resp.status_code}): {resp.text[:200]}"
    except Exception as e:
        return f"⚠️ Send error: {e}"


# ==================== AGENT ====================

checkpointer = AgentBaseMemoryEvents(memory_id=MEMORY_ID) if MEMORY_ID else None

agent = create_agent(
    llm,
    tools=[
        recall_previous_context,
        save_briefing_context,
        fetch_dashboard_data,
        read_outlook_emails,
        read_calendar,
        read_teams_messages,
        read_lark_messages,
        send_morning_briefing,
    ],
    system_prompt=(
        "You are the Easy Lazy Morning agent for Ann at ZaloPay Telco Marketing. "
        "Run the full morning briefing by following these steps IN ORDER:\n\n"
        "1. recall_previous_context('MTD MPU FPU KPI last run pending items') — get history\n"
        "2. fetch_dashboard_data('mpu_performance') — Telco MPU, FPU, RPU, Churn\n"
        "3. fetch_dashboard_data('sp_kpi') — SP payment volume, Telco contribution\n"
        "4. fetch_dashboard_data('tiktok_payment') — TikTok MPU/FPU, TPV\n"
        "5. fetch_dashboard_data('promo_cost') — promo spend MTD, Cost/User vs plan\n"
        "6. read_outlook_emails — flag action items\n"
        "7. read_calendar — today's meetings\n"
        "8. read_teams_messages — DMs and @mentions\n"
        "9. read_lark_messages — Lark messages\n"
        "10. Analyze all KPI data using two checks per metric:\n"
        "    Check A (vs SPLM): splm_gap = (MTD_actual - SPLM_actual) / SPLM_actual * 100\n"
        "      🟢 >= 0% | 🟡 -5% to 0% | 🔴 < -5%\n"
        "    Check B (on-track): projected_eom = MTD_actual / days_elapsed * total_working_days\n"
        "      on_track = projected_eom / monthly_target * 100\n"
        "      🟢 >= 95% | 🟡 85–94% | 🔴 < 85%\n"
        "    Standalone alerts: FPU WoW drop > 10% 🔴, Cost/User > 130% of plan 🔴, notification CR < 0.48% flag\n"
        "11. Compose the briefing using the Morning Brief template (KPI status, meetings, emails, messages, workplan)\n"
        "12. send_morning_briefing(subject, body)\n"
        "13. save_briefing_context with today's KPI values, pending action items, meeting prep notes (pipe-separated)\n\n"
        "If any source returns ⚠️, note it in the briefing and continue. Never stop on a single failure.\n"
        "Use recalled context from memory as fallback values when dashboard data is unavailable."
    ),
    checkpointer=checkpointer,
)


@app.entrypoint
def handler(payload: dict, context: RequestContext) -> dict:
    today = datetime.now(VN_TZ).strftime("%Y-%m-%d")
    trigger = payload.get("trigger", "scheduled")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": f"Run Easy Lazy Morning briefing for {today}. Trigger: {trigger}."}]},
        config={
            "configurable": {
                "actor_id": "morning-briefing",
                "thread_id": today,
            }
        },
    )
    ai_message = result["messages"][-1]
    return {
        "status": "success",
        "response": ai_message.content,
        "date": today,
        "timestamp": datetime.now(VN_TZ).isoformat(),
    }


@app.ping
def health_check() -> PingStatus:
    return PingStatus.HEALTHY


if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
