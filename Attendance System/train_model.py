import cv2
import numpy as np
import os

# --- Constants ---
DATASET_DIR = "dataset"
TRAINER_PATH = os.path.join("trainer", "trainer.yml")
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
# Smaller image size = Significantly faster training
IMG_SIZE = (100, 100) 

def capture_faces(face_id, num_samples=25): # Reduced to 25 for speed
    os.makedirs(DATASET_DIR, exist_ok=True)
    os.makedirs("trainer", exist_ok=True)

    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    cam = cv2.VideoCapture(0)
    
    count = 0
    while count < num_samples:
        ret, frame = cam.read()
        if not ret: break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Faster detection parameters
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            count += 1
            # Resize immediately for disk space and training speed
            face_crop = cv2.resize(gray[y:y+h, x:x+w], IMG_SIZE)
            cv2.imwrite(f"{DATASET_DIR}/User.{face_id}.{count}.jpg", face_crop)

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"Capturing: {count}/{num_samples}", (10, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Fast Capture - Stay Still", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cam.release()
    cv2.destroyAllWindows()
    return True, "Capture complete", count

def train_model():
    """Optimized LBPH training from disk."""
    # LBPH: radius=1, neighbors=8, grid_x=8, grid_y=8 (standard speed/accuracy balance)
    recognizer = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
    
    faces = []
    ids = []
    
    if not os.path.exists(DATASET_DIR) or len(os.listdir(DATASET_DIR)) == 0:
        return False, "Dataset is empty. Capture faces first."

    # High-speed list comprehension for loading
    image_paths = [os.path.join(DATASET_DIR, f) for f in os.listdir(DATASET_DIR) if f.endswith(".jpg")]
    
    for path in image_paths:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        # No need to resize here, they were resized during capture!
        fid = int(os.path.split(path)[-1].split(".")[1])
        faces.append(img)
        ids.append(fid)

    if len(faces) == 0:
        return False, "No valid face data found."

    recognizer.train(faces, np.array(ids))
    recognizer.write(TRAINER_PATH)
    return True, f"Model trained on {len(faces)} images in seconds!"

def recognize_faces_live():
    """Recognizes faces and returns IDs found."""
    if not os.path.exists(TRAINER_PATH):
        return False, "Trainer file missing. Please train the model.", []

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(TRAINER_PATH)
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    
    cam = cv2.VideoCapture(0)
    found_ids = set() # Use set to avoid duplicates during a single session

    # Run for 5 seconds or until 'q'
    import time
    start_time = time.time()
    
    while (time.time() - start_time) < 7:
        ret, frame = cam.read()
        if not ret: break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:
            roi_gray = cv2.resize(gray[y:y+h, x:x+w], IMG_SIZE)
            face_id, confidence = recognizer.predict(roi_gray)
            
            # Confidence < 50-60 is usually a good match for LBPH
            if confidence < 50:
                found_ids.add((face_id, confidence))
                label = f"ID: {face_id} ({round(confidence)}%)"
                color = (0, 255, 0)
            else:
                label = "Unknown"
                color = (0, 0, 255)

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("Attendance - Press 'q' to Finish", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cam.release()
    cv2.destroyAllWindows()
    return True, "Scanning complete", list(found_ids)