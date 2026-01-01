from fastapi import FastAPI, HTTPException, BackgroundTasks
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

nest_asyncio.apply()

app = FastAPI(title="Sath-Chakra AI Backend")

# Change this block in your main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For deployment, "*" is the safest way to clear the sync error
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for folder in ["data/shares", "data/calendars"]:
    os.makedirs(folder, exist_ok=True)

app.mount("/data", StaticFiles(directory="data"), name="data")

@app.post("/analyze-chakra")
async def analyze_chakra(user_input: UserChakraInput, background_tasks: BackgroundTasks):
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
        event_lines = [line for line in full_text.split('\n') if "DATE:" in line]
        clean_event_lines = []
        for line in event_lines:
            idx = line.find("DATE:")
            if idx != -1:
                clean_event_lines.append(line[idx:])
        calendar_path = create_ics_file(clean_event_lines, user_input.user_id)
        # Run card gen in thread to avoid loop issues
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            share_card_path = await loop.run_in_executor(
                pool,
                lambda: generate_identity_card(user_id=user_input.user_id, data=data_to_save, social_json=final_state.get("social_copy", "{}"))
            )
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