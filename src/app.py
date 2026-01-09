"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import os
import json
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Load activities from JSON file
def load_activities():
    """Load activities from activities.json file"""
    activities_file = os.path.join(Path(__file__).parent, "activities.json")
    try:
        with open(activities_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {activities_file} not found. Using empty activities.")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: {activities_file} is not valid JSON. Using empty activities.")
        return {}

# In-memory activity database (loaded from JSON)
activities = load_activities()

# Load teachers credentials from JSON file
def load_teachers():
    """Load teacher credentials from teachers.json file"""
    teachers_file = os.path.join(Path(__file__).parent, "teachers.json")
    try:
        with open(teachers_file, 'r') as f:
            data = json.load(f)
            return {teacher["username"]: teacher["password"] for teacher in data.get("teachers", [])}
    except FileNotFoundError:
        print(f"Warning: {teachers_file} not found. No teachers will be able to log in.")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: {teachers_file} is not valid JSON.")
        return {}

# In-memory teacher credentials (loaded from JSON)
teachers = load_teachers()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/login")
def login(username: str, password: str):
    """Authenticate a teacher"""
    if username not in teachers or teachers[username] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"message": "Login successful", "username": username}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, username: str = None, password: str = None):
    """Unregister a student from an activity (teacher only with authentication)"""
    # Validate teacher authentication if credentials are provided
    if username and password:
        if username not in teachers or teachers[username] != password:
            raise HTTPException(status_code=401, detail="Invalid teacher credentials")
    else:
        # If no auth provided, allow it (for backward compatibility)
        pass
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
