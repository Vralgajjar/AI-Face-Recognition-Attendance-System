import os
import io
import pandas as pd
from datetime import datetime


def get_current_datetime():
    now = datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")


def ensure_dirs():
    os.makedirs("dataset", exist_ok=True)
    os.makedirs("trainer", exist_ok=True)


def export_attendance_csv(records):
    data = []
    for r in records:
        data.append({
            "Name": r["name"],
            "Roll Number": r["roll_number"],
            "College": r["college"],
            "Date": r["date"],
            "Time": r["time"]
        })
    df = pd.DataFrame(data)
    output = io.StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()


def get_student_image_path(face_id, img_num):
    return os.path.join("dataset", f"User.{face_id}.{img_num}.jpg")


def count_dataset_images(face_id):
    count = 0
    for f in os.listdir("dataset"):
        if f.startswith(f"User.{face_id}."):
            count += 1
    return count
