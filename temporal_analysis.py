import sqlite3
from datetime import datetime
import os


DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "cropcare.db"
)


# --------------------------------
# DATABASE CONNECTION
# --------------------------------

def get_connection():
    return sqlite3.connect(DATABASE)


# --------------------------------
# CREATE DATABASE
# --------------------------------

def create_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS severity_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            plant_id TEXT NOT NULL,

            image_name TEXT,

            severity_percentage REAL NOT NULL,

            severity_level TEXT NOT NULL,

            recorded_at TEXT NOT NULL,

            prediction TEXT DEFAULT 'Unknown'

        )
    """)

    # Add prediction column to an existing database
    cursor.execute(
        "PRAGMA table_info(severity_history)"
    )

    columns = [
        column[1]
        for column in cursor.fetchall()
    ]

    if "prediction" not in columns:

        cursor.execute("""
            ALTER TABLE severity_history
            ADD COLUMN prediction TEXT DEFAULT 'Unknown'
        """)

    connection.commit()
    connection.close()


# --------------------------------
# SAVE ANALYSIS RECORD
# --------------------------------

def save_severity(
    plant_id,
    image_name,
    severity_percentage,
    severity_level,
    prediction="Unknown"
):

    create_database()

    connection = get_connection()
    cursor = connection.cursor()

    recorded_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute("""
        INSERT INTO severity_history
        (
            plant_id,
            image_name,
            severity_percentage,
            severity_level,
            recorded_at,
            prediction
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        plant_id,
        image_name,
        severity_percentage,
        severity_level,
        recorded_at,
        prediction
    ))

    connection.commit()
    connection.close()


# --------------------------------
# TEMPORAL ANALYSIS
# --------------------------------

def analyze_trend(plant_id):

    create_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT severity_percentage, recorded_at

        FROM severity_history

        WHERE plant_id = ?

        ORDER BY recorded_at ASC, id ASC
    """, (plant_id,))

    records = cursor.fetchall()

    connection.close()

    if len(records) < 2:

        return {
            "trend": "Insufficient Data",
            "message": "Upload at least two records for temporal analysis.",
            "records": records
        }

    first_severity = records[0][0]
    latest_severity = records[-1][0]

    difference = round(
        latest_severity - first_severity,
        2
    )

    if difference > 2:

        trend = "Increasing"

        message = (
            "Disease severity has increased by "
            + str(difference)
            + "%."
        )

    elif difference < -2:

        trend = "Decreasing"

        message = (
            "Disease severity has decreased by "
            + str(abs(difference))
            + "%."
        )

    else:

        trend = "Stable"

        message = "Disease severity is relatively stable."

    return {
        "trend": trend,
        "difference": difference,
        "message": message,
        "records": records
    }


# --------------------------------
# GET ALL HISTORY
# --------------------------------

def get_all_history():

    create_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            plant_id,
            image_name,
            severity_percentage,
            severity_level,
            recorded_at,
            prediction

        FROM severity_history

        ORDER BY recorded_at DESC, id DESC
    """)

    records = cursor.fetchall()

    connection.close()

    return records


# --------------------------------
# DASHBOARD STATISTICS
# --------------------------------

def get_dashboard_stats():

    create_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM severity_history
    """)

    total_analyses = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT plant_id)
        FROM severity_history
    """)

    plants_monitored = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM severity_history
        WHERE LOWER(prediction) LIKE '%healthy%'
    """)

    healthy_crops = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM severity_history
        WHERE prediction != 'Unknown'
        AND LOWER(prediction) NOT LIKE '%healthy%'
    """)

    diseased_crops = cursor.fetchone()[0]

    # Disease distribution

    cursor.execute("""
        SELECT prediction, COUNT(*)
        FROM severity_history
        WHERE prediction != 'Unknown'
        GROUP BY prediction
    """)

    disease_distribution = cursor.fetchall()

    # Recent severity records

    cursor.execute("""
        SELECT
            plant_id,
            severity_percentage,
            recorded_at

        FROM severity_history

        ORDER BY recorded_at ASC, id ASC
    """)

    severity_records = cursor.fetchall()

    connection.close()

    return {
        "total_analyses": total_analyses,
        "plants_monitored": plants_monitored,
        "healthy_crops": healthy_crops,
        "diseased_crops": diseased_crops,
        "disease_distribution": disease_distribution,
        "severity_records": severity_records
    }