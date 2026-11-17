import cv2
import numpy as np


def estimate_severity(image_path):

    # Read image
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("Unable to read the uploaded image.")

    # Resize image
    image = cv2.resize(image, (500, 500))

    # Convert BGR to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # ---------------------------------
    # STEP 1: LEAF SEGMENTATION
    # ---------------------------------

    height, width = image.shape[:2]

    mask = np.zeros((height, width), np.uint8)

    background_model = np.zeros((1, 65), np.float64)
    foreground_model = np.zeros((1, 65), np.float64)

    rectangle = (
        5,
        5,
        width - 10,
        height - 10
    )

    cv2.grabCut(
        image,
        mask,
        rectangle,
        background_model,
        foreground_model,
        5,
        cv2.GC_INIT_WITH_RECT
    )

    leaf_mask = np.where(
        (mask == cv2.GC_FGD) |
        (mask == cv2.GC_PR_FGD),
        255,
        0
    ).astype("uint8")

    # Keep largest foreground region
    contours, _ = cv2.findContours(
        leaf_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        raise ValueError("Leaf region could not be detected.")

    largest_contour = max(
        contours,
        key=cv2.contourArea
    )

    leaf_mask = np.zeros_like(leaf_mask)

    cv2.drawContours(
        leaf_mask,
        [largest_contour],
        -1,
        255,
        thickness=cv2.FILLED
    )

    # ---------------------------------
    # STEP 2: DISEASE REGION DETECTION
    # ---------------------------------

    # Brown and yellow lesion ranges
    lower_brown = np.array([5, 40, 20])
    upper_brown = np.array([25, 255, 220])

    lower_yellow = np.array([20, 40, 40])
    upper_yellow = np.array([35, 255, 230])

    brown_mask = cv2.inRange(
        hsv,
        lower_brown,
        upper_brown
    )

    yellow_mask = cv2.inRange(
        hsv,
        lower_yellow,
        upper_yellow
    )

    disease_mask = cv2.bitwise_or(
        brown_mask,
        yellow_mask
    )

    # Consider disease pixels only inside leaf
    disease_mask = cv2.bitwise_and(
        disease_mask,
        leaf_mask
    )

    # Remove small noise
    kernel = np.ones((3, 3), np.uint8)

    disease_mask = cv2.morphologyEx(
        disease_mask,
        cv2.MORPH_OPEN,
        kernel
    )

    # ---------------------------------
    # STEP 3: SEVERITY CALCULATION
    # ---------------------------------

    total_leaf_pixels = cv2.countNonZero(leaf_mask)

    affected_pixels = cv2.countNonZero(disease_mask)

    if total_leaf_pixels == 0:
        raise ValueError("Unable to identify leaf area.")

    severity_percentage = round(
        (affected_pixels / total_leaf_pixels) * 100,
        2
    )

    # ---------------------------------
    # STEP 4: SEVERITY CLASSIFICATION
    # ---------------------------------

    if severity_percentage < 20:
        severity_level = "Low"

    elif severity_percentage < 50:
        severity_level = "Medium"

    else:
        severity_level = "High"

    return {
        "severity_percentage": severity_percentage,
        "severity_level": severity_level
    }