#!/usr/bin/env python3
"""
CLI for Canadian Amateur Radio Question Banks for testing yourself.
"""

import typer
import requests
from pathlib import Path
import zipfile
from typing import Annotated

app = typer.Typer()

# Official ZIP URLs
ZIP_URLS = {
    "basic": "https://apc-cap.ic.gc.ca/datafiles/amat_basic_quest.zip",
    "advanced": "https://apc-cap.ic.gc.ca/datafiles/amat_adv_quest.zip",
}

DATA_DIR = Path("data")


def download_and_extract(level: str, output_dir: Path, force: bool):
    """Shared logic for downloading/extracting a level."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    zip_url = ZIP_URLS[level]
    extract_dir = output_dir / level
    extract_dir.mkdir(parents=True, exist_ok=True)

    zip_path = extract_dir / f"{level}_questions.zip"

    if zip_path.exists() and not force:
        typer.confirm(f"{zip_path} already exists. Overwrite?", abort=True)

    # Download
    typer.echo(f"Downloading {level.upper()} question bank...", nl=False)
    response = requests.get(zip_url, stream=True)
    response.raise_for_status()

    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    typer.echo(" done!")

    # Extract
    typer.echo("Extracting...", nl=False)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    typer.echo(" done!")


@app.command()
def update(
    force: Annotated[bool, typer.Option("-f", "--force")] = False,
    output: Annotated[Path, typer.Option("-o", "--output")] = DATA_DIR,
):
    """
    Update question banks (basic, advanced).
    """
    download_and_extract("basic", output, force)
    download_and_extract("advanced", output, force)


if __name__ == "__main__":
    app()
