#!/usr/bin/env python3
"""
CLI for Canadian Amateur Radio Question Banks for testing yourself.
"""

import json
import shutil
import zipfile
from pathlib import Path

import pandas as pd
import requests
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

app = typer.Typer()
console = Console()

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

    console.print(f"[cyan]Downloading {level.upper()} question bank...[/]", end="")
    response = requests.get(zip_url, stream=True)
    response.raise_for_status()

    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    console.print(" [green]✓[/]")

    console.print(f"[cyan]Extracting {level.upper()}...[/]", end="")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(level_dir)
    console.print(" [green]✓[/]")

    txt_files = list(level_dir.glob("*_delim.txt"))
    if not txt_files:
        console.print(f"[red]Error: Could not find delimited text file for {level}[/]")
        raise typer.Exit(code=1)

    txt_path = txt_files[0]

    console.print(f"[cyan]Processing {level.upper()} data to JSON...[/]", end="")

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

    console.print(" [green]✓[/]")


@app.command()
def update():
    """Update question banks (basic, advanced)."""
    console.print(
        Panel(
            "[bold gold1]Canadian Amateur Radio Question Bank Updater[/]",
            box=box.DOUBLE,
            style="blue",
        )
    )
    console.print()

    if DOWNLOAD_DIR.exists():
        shutil.rmtree(DOWNLOAD_DIR)
    DOWNLOAD_DIR.mkdir()
    DATA_DIR.mkdir(exist_ok=True)

    process_question_bank("basic")
    process_question_bank("advanced")

    if DOWNLOAD_DIR.exists():
        shutil.rmtree(DOWNLOAD_DIR)

    console.print()
    console.print(
        Panel(
            "[bold green]✓ Question banks updated successfully![/]",
            border_style="green",
        )
    )


@app.command()
def quiz():
    """Run interactive quiz."""
    from quiz import Quiz

    console.clear()

    # Title
    console.print(
        Panel(
            "[bold gold1]Canadian Amateur Radio Quiz[/]", box=box.DOUBLE, style="blue"
        )
    )
    console.print()

    # Level selection table
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Level", style="green")

    table.add_row("1", "Basic")
    table.add_row("2", "Advanced")

    console.print(table)
    console.print()
    console.print("[cyan]Select question level (1 or 2):[/] ", end="")

    choice = typer.prompt("", type=int)

    # Map choice to file
    files = {
        1: Path("data/amateur_basic_question.json"),
        2: Path("data/amateur_advanced_question.json"),
    }

    if choice not in files:
        console.print("[red]Invalid choice! Please select 1 or 2.[/]")
        raise typer.Exit(1)

    filepath = files[choice]

    if not filepath.exists():
        console.print(f"[red]File not found: {filepath}[/]")
        console.print(
            "[yellow]Run 'update' command first to download question banks.[/]"
        )
        raise typer.Exit(1)

    quiz = Quiz(filepath)
    quiz.run()


if __name__ == "__main__":
    app()
