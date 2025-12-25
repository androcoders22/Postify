"""
CSV Service - Holiday CSV parsing.
"""
import csv
from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from config import CSV_FILE_PATH


def parse_csv_for_today() -> Optional[str]:
    """Parse the CSV file and return today's holiday if found."""
    today = datetime.now().strftime("%d-%m-%Y")

    try:
        with open(CSV_FILE_PATH, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Date"].strip() == today:
                    return row["Prompt"].strip()
    except FileNotFoundError:
        raise HTTPException(
            status_code=500, detail=f"CSV file not found: {CSV_FILE_PATH}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading CSV: {str(e)}")

    return None
