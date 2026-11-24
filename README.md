# StudyFlow — Python Flask Study Planner

A beginner-friendly study planner built with **Python Flask, SQLite, HTML, CSS and JavaScript**.

## Features
- User registration and login (passwords are hashed with Werkzeug)
- Personal dashboard with study statistics and a 7-day study chart
- Create and manage subjects
- Create, edit and delete flashcards
- Due-card practice with an SM-2-inspired spaced repetition scheduler
- 25-minute focus / 5-minute break timer
- Save completed focus sessions and track daily study time
- Responsive layout for desktop and mobile

## Requirements
- Python 3.9 or newer
- VS Code (recommended)

## Run on Windows
1. Extract the ZIP file.
2. Open the extracted `studyflow-flask` folder in VS Code.
3. Open **Terminal → New Terminal**.
4. Create a virtual environment:
   ```bash
   py -m venv .venv
   ```
5. Activate it:
   ```bash
   .venv\Scripts\activate
   ```
   If PowerShell blocks activation, use Command Prompt terminal, or run:
   ```bash
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   .venv\Scripts\python.exe app.py
   ```
6. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
7. Start the app:
   ```bash
   python app.py
   ```
8. Open the address printed in the terminal, usually `http://127.0.0.1:5000`.

## First use
Register an account, add subjects, create flashcards, then open Practice to review cards due today. Use the Timer on the dashboard and select a subject before starting a focus session.

## Database
SQLite database `studyflow.db` is created automatically the first time the app runs. It is stored locally in this project folder.

## Security note
This is a college-project/local-development version. Passwords are hashed, but before public deployment you should set a strong random `SECRET_KEY`, disable Flask debug mode, use HTTPS, add CSRF protection, and configure secure session cookies. Do not publish your local database or secret key.
