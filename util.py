import sys

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

APP_TITLE = "Canadian Amateur Radio Quiz"


def get_key() -> str:
    """Read a single raw keypress from stdin without requiring Enter."""
    if sys.platform == "win32":
        # Windows systems
        import msvcrt

        return msvcrt.getwch()
    else:
        # Mac and Linux systems
        import termios
        import tty

        fd = sys.stdin.fileno()
        state = termios.tcgetattr(fd)
        try:
            _ = tty.setraw(fd)
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, state)
        return key


def print_header(console: Console, title: str = APP_TITLE) -> None:
    """Print the standard gold-on-blue double-border title panel."""
    console.print(
        Panel(
            f"[bold gold1]{title}[/]",
            box=box.DOUBLE,
            style="blue",
        )
    )
    console.print()


def make_table(*col_specs: tuple) -> Table:
    """
    Create the standard app table (rounded border, bold-cyan header).

    Each element of col_specs is a tuple of positional + keyword args passed
    directly to Table.add_column, e.g.:
        make_table(
            ("#", {"justify": "right", "style": "cyan"}),
            ("Course", {"style": "green"}),
        )
    """
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    for spec in col_specs:
        header, kwargs = spec
        table.add_column(header, **kwargs)
    return table
