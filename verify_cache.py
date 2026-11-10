
import json
from pathlib import Path

CACHE_DIR = Path("data/cache")

TEMP_EXTENSIONS = {
    ".tmp",
    ".temp",
    ".bak",
    ".old",
    ".part"
}

def verify_cache():
    print("\nCACHE INTEGRITY VERIFICATION")
    print("=" * 40)

    if not CACHE_DIR.exists():
        print("ERROR: Cache directory not found.")
        return

    json_files = list(CACHE_DIR.glob("*.json"))
    temp_files = [
        file for file in CACHE_DIR.iterdir()
        if file.is_file() and file.suffix.lower() in TEMP_EXTENSIONS
    ]

    valid_count = 0
    invalid_count = 0

    for file_path in json_files:
        try:
            with file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            print(f"VALID: {file_path.name}")
            print(f"  Data type: {type(data).__name__}")
            valid_count += 1

        except json.JSONDecodeError as error:
            print(f"INVALID: {file_path.name}")
            print(f"  Error: {error}")
            invalid_count += 1

    print("\nTEMPORARY ARTIFACTS")
    if temp_files:
        for file_path in temp_files:
            print(f"FOUND: {file_path.name}")
    else:
        print("No temporary artifacts found.")

    print("\nSUMMARY")
    print(f"Valid JSON files: {valid_count}")
    print(f"Invalid JSON files: {invalid_count}")
    print(f"Temporary artifacts found: {len(temp_files)}")

    if invalid_count == 0:
        print("\nJSON INTEGRITY CHECK PASSED")
    else:
        print("\nJSON INTEGRITY CHECK FAILED")


if __name__ == "__main__":
    verify_cache()
