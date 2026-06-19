import os
import subprocess
import time
import webbrowser
from pathlib import Path

# =====================================
# NEXUSMIND AI PROJECT LAUNCHER
# =====================================

PROJECT_NAME = "NEXUSMIND AI"

# Configure your services here
SERVICES = [
    {
        "name": "Backend",
        "folder": "backend",
        "command": "npm run dev"
    },
    {
        "name": "Frontend",
        "folder": "frontend",
        "command": "npm run dev"
    },
    {
        "name": "AI Service",
        "folder": "ai-service",
        "command": "python app.py"
    }
]

# Main URL
PROJECT_URL = "http://localhost:3000"

# =====================================
# FUNCTIONS
# =====================================

def print_header():
    print("=" * 60)
    print(f"          {PROJECT_NAME} LAUNCHER")
    print("=" * 60)
    print()


def folder_exists(folder):
    return Path(folder).exists()


def start_service(service):
    name = service["name"]
    folder = service["folder"]
    command = service["command"]

    print(f"[INFO] Starting {name}...")

    if not folder_exists(folder):
        print(f"[ERROR] Folder not found: {folder}")
        return False

    try:
        subprocess.Popen(
            f'start "{name}" cmd /k "cd /d {folder} && {command}"',
            shell=True
        )

        print(f"[SUCCESS] {name} launched")
        return True

    except Exception as e:
        print(f"[FAILED] {name}")
        print(e)
        return False


def launch_all_services():
    print("\nStarting Services...\n")

    success_count = 0

    for service in SERVICES:
        if start_service(service):
            success_count += 1

        time.sleep(2)

    return success_count


def open_project():
    print("\nWaiting for services to initialize...\n")

    time.sleep(10)

    try:
        webbrowser.open(PROJECT_URL)
        print(f"[SUCCESS] Browser opened -> {PROJECT_URL}")

    except Exception as e:
        print("[FAILED] Browser launch")
        print(e)


# =====================================
# MAIN
# =====================================

if __name__ == "__main__":

    print_header()

    total = len(SERVICES)

    started = launch_all_services()

    print()
    print("=" * 60)
    print(f"Started {started}/{total} services")
    print("=" * 60)

    open_project()

    print("\nNEXUSMIND AI is launching...")
    print("Check the opened CMD windows for logs.")
    print("\nPress ENTER to exit launcher.")

    input()