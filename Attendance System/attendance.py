from train_model import recognize_faces_live
from database import get_student_by_face_id, mark_attendance
from utils import get_current_datetime


def run_attendance():
    """
    Full attendance flow: recognize faces → mark attendance.
    Returns (success, message, list_of_marked)
    """
    success, msg, results = recognize_faces_live()

    if not success:
        return False, msg, []

    if not results:
        return False, "No faces recognized. Try better lighting or retrain the model.", []

    marked = []
    errors = []

    for face_id, confidence in results:
        student = get_student_by_face_id(face_id)
        if not student:
            continue

        date, time = get_current_datetime()
        ok, message = mark_attendance(
            student["id"],
            student["name"],
            student["roll_number"],
            student["college"],
            date,
            time
        )

        if ok:
            marked.append({
                "name": student["name"],
                "roll_number": student["roll_number"],
                "college": student["college"],
                "date": date,
                "time": time
            })
        else:
            errors.append(f"{student['name']}: {message}")

    if marked:
        msg = f"Attendance marked for {len(marked)} student(s)."
        if errors:
            msg += f" ({len(errors)} skipped: already marked)"
        return True, msg, marked
    elif errors:
        return False, "; ".join(errors), []
    else:
        return False, "No matching students found in database.", []
