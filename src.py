import os
from langchain_google_genai import ChatGoogleGenerativeAI
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Optional, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from email.message import EmailMessage
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display
import base64
from pydantic import BaseModel, Field

os.environ["GOOGLE_API_KEY"] = ""

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)


members: List[str] = [
    "life_advisor",
    "health_coach",
    "email_manager",
    "calendar_manager",
]


class Route(BaseModel):
    step: Literal[*members] = Field(
        None, description="The next step in the routing process"
    )


router = llm.with_structured_output(Route)
SCOPES_CALENDAR = ["https://www.googleapis.com/auth/calendar.events"]
SCOPES_EMAIL = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
]


# State
class State(TypedDict):
    input: str
    decision: str
    output: str


def authenticate(SCOPES):

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def email_json():
    json_schema = {
        "title": "EmailDraft",
        "description": "AI-generated email with structured fields.",
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "Recipient's email address.",
            },
            "subject": {
                "type": "string",
                "description": "The subject line of the email.",
            },
            "body": {
                "type": "string",
                "description": "The main content of the email.",
            },
        },
        "required": ["to", "subject", "body"],
    }
    return json_schema


def calendar_json():
    event_json_schema = {
        "title": "CalendarEvent",
        "description": "Extract structured calendar event details from text.",
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Title of the event.",
            },
            "location": {
                "type": "string",
                "description": "Location where the event will take place.",
            },
            "description": {
                "type": "string",
                "description": "Short description of the event.",
            },
            "start": {
                "type": "string",
                "description": "Start date and time in ISO format (YYYY-MM-DDTHH:MM:SS-07:00).",
            },
            "end": {
                "type": "string",
                "description": "End date and time in ISO format (YYYY-MM-DDTHH:MM:SS-07:00).",
            },
            "attendees": {
                "type": "array",
                "items": {
                    "type": "email",
                    "description": "Email addresses of attendees.",
                },
            },
            "timeZone": {
                "type": "string",
                "description": "Time zone of the event (e.g., 'America/Los_Angeles').",
            },
        },
        "required": ["summary", "start", "end"],
    }
    return event_json_schema


def calendar_manager(state: State):
    creds = authenticate(SCOPES_CALENDAR)
    service = build("calendar", "v3", credentials=creds)
    service = build("calendar", "v3", credentials=creds)
    event_json_schema = calendar_json()
    structured_llm = llm.with_structured_output(event_json_schema)

    event_details = structured_llm.invoke(state["input"])
    event = {
        "summary": event_details[0]["args"].get("summary", "Untitled Event"),
        "location": event_details[0]["args"].get("location", "No location provided"),
        "description": event_details[0]["args"].get("description", ""),
        "start": {
            "dateTime": event_details[0]["args"]["start"],
            "timeZone": event_details[0]["args"].get("timeZone", "America/Los_Angeles"),
        },
        "end": {
            "dateTime": event_details[0]["args"]["end"],
            "timeZone": event_details[0]["args"].get("timeZone", "America/Los_Angeles"),
        },
        "attendees": [
            {"email": email} for email in event_details[0]["args"].get("attendees", [])
        ],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},
                {"method": "popup", "minutes": 10},
            ],
        },
    }

    event = service.events().insert(calendarId="primary", body=event).execute()
    print("Event created: %s" % (event.get("htmlLink")))
    return {"output": event.get("htmlLink")}


def email_manager(state: State):
    """AI-Powered Email Drafter with Structured Output"""

    creds = authenticate(SCOPES_EMAIL)
    service = build("gmail", "v1", credentials=creds)
    json_schema = email_json()
    structured_llm = llm.with_structured_output(json_schema)

    email_details = structured_llm.invoke(state["input"])

    to_email = email_details[0]["args"].get("to", "default@example.com")  # Fallback
    subject = email_details[0]["args"].get("subject", "No Subject")
    message_body = email_details[0]["args"].get("body", "No Content")

    message = EmailMessage()
    message.set_content(message_body)
    message["To"] = to_email
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"message": {"raw": encoded_message}}
    try:
        draft = (
            service.users().drafts().create(userId="me", body=create_message).execute()
        )
        print(f"✅ Draft created successfully! ID: {draft['id']}")

        return {
            "output": {
                "draft_id": draft["id"],
                "status": "success",
                "email_data": email_details,
            }
        }
    except HttpError as error:
        print(f"❌ An error occurred: {error}")
        return {"status": "error", "message": str(error)}


def health_coach(state: State):
    """Health Coach - Provides fitness and wellness advice"""
    system_prompt = """
    You are a knowledgeable and supportive Health Coach.
    Your goal is to help users improve their physical health, 
    diet, exercise, and overall wellness.
        
    Based on the user's question, provide expert advice on fitness routines, 
    nutrition, wellness habits, and lifestyle changes.
        
    Answer the following question with clear, actionable, and motivational advice:
    Question:
    """

    result = llm.invoke(system_prompt + state["input"])
    return {"output": result.content}


def life_advisor(state: State):
    """Life Advisor - Provides personal development guidance"""

    system_prompt = f"""
    You are a wise and motivational Life Advisor.
    Your job is to help users with self-improvement, 
    decision-making, goal setting, and personal growth.
    
    Respond with insightful and positive guidance that helps users 
    overcome challenges and stay motivated.
    
    Answer the following question in a practical and inspiring way:
    
    Question:
    """

    result = llm.invoke(system_prompt + state["input"])
    return {"output": result.content}


def llm_call_router(state: State):
    """Route the input to the appropriate node"""
    print("Members", members)
    # Run the augmented LLM with structured output to serve as routing logic
    decision = router.invoke(
        [
            SystemMessage(
                content="""
                You are a smart AI router. Your task is to determine the most suitable member from a given list to handle the user's input.
"""
            ),
            HumanMessage(content=members),
            HumanMessage(content="User Input :" + state["input"]),
        ]
    )
    return {"decision": decision.step}


def route_decision(state: State):
    if state["decision"] == "life_advisor":
        return "life_advisor"
    elif state["decision"] == "health_coach":
        return "health_coach"
    elif state["decision"] == "email_manager":
        return "email_manager"
    elif state["decision"] == "calendar_manager":
        return "calendar_manager"


router_builder = StateGraph(State)

router_builder.add_node("health_coach", health_coach)
router_builder.add_node("life_advisor", life_advisor)
router_builder.add_node("email_manager", email_manager)
router_builder.add_node("calendar_manager", calendar_manager)
router_builder.add_node("llm_call_router", llm_call_router)

router_builder.add_edge(START, "llm_call_router")

router_builder.add_conditional_edges(
    "llm_call_router",
    route_decision,
    {
        "health_coach": "health_coach",
        "life_advisor": "life_advisor",
        "email_manager": "email_manager",
        "calendar_manager": "calendar_manager",
    },
)
router_builder.add_edge("health_coach", END)
router_builder.add_edge("life_advisor", END)
router_builder.add_edge("email_manager", END)
router_builder.add_edge("calendar_manager", END)

# Compile workflow
router_workflow = router_builder.compile()
