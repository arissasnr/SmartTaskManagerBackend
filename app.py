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

def extract_task_name(text):

    patterns = [

        r"Task:\s*(.*)",

        r"Task Title:\s*(.*)"

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return match.group(1).strip()

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

    print("TASK DETECTED:")
    print(repr(task_name))

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

    print("TASK DETECTED:")
    print(repr(task_name))

    print("TASK DETECTED:")
    print(repr(task_name))

    print("ROWS FOUND:")
    print(len(task_info))

    print("MATCHES FOUND:")
    print(len(task_info))

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
        "checklist": checklist_items
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

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )