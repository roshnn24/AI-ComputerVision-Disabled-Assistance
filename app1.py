import cv2
from flask import Flask, Response, render_template, request, redirect, url_for
from ultralytics import YOLO

app = Flask(__name__)

# Initialize YOLO models
model1 = YOLO(r'/Users/rosh/Downloads/fall.pt')
model3 = YOLO("yolov8x-worldv2.pt")

# Dummy data for users and caretakers (replace this with your actual authentication mechanism)
users = {'user1': 'password1', 'user2': 'password2'}
caretakers = {'caretaker1': 'password1', 'caretaker2': 'password2'}

# Function to verify user credentials
def verify_user(username, password):
    return users.get(username) == password

# Function to verify caretaker credentials
def verify_caretaker(username, password):
    return caretakers.get(username) == password

# Function to predict and detect objects using YOLO models
def predict(chosen_model, img, classes=[], conf=0.5):
    if classes:
        results = chosen_model.predict(img, classes=classes, conf=conf)
    else:
        results = chosen_model.predict(img, conf=conf)
    return results

# Function to draw bounding boxes and labels on detected objects
def predict_and_detect(chosen_model, img, classes=[], conf=0.5, rectangle_thickness=2, text_thickness=1, font_scale=1.5):
    results = predict(chosen_model, img, classes, conf=conf)
    for result in results:
        for box in result.boxes:
            # Draw bounding box
            cv2.rectangle(img, (int(box.xyxy[0][0]), int(box.xyxy[0][1])),
                          (int(box.xyxy[0][2]), int(box.xyxy[0][3])), (255, 0, 0), rectangle_thickness)
            # Display text on top of bounding box
            class_name = result.names[int(box.cls[0])]
            confidence = float(box.conf)
            text = f"{class_name}: {confidence:.2f}"
            cv2.putText(img, text,
                        (int(box.xyxy[0][0]), int(box.xyxy[0][1]) - 10),
                        cv2.FONT_HERSHEY_PLAIN, font_scale, (255, 0, 0), text_thickness)
    return img, results

# Function to generate video frames with object detection
def generate_frames():
    cap = cv2.VideoCapture("/Users/rosh/Downloads/fall_detection_1 (1).mp4")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        result_img1, _ = predict_and_detect(model1, frame, classes=[], conf=0.5)
        result_img3, results3 = predict_and_detect(model3, result_img1, classes=[], conf=0.5)

        collision_detected = False
        fall_detected = False

        for result in results3:
            for box in result.boxes:
                if result.names[int(box.cls[0])] == "person":
                    person_box = box
                    person_center = ((box.xyxy[0][0] + box.xyxy[0][2]) / 2, (box.xyxy[0][1] + box.xyxy[0][3]) / 2)
                elif result.names[int(box.cls[0])] == "fall":
                    fall_detected = True
                    break
                else:
                    object_box = box

                    # Calculate distances between person and nearby objects
                    object_center = ((object_box.xyxy[0][0] + object_box.xyxy[0][2]) / 2,
                                     (object_box.xyxy[0][1] + object_box.xyxy[0][3]) / 2)
                    distance = ((person_center[0] - object_center[0]) ** 2 + (
                                person_center[1] - object_center[1]) ** 2) ** 0.5

                    if distance < 100:  # Modify this threshold as needed
                        collision_detected = True
                        break

        if collision_detected or fall_detected:
            yield "data: Alert!! Collision or Fall detected!!!\n\n"

# Route for user login
@app.route('/login/user', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_user(username, password):
            # Redirect to user dashboard after successful login
            return redirect(url_for('user_dashboard'))
        else:
            return render_template('login.html', message='Invalid username or password')
    return render_template('login.html', message='')

# Route for caretaker login
@app.route('/login/caretaker', methods=['GET', 'POST'])
def caretaker_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_caretaker(username, password):
            # Redirect to caretaker dashboard after successful login
            return redirect(url_for('caretaker_dashboard'))
        else:
            return render_template('login.html', message='Invalid username or password')
    return render_template('login.html', message='')

# User dashboard route
@app.route('/dashboard/user')
def user_dashboard():
    return "User Dashboard"

# Caretaker dashboard route
@app.route('/dashboard/caretaker')
def caretaker_dashboard():
    return "Caretaker Dashboard"

# Route for index page
@app.route('/')
def index():
    return render_template('index.html')

# Route for streaming alerts
@app.route('/alert_feed')
def alert_feed():
    return Response(generate_frames(), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run(debug=True)
