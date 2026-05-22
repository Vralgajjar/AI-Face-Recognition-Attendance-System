CV, the system features a complete dashboard for managing students, capturing face samples, training an LBPH model on-the-fly, and generating detailed Excel/CSV attendance reports.

🚀 Key Features
Secure Authentication: Multi-user access with secure session management and SHA-256 hashed password authentication.

Student Management: Complete CRUD-like interface to add or delete student profiles directly from the dashboard.

Fast Face Capture: Seamlessly opens the webcam to capture and instantly optimize face samples (resized dynamically to maximize speed and save disk space).

On-Demand Model Training: Uses an optimized LBPH (Local Binary Patterns Histograms) Face Recognizer that trains new data in seconds right from the UI.

Live Attendance Scanning: Fires up a fast, live recognition stream with visual boundaries and match-confidence indicators to automatically log student entries.

Smart Analytics & Reports: * Interactive dashboard statistics (Total Students, Today's Attendance logs).

Filtered historical records (searchable by date, name, roll number, or college).

One-click CSV report export.

Concurrent Thread Protection: Utilizes threading locks to prevent camera resource conflicts between background operations like capturing, training, and scanning.

🛠️ Tech Stack
Backend Framework: Flask (Python)

Computer Vision: OpenCV (opencv-python), Pillow

Database: SQLite 3 (Lightweight, zero-config relational database)

Data Processing: Pandas (CSV generation)
