#!/usr/bin/env python3
"""
CLI for Canadian Amateur Radio Question Banks for testing yourself.
"""

import typer
import requests
from pathlib import Path
import zipfile
import shutil
import pandas as pd
import json

app = typer.Typer()

ZIP_URLS = {
    "basic": "https://apc-cap.ic.gc.ca/datafiles/amat_basic_quest.zip",
    "advanced": "https://apc-cap.ic.gc.ca/datafiles/amat_adv_quest.zip",
}

CATEGORIES = {
    "A-001": "Advanced Theory",
    "A-002": "Advanced Components and Circuits",
    "A-003": "Measurements",
    "A-004": "Power Supplies",
    "A-005": "Transmitters, Modulation and Processing",
    "A-006": "Receivers",
    "A-007": "Feedlines - Matching and Antenna Systems",
    "B-001": "Regulation and Policies",
    "B-002": "Operating and Procedures",
    "B-003": "Station Assembly, Practice and Safety",
    "B-004": "Circuit Components",
    "B-005": "Basic Electronics and Theory",
    "B-006": "Feedlines and Antenna Systems",
    "B-007": "Radio Wave Propagation",
    "B-008": "Interference and Suppression",
}

DOWNLOAD_DIR = Path(".download")
DATA_DIR = Path("data")


def process_question_bank(level: str):
    zip_url = ZIP_URLS[level]
    level_dir = DOWNLOAD_DIR / level
    level_dir.mkdir(parents=True, exist_ok=True)
    zip_path = level_dir / f"{level}_questions.zip"

    typer.echo(f"Downloading {level.upper()} question bank...", nl=False)
    response = requests.get(zip_url, stream=True)
    response.raise_for_status()

    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    typer.echo(" done!")

    typer.echo(f"Extracting {level.upper()}...", nl=False)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(level_dir)
    typer.echo(" done!")

    txt_files = list(level_dir.glob("*_delim.txt"))
    if not txt_files:
        typer.echo(f"Error: Could not find delimited text file for {level}", err=True)
        raise typer.Exit(code=1)

    txt_path = txt_files[0]

    typer.echo(f"Processing {level.upper()} data to JSON...", nl=False)

    df = pd.read_csv(txt_path, sep=";", encoding="ISO-8859-1")
    df.columns = df.columns.str.strip()

    # Extract prefix (e.g. B-001) from ID (e.g. B-001-001-001)
    def get_prefix(qid):
        parts = str(qid).split("-")
        if len(parts) >= 2:
            return f"{parts[0]}-{parts[1]}"
        return "Unknown"

    df["category_code"] = df["question_id"].apply(get_prefix)

    df_final = df[
        [
            "question_id",
            "question_english",
            "correct_answer_english",
            "incorrect_answer_1_english",
            "incorrect_answer_2_english",
            "incorrect_answer_3_english",
            "category_code",
        ]
    ].copy()

    df_final.rename(
        columns={
            "question_id": "id",
            "question_english": "question",
            "correct_answer_english": "answer",
            "incorrect_answer_1_english": "distractor_1",
            "incorrect_answer_2_english": "distractor_2",
            "incorrect_answer_3_english": "distractor_3",
        },
        inplace=True,
    )

    output_data = {}
    for code, group in df_final.groupby("category_code"):
        title = CATEGORIES.get(code, "Unknown Category")
        questions = group.drop(columns=["category_code"]).to_dict(orient="records")
        output_data[code] = {"title": title, "questions": questions}

    output_json = DATA_DIR / f"amateur_{level}_question.json"

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    typer.echo(" done!")


@app.command()
def update():
    """Update question banks (basic, advanced)."""
    if DOWNLOAD_DIR.exists():
        shutil.rmtree(DOWNLOAD_DIR)
    DOWNLOAD_DIR.mkdir()
    DATA_DIR.mkdir(exist_ok=True)

    process_question_bank("basic")
    process_question_bank("advanced")

    if DOWNLOAD_DIR.exists():
        shutil.rmtree(DOWNLOAD_DIR)


@app.command()
def quiz():
    """Run interactive quiz."""
    from pathlib import Path
    from quiz import Quiz
    import typer

    data_dir = Path("data")
    json_files = list(data_dir.glob("*.json"))

    if not json_files:
        typer.echo("No JSON files found in data directory!")
        raise typer.Exit(1)

    typer.echo("Available question sets:")
    for idx, file in enumerate(json_files, 1):
        typer.echo(f"  {idx}. {file.name}")

    choice = typer.prompt("Select a file (number)", type=int)

    if 1 <= choice <= len(json_files):
        selected_file = json_files[choice - 1]
        quiz = Quiz(selected_file)
        quiz.run()
    else:
        typer.echo("Invalid selection!")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
