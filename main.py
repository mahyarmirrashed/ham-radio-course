#!/usr/bin/env python3
"""
CLI for Canadian Amateur Radio question banks (both basic and advanced).
"""

import typer

from quiz import quiz
from update import update

app = typer.Typer()
_ = app.command()(update)
_ = app.command()(quiz)

if __name__ == "__main__":
    app()
