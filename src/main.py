from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.models.chakra_schema import UserChakraInput
from src.database import save_user_snapshot
from src.agents.chakra_agent import chakra_agent
from src.utils.calendar_gen import create_ics_file
from src.utils.email_service import send_reminder_email
from src.utils.visualizer import generate_identity_card

import os
import traceback
import asyncio
import concurrent.futures
import nest_asyncio

# Rate Limiting Imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

nest_asyncio.apply()


# 1. CUSTOM KEY FUNCTION FOR RAILWAY
# This extracts the real user's IP from the proxy headers provided by Railway.
def get_railway_user_ip(request: Request):
    # Railway passes the real IP in 'X-Forwarded-For'
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Get the first IP in the list (the original client)
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


# 2. INITIALIZE LIMITER
limiter = Limiter(key_func=get_railway_user_ip)
app = FastAPI(title="Sath-Chakra AI Backend")
app.state.limiter = limiter


# 3. CUSTOM RATE LIMIT EXCEEDED HANDLER
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": "Protocol 2026 security: You have reached the hourly limit. Please try again later.",
            "message_si": "ඔබ පැයකට ලබා ගත හැකි උපරිම සීමාව පසු කර ඇත. කරුණාකර පසුව නැවත උත්සාහ කරන්න."
        }
    )


# CORS CONFIGURATION
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sath-chakra-ai.vercel.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Folder Setup
for folder in ["data/shares", "data/calendars"]:
    os.makedirs(folder, exist_ok=True)

app.mount("/data", StaticFiles(directory="data"), name="data")


# 4. APPLY RATE LIMIT TO ROUTE
@app.post("/analyze-chakra")
@limiter.limit("5/hour")  # Limit: 5 requests per hour per unique user
async def analyze_chakra(request: Request, user_input: UserChakraInput, background_tasks: BackgroundTasks):
    try:
        data_to_save = user_input.model_dump()
        save_user_snapshot(data_to_save)

        initial_state = {
            "user_data": data_to_save,
            "language": user_input.language,
            "analysis_report": "",
            "action_plan": "",
            "social_copy": ""
        }

        final_state = chakra_agent.invoke(initial_state)
        full_text = final_state.get("action_plan", "")

        # Calendar logic
        event_lines = [line for line in full_text.split('\n') if "DATE:" in line]
        calendar_path = create_ics_file(event_lines, user_input.user_id)

        # Card generation
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            share_card_path = await loop.run_in_executor(
                pool,
                lambda: generate_identity_card(
                    user_id=user_input.user_id,
                    data=data_to_save,
                    social_json=final_state.get("social_copy", "{}")
                )
            )

        # Background Email task
        email_body = f"ඔබේ 2026 උපායමාර්ගික සැලැස්ම සූදානම්.\n\n{final_state.get('analysis_report', '')}"
        background_tasks.add_task(
            send_reminder_email,
            user_input.email,
            "Sath-Chakra: Your 2026 Roadmap",
            email_body
        )

        return {
            "status": "success",
            "ai_analysis": final_state.get("analysis_report"),
            "action_plan_2026": final_state.get("action_plan"),
            "shareable_card_url": f"/data/shares/share_{user_input.user_id}.png",
            "calendar_url": f"/data/calendars/roadmap_{user_input.user_id}.ics",
            "message": "Protocol 2026 Initialized. Identity Artifact Ready."
        }
    except Exception as e:
        print(f"CRITICAL INTEGRATION ERROR: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")