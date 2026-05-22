from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, Response
)
from functools import wraps
import threading
import os

from database import (
    init_db, get_all_students, add_student, delete_student,
    get_all_attendance, get_dashboard_stats, get_next_face_id
)
from auth import register_user, login_user
from utils import export_attendance_csv, ensure_dirs

app = Flask(__name__)
app.secret_key = "attendance_secret_key_2024"

# Thread lock to prevent concurrent camera use
camera_lock = threading.Lock()
training_status = {"running": False, "message": "", "done": False, "success": False}


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ─── AUTH ROUTES ─────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        ok, result = login_user(username, password)
        if ok:
            session["user_id"] = result["id"]
            session["username"] = result["username"]
            flash(f"Welcome back, {result['username']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(result, "error")
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        ok, message = register_user(username, password)
        if ok:
            flash(message + " Please login.", "success")
            return redirect(url_for("login"))
        else:
            flash(message, "error")
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


# ─── DASHBOARD ───────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    stats = get_dashboard_stats()
    students = get_all_students()
    return render_template("dashboard.html",
                           stats=stats,
                           students=students,
                           username=session.get("username"))


# ─── STUDENT MANAGEMENT ──────────────────────────────────────

@app.route("/students/add", methods=["POST"])
@login_required
def add_student_route():
    name = request.form.get("name", "").strip()
    roll = request.form.get("roll_number", "").strip()
    college = request.form.get("college", "").strip()

    if not all([name, roll, college]):
        flash("All fields are required.", "error")
        return redirect(url_for("dashboard"))

    face_id = get_next_face_id()
    ok, message = add_student(name, roll, college, face_id)

    if ok:
        flash(f"Student '{name}' added with Face ID {face_id}. Now capture their face.", "success")
    else:
        flash(message, "error")

    return redirect(url_for("dashboard"))


@app.route("/students/delete/<int:student_id>", methods=["POST"])
@login_required
def delete_student_route(student_id):
    delete_student(student_id)
    flash("Student deleted.", "success")
    return redirect(url_for("dashboard"))


# ─── FACE CAPTURE & TRAINING ─────────────────────────────────

@app.route("/capture/<int:face_id>", methods=["POST"])
@login_required
def capture_face(face_id):
    """Launch face capture in background thread"""
    global training_status

    if camera_lock.locked():
        return jsonify({"success": False, "message": "Camera is already in use."})

    def do_capture():
        from train_model import capture_faces
        with camera_lock:
            training_status.update({"running": True, "message": "Capturing faces...", "done": False})
            ok, msg, count = capture_faces(face_id, num_samples=50)
            training_status.update({"running": False, "message": msg, "done": True, "success": ok})

    t = threading.Thread(target=do_capture)
    t.daemon = True
    t.start()

    return jsonify({"success": True, "message": "Face capture started. A webcam window will open."})


@app.route("/train", methods=["POST"])
@login_required
def train_model_route():
    """Train the LBPH model"""
    global training_status

    if camera_lock.locked():
        return jsonify({"success": False, "message": "Camera is in use."})

    def do_train():
        from train_model import train_model
        training_status.update({"running": True, "message": "Training model...", "done": False})
        ok, msg = train_model()
        training_status.update({"running": False, "message": msg, "done": True, "success": ok})

    t = threading.Thread(target=do_train)
    t.daemon = True
    t.start()

    return jsonify({"success": True, "message": "Training started..."})


@app.route("/training-status")
@login_required
def training_status_route():
    return jsonify(training_status)


# ─── ATTENDANCE ───────────────────────────────────────────────

@app.route("/attendance")
@login_required
def attendance_page():
    return render_template("attendance.html", username=session.get("username"))


@app.route("/attendance/start", methods=["POST"])
@login_required
def start_attendance():
    if camera_lock.locked():
        return jsonify({"success": False, "message": "Camera is already in use."})

    result = {"success": False, "message": "", "marked": []}

    def do_attendance():
        from attendance import run_attendance
        with camera_lock:
            ok, msg, marked = run_attendance()
            result["success"] = ok
            result["message"] = msg
            result["marked"] = marked

    t = threading.Thread(target=do_attendance)
    t.daemon = True
    t.start()
    t.join(timeout=60)  # Max 60s

    return jsonify(result)


# ─── REPORTS ─────────────────────────────────────────────────

@app.route("/report")
@login_required
def report():
    date_filter = request.args.get("date", "")
    search = request.args.get("search", "")
    records = get_all_attendance(date_filter or None, search or None)
    return render_template("report.html",
                           records=records,
                           date_filter=date_filter,
                           search=search,
                           username=session.get("username"))


@app.route("/report/export")
@login_required
def export_report():
    date_filter = request.args.get("date", "")
    search = request.args.get("search", "")
    records = get_all_attendance(date_filter or None, search or None)
    csv_data = export_attendance_csv(records)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_report.csv"}
    )


# ─── API ──────────────────────────────────────────────────────

@app.route("/api/stats")
@login_required
def api_stats():
    return jsonify(get_dashboard_stats())


if __name__ == "__main__":
    init_db()
    ensure_dirs()
    print("\n" + "="*50)
    print("  AI Attendance System Running")
    print("  Open: http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True, threaded=True)
