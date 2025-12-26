"""
Migration Script: CSV to MongoDB
Migrates holiday data from holidays.csv to MongoDB holidays collection.
"""
import asyncio
import csv
from database import HolidayRepository
from config import CSV_FILE_PATH


async def migrate_csv_to_mongodb():
    """Migrate holidays from CSV to MongoDB."""
    print("Starting CSV to MongoDB migration...")

    # Read CSV file
    holidays_data = []
    try:
        with open(CSV_FILE_PATH, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                date = row.get("Date", "").strip()
                prompt = row.get("Prompt", "").strip()
                description = row.get("Description", "").strip() or None

                if date and prompt:
                    holidays_data.append({
                        "date": date,
                        "prompt": prompt,
                        "description": description
                    })

        print(f"Found {len(holidays_data)} holidays in CSV")

    except FileNotFoundError:
        print(f"CSV file not found: {CSV_FILE_PATH}")
        return
    except Exception as e:
        print(f"Error reading CSV: {str(e)}")
        return


    print("Clearing existing holidays from MongoDB...")
    await HolidayRepository.delete_all()


    success_count = 0
    error_count = 0

    for holiday in holidays_data:
        try:
            await HolidayRepository.create(
                date=holiday["date"],
                prompt=holiday["prompt"],
                description=holiday["description"]
            )
            success_count += 1
            print(f"Migrated: {holiday['date']} - {holiday['prompt']}")
        except Exception as e:
            error_count += 1
            print(f"Failed to migrate {holiday['date']}: {str(e)}")

    print("\n" + "="*60)
    print(f"Migration Complete!")
    print(f"Successfully migrated: {success_count} holidays")
    print(f"Failed: {error_count} holidays")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(migrate_csv_to_mongodb())
