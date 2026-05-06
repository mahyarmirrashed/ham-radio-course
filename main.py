#!/usr/bin/env python3
"""CLI for Canadian Amateur Radio question banks (both basic and
advanced)."""

import typer

from cmd import test, update

app = typer.Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Canadian Amateur Radio exam practice tool."""
    if ctx.invoked_subcommand is None:
        test()


_ = app.command()(test)
_ = app.command()(update)

if __name__ == "__main__":
    app()
