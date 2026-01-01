import json
import os
from datetime import datetime

# Define the path using the directory structure we agreed upon
DB_PATH = "data/user_history.json"


def save_user_snapshot(user_data: dict):
    """
    Saves a user's Wheel of Life snapshot with a timestamp.
    Ensures data integrity by checking if the file exists.
    """
    # Create data directory if it doesn't exist (DevOps/File Management)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Add a timestamp for tracking (Behavioral Science: needed for 3-month re-check)
    user_data["timestamp"] = datetime.now().isoformat()

    history = []
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    history.append(user_data)

    with open(DB_PATH, "w") as f:
        json.dump(history, f, indent=4)

    return "Snapshot saved successfully."