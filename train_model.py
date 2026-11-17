import os
import cv2
import numpy as np
import joblib

from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


DATASET_PATH = "dataset"
MODEL_PATH = "model/crop_disease_model.pkl"

CLASSES = ["Healthy", "Early_Blight", "Late_Blight"]


def extract_features(image_path):

    image = cv2.imread(image_path)

    if image is None:
        return None

    image = cv2.resize(image, (128, 128))

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    hsv_mean = np.mean(hsv, axis=(0, 1))
    hsv_std = np.std(hsv, axis=(0, 1))

    gray_mean = np.mean(gray)
    gray_std = np.std(gray)

    edges = cv2.Canny(gray, 100, 200)
    edge_ratio = np.mean(edges > 0)

    features = np.concatenate([
        hsv_mean,
        hsv_std,
        [gray_mean, gray_std, edge_ratio]
    ])

    return features


def get_class_from_path(image_path):

    parts = os.path.normpath(image_path).split(os.sep)

    for folder in reversed(parts[:-1]):

        name = folder.lower().replace(" ", "_")

        if "early_blight" in name:
            return "Early_Blight"

        if "late_blight" in name:
            return "Late_Blight"

        if "healthy" in name:
            return "Healthy"

    return None


def load_dataset():

    features = []
    labels = []

    print("\nLoading crop disease dataset...\n")

    for root, dirs, files in os.walk(DATASET_PATH):

        for file in files:

            if file.lower().endswith((".jpg", ".jpeg", ".png")):

                image_path = os.path.join(root, file)

                label = get_class_from_path(image_path)

                if label not in CLASSES:
                    continue

                feature = extract_features(image_path)

                if feature is not None:

                    features.append(feature)
                    labels.append(label)

    print("Dataset Class Counts:")

    counts = Counter(labels)

    for class_name in CLASSES:
        print(f"{class_name}: {counts.get(class_name, 0)} images")

    if len(counts) != 3 or any(counts.get(c, 0) < 2 for c in CLASSES):
        raise ValueError(
            "\nAll three classes must contain at least 2 valid images. "
            "Please check the dataset folders."
        )

    return np.array(features), np.array(labels)


def train_model():

    X, y = load_dataset()

    print("\nTotal Images:", len(X))
    print("Total Features:", X.shape[1])

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print("\nTraining Random Forest Classifier...")

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    print("\nModel Training Completed!")
    print("Model Accuracy:", round(accuracy * 100, 2), "%")

    print("\nClassification Report:\n")

    print(
        classification_report(
            y_test,
            predictions,
            labels=CLASSES,
            zero_division=0
        )
    )

    os.makedirs("model", exist_ok=True)

    joblib.dump(model, MODEL_PATH)

    print("\nModel saved successfully!")
    print("Location:", os.path.abspath(MODEL_PATH))


if __name__ == "__main__":
    train_model()