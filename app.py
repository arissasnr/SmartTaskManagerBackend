from flask import Flask, request
import cv2
import pytesseract
import os

if os.name == "nt":

    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )
import pandas as pd
import re

app = Flask(__name__)

tasks_df = pd.read_csv("tasks.csv")

checklist_df = pd.read_csv("checklist.csv")

schedule_df = pd.read_excel(
    "technician_schedule.xlsx"
)

users_df = pd.read_csv(
    "users.csv"
)

print(users_df)

print(schedule_df)

print(schedule_df.columns)

print(tasks_df.head())

print(checklist_df.head())

print(schedule_df.head())

def extract_text_from_image(image_path):

    print("READING IMAGE:")
    print(image_path)

    image = cv2.imread(image_path)

    print("IMAGE LOADED:")
    print(image is not None)

    text = pytesseract.image_to_string(image)

    print("OCR TEXT LENGTH:")
    print(len(text))

    return text

def find_available_slots(
    technician_name,
    schedule_df,
):
    tech_tasks = schedule_df[
    schedule_df["Name"]
        .str.strip()
    ==
    technician_name.strip()
].sort_values("Start")

    print("TECH TASKS")
    print(tech_tasks)

    free_slots = []
    current_time = 8

    for _, row in tech_tasks.iterrows():
        if row["Start"] > current_time:
            free_slots.append((current_time, row["Start"]))
        current_time = row["End"]

    if current_time < 17:
        free_slots.append((current_time, 17))

    return free_slots

def get_matching_technicians(
    required_skill,
    schedule_df
):

    technicians = schedule_df[
        schedule_df["Skill"]
            .str.strip()
        ==
        required_skill.strip()
    ]["Name"] \
        .str.strip() \
        .unique()

    return list(technicians)

print(

    get_matching_technicians(
        "B2 Technician",
        schedule_df
    )

)

def recommend_technicians(
    required_skill,
    required_manpower,
    schedule_df
):

    matching_techs = get_matching_technicians(
        required_skill,
        schedule_df
    )

    return matching_techs[
        :required_manpower
    ]

def build_schedule_recommendation(
    required_skill,
    required_manpower,
    schedule_df
):

    technicians = recommend_technicians(
        required_skill,
        required_manpower,
        schedule_df
    )

    availability = find_common_slot(
        technicians,
        schedule_df
    )

    overlap = get_overlap_slot(
        technicians,
        schedule_df
    )

    if overlap:

        return {

            "recommended_technicians":
                technicians,

            "availability":
                availability,

            "schedule_status":
                "Available",

            "suggested_slot":
                f"{overlap[0]:02d}:00 - {overlap[1]:02d}:00",

            "scheduling_recommendation":
                "Task can be inserted into current maintenance schedule."

        }

    return {

        "recommended_technicians":
            technicians,

        "availability":
            availability,

        "schedule_status":
            "Conflict Detected",

        "suggested_slot":
            "None",

        "scheduling_recommendation":
            "Supervisor review required before task insertion."

    }

def get_overlap_slot(
    technicians,
    schedule_df
):

    technician_slots = []

    for tech in technicians:

        slots = find_available_slots(
            tech,
            schedule_df
        )

        if len(slots) > 0:

            technician_slots.append(
                slots[0]
            )

    if len(technician_slots) < 2:

        return None

    overlap_start = max(
        slot[0]
        for slot in technician_slots
    )

    overlap_end = min(
        slot[1]
        for slot in technician_slots
    )

    if overlap_start < overlap_end:

        return (
            overlap_start,
            overlap_end
        )

    return None

def find_common_slot(
    technicians,
    schedule_df
):

    technician_slots = {}

    for tech in technicians:

        technician_slots[tech] = (
            find_available_slots(
                tech,
                schedule_df
            )
        )

    return technician_slots

def get_recommended_slot(
    technicians,
    schedule_df
):

    latest_start = 8
    earliest_end = 17

    for tech in technicians:

        slots = find_available_slots(
            tech,
            schedule_df
        )

        first_slot = slots[0]

        latest_start = max(
            latest_start,
            first_slot[0]
        )

        earliest_end = min(
            earliest_end,
            first_slot[1]
        )

    return (
        latest_start,
        earliest_end
    )


def extract_task_name(text):
    patterns = [
        r"Task:\s*(.*)",
        r"Task Title:\s*(.*)"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            return match.group(1).strip()

    text = text.lower()

    if "fuel boost pump" in text:
        return "Replace Fuel Boost Pump"

    elif "main landing gear" in text:
        return "Replace Main Landing Gear"

    elif "storage battery" in text:
        return "Replace Nickel-Cadmium Storage Battery"

    return None

@app.route("/")
def home():

    return "Smart Task Manager API Running"


import os

@app.route("/analyze")
def analyze():

    print("USING IMAGE:")
    print("uploads/upload.png")
    print("CURRENT FOLDER:")
    print(os.getcwd())
    print("IMAGE FILE EXISTS:")
    print(os.path.exists("taskcard_fuel_pump.png"))

    print("CURRENT FOLDER:")
    print(os.getcwd())
    print("IMAGE FILE EXISTS:")
    print(os.path.exists("uploads/upload.png"))

    ocr_text = extract_text_from_image(
    "uploads/upload.png"
)

    print("OCR RESULT")
    print(ocr_text)

    task_name = extract_task_name(
        ocr_text
    )

    print("TASK DETECTED:")
    print(repr(task_name))

    if task_name is None:
        return {
            "error": "Task not found"
        }

    task_info = tasks_df[
    tasks_df["task_name"]
        .str.lower()
    ==
    task_name.lower()
]

    if task_info.empty:
        return {
            "error": f"Task not found: {task_name}"
        }

    task_id = task_info.iloc[0]["task_id"]

    required_skill = task_info.iloc[0]["skill_required"]

    required_manpower = task_info.iloc[0]["manpower_required"]

    available_techs = schedule_df[
    schedule_df["Skill"].str.lower() == required_skill.lower()
]

    selected_tech = available_techs.iloc[0]

    duration_hours = (
    selected_tech["End"]
    - selected_tech["Start"]
)

    task_checklist = checklist_df[
        checklist_df["task_id"] == task_id
    ]

    checklist_items = []

    for item in task_checklist["checklist_item"]:

        checklist_items.append(item)

    schedule_recommendation = build_schedule_recommendation(
        required_skill,
        required_manpower,
        schedule_df,
    )

    print("SCHEDULE RECOMMENDATION:")
    print(schedule_recommendation)

    return {
        "task_id": str(task_info.iloc[0]["task_id"]),
        "task_name": task_name,
        "skill": required_skill,
        "ata": str(task_info.iloc[0]["ata_chapter"]),
        "amm": str(task_info.iloc[0]["AMM_reference"]),
        "technician": str(selected_tech["Name"]),
        "duration":
    f"{duration_hours} Hours",
        "manpower":
    str(required_manpower),
        "start_time":
    f"{int(selected_tech['Start']):02d}:00",
"end_time":
    f"{int(selected_tech['End']):02d}:00",
        "checklist": checklist_items,
        "recommended_technicians":
    schedule_recommendation[
        "recommended_technicians"
    ],

"availability":
    schedule_recommendation[
        "availability"
    ],

"schedule_status":
    schedule_recommendation[
        "schedule_status"
    ],

"suggested_slot":
    schedule_recommendation[
        "suggested_slot"
    ],

"scheduling_recommendation":
    schedule_recommendation[
        "scheduling_recommendation"
    ],
    }

@app.route("/test_upload", methods=["POST"])
def test_upload():

    file = request.files["image"]

    print("FILE RECEIVED:")
    print(file.filename)

    data = file.read()

    print("SIZE:")
    print(len(data))

    file.seek(0)

    file.save(
        "uploads/upload.png"
    )

    print("NEW IMAGE SAVED")

    return {
        "message": "Image uploaded",
        "file": file.filename
    }

@app.route("/login")
def login():

    users_df = pd.read_csv(
        "users.csv"
    )

    email = request.args.get(
        "email"
    )

    password = request.args.get(
        "password"
    )

    user = users_df[

        (users_df["email"] == email)

        &

        (users_df["password"] == password)

    ]

    if user.empty:

        return {
            "status": "failed",
            "message": "Invalid credentials"
        }

    row = user.iloc[0]

    if row["status"] != "approved":

        return {
            "status": "pending",
            "message":
                "Awaiting admin approval"
        }

    return {

        "status": "success",

        "name":
            row["name"],

        "role":
            row["role"]

    }

@app.route("/signup")
def signup():

    users_df = pd.read_csv(
    "users.csv"
)

    name = request.args.get("name")

    email = request.args.get("email")

    password = request.args.get("password")

    print("SIGNUP REQUEST RECEIVED")
    print(name)
    print(email)
    print(password)

    existing_user = users_df[
        users_df["email"] == email
    ]

    if not existing_user.empty:

        return {
            "status": "failed",
            "message": "Email already exists"
        }

    new_id = len(users_df) + 1

    users_df.loc[
        len(users_df)
    ] = [

        new_id,
        name,
        email,
        password,
        "technician",
        "pending"

    ]

    print("ABOUT TO SAVE CSV")

    users_df.to_csv(
        "users.csv",
        index=False
    )

    print("CSV SAVED SUCCESSFULLY")

    return {

        "status": "success",

        "message":
            "Account created. Awaiting admin approval."

    }

@app.route("/pending_users")
def pending_users():

    users_df = pd.read_csv(
        "users.csv"
    )

    pending = users_df[
        users_df["status"] == "pending"
    ]

    result = []

    for _, row in pending.iterrows():

        result.append({

            "user_id":
                int(row["user_id"]),

            "name":
                row["name"],

            "email":
                row["email"]

        })

    return {
        "users":
            result
    }

@app.route("/approve_user")
def approve_user():

    user_id = request.args.get(
        "user_id"
    )

    users_df = pd.read_csv(
        "users.csv"
    )

    users_df.loc[

        users_df["user_id"]
        ==
        int(user_id),

        "status"

    ] = "approved"

    users_df.to_csv(
        "users.csv",
        index=False
    )

    return {

        "status":
            "success",

        "message":
            "User approved"

    }

@app.route("/reject_user")
def reject_user():

    user_id = request.args.get(
        "user_id"
    )

    users_df = pd.read_csv(
        "users.csv"
    )

    users_df = users_df[

        users_df["user_id"]
        !=
        int(user_id)

    ]

    users_df.to_csv(
        "users.csv",
        index=False
    )

    return {

        "status":"success",

        "message":
            "User rejected"

    }

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )