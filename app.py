from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import uuid
import joblib

from werkzeug.utils import secure_filename

from train_model import extract_features
from severity import estimate_severity

from temporal_analysis import (
    create_database,
    save_severity,
    analyze_trend,
    get_all_history,
    get_dashboard_stats
)


# --------------------------------
# FLASK APPLICATION
# --------------------------------

app = Flask(__name__)

app.secret_key = "cropcare_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

MODEL_PATH = os.path.join(
    BASE_DIR,
    "model",
    "crop_disease_model.pkl"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --------------------------------
# DATABASE INITIALIZATION
# --------------------------------

create_database()


# --------------------------------
# LOAD TRAINED MODEL
# --------------------------------

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        "Trained model not found. Please run train_model.py first."
    )

model = joblib.load(MODEL_PATH)


# --------------------------------
# ALLOWED IMAGE FORMATS
# --------------------------------

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# --------------------------------
# HOME / DASHBOARD PAGE
# --------------------------------

@app.route("/")
def home():

    dashboard = get_dashboard_stats()

    return render_template(
        "index.html",
        dashboard=dashboard
    )


# --------------------------------
# UPLOAD PAGE
# --------------------------------

@app.route("/upload")
def upload():

    return render_template("upload.html")


# --------------------------------
# DISEASE PREDICTION
# --------------------------------

@app.route("/predict", methods=["POST"])
def predict():

    if "crop_image" not in request.files:

        flash("Please select a crop image.")
        return redirect(url_for("upload"))

    file = request.files["crop_image"]

    if file.filename == "":

        flash("No image selected.")
        return redirect(url_for("upload"))

    if not allowed_file(file.filename):

        flash("Only JPG, JPEG and PNG images are allowed.")
        return redirect(url_for("upload"))

    try:

        # Save uploaded image

        original_filename = secure_filename(file.filename)

        unique_filename = (
            str(uuid.uuid4())[:8]
            + "_"
            + original_filename
        )

        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            unique_filename
        )

        file.save(image_path)


        # Extract image features

        features = extract_features(image_path)

        if features is None:

            raise ValueError(
                "Unable to process the uploaded image."
            )

        features = features.reshape(1, -1)


        # Random Forest Prediction

        prediction = model.predict(features)[0]


        # Prediction Confidence

        probabilities = model.predict_proba(features)[0]

        confidence = round(
            max(probabilities) * 100,
            2
        )


        # Severity Estimation

        severity_result = estimate_severity(image_path)

        severity_percentage = severity_result[
            "severity_percentage"
        ]

        severity_level = severity_result[
            "severity_level"
        ]


        # Plant ID

        plant_id = request.form.get(
            "plant_id",
            "default-plant"
        ).strip()

        if not plant_id:
            plant_id = "default-plant"


        # Save prediction and severity

        save_severity(
            plant_id,
            unique_filename,
            severity_percentage,
            severity_level,
            str(prediction)
        )


        # Temporal Analysis

        trend = analyze_trend(plant_id)


        # Display Result

        return render_template(
            "result.html",

            prediction=prediction,

            confidence=confidence,

            severity_percentage=severity_percentage,

            severity_level=severity_level,

            trend=trend,

            image_filename=unique_filename
        )


    except Exception as error:

        print("Prediction Error:", error)

        flash(
            "Something went wrong while analyzing the image. "
            "Please try again."
        )

        return redirect(url_for("upload"))


# --------------------------------
# DISPLAY UPLOADED IMAGE
# --------------------------------

@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# --------------------------------
# HISTORY PAGE
# --------------------------------

@app.route("/history")
def history():

    history_records = get_all_history()

    return render_template(
        "history.html",
        history=history_records
    )


# --------------------------------
# RUN APPLICATION
# --------------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )