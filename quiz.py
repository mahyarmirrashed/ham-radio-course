import json
import random
import sys
import tty
import termios
from pathlib import Path
from time import sleep

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box

DATA_DIR = Path("data")


class Quiz:
    def __init__(self):
        self.console = Console()
        self.questions = []
        self.current_q_index = 0
        self.score = 0
        self.categories = {}
        self.state = "MENU"  # MENU, QUIZ, RESULT
        self.selected_category = None
        self.last_feedback = ""

    def load_data(self):
        files = list(DATA_DIR.glob("*.json"))
        if not files:
            return False

        for f in files:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
                for code, content in data.items():
                    title = content["title"]
                    qs = content["questions"]
                    if title not in self.categories:
                        self.categories[title] = []
                    self.categories[title].extend(qs)
        return True

    def get_key(self):
        """Simple cross-platform key reader (Unix version)."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def make_layout(self):
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3),
        )
        return layout

    def render_header(self):
        title = "Canadian Amateur Radio Quiz"
        if self.state == "QUIZ":
            title += f" | Category: {self.selected_category}"
        return Panel(
            Align.center(f"[bold gold1]{title}[/]", vertical="middle"),
            style="white on blue",
        )

    def render_footer(self):
        if self.state == "MENU":
            text = "Press [bold]Category Number[/] to start | [bold]q[/] to quit"
        elif self.state == "QUIZ":
            text = "Press [bold]1-4[/] to answer | [bold]q[/] to quit menu"
        else:
            text = "Press [bold]q[/] to quit"
        return Panel(Align.center(text, vertical="middle"), style="white on blue")

    def render_menu(self):
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Category", style="green")
        table.add_column("Questions", justify="right")

        cats = sorted(self.categories.items())
        # "All" option
        table.add_row("0", "All Categories", str(sum(len(v) for v in cats)))

        for idx, (name, qs) in enumerate(cats, 1):
            table.add_row(str(idx), name, str(len(qs)))

        return Panel(
            Align.center(table, vertical="middle"),
            title="Main Menu",
            border_style="green",
        )

    def render_quiz(self):
        q = self.questions[self.current_q_index]

        # Question Panel
        q_text = f"[bold white]{q['question']}[/]"
        q_panel = Panel(
            Align.center(q_text, vertical="middle"),
            title=f"Question {self.current_q_index + 1}/{len(self.questions)}",
            border_style="blue",
            padding=(1, 2),
        )

        # Choices Table
        grid = Table.grid(expand=True, padding=(1, 2))
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="center", ratio=1)

        # Randomize choices if not already done (we do it in loop logic usually, but here simple)
        # For display, we just assume they are shuffled in self.current_choices

        c = self.current_choices
        grid.add_row(
            Panel(f"[bold]1.[/] {c[0]}", border_style="white"),
            Panel(f"[bold]2.[/] {c[1]}", border_style="white"),
        )
        grid.add_row(
            Panel(f"[bold]3.[/] {c[2]}", border_style="white"),
            Panel(f"[bold]4.[/] {c[3]}", border_style="white"),
        )

        # Body Layout
        body = Layout()
        body.split(
            Layout(q_panel, ratio=1),
            Layout(Align.center(self.last_feedback, vertical="middle"), size=3),
            Layout(grid, ratio=2),
        )
        return body

    def render_result(self):
        score_pct = (self.score / len(self.questions)) * 100
        panel = Panel(
            Align.center(
                f"[bold]Quiz Complete![/]\n\n"
                f"Score: [bold green]{self.score}[/] / {len(self.questions)}\n"
                f"Percentage: [bold yellow]{score_pct:.1f}%[/]",
                vertical="middle",
            ),
            title="Results",
            border_style="gold1",
        )
        return panel

    def run(self):
        if not self.load_data():
            print("No data found! Run 'update' first.")
            return

        # Prepare Menu Options
        menu_options = ["All Categories"] + sorted(self.categories.keys())

        with Live(self.make_layout(), screen=True, refresh_per_second=10) as live:
            while True:
                layout = self.make_layout()
                layout["header"].update(self.render_header())
                layout["footer"].update(self.render_footer())

                if self.state == "MENU":
                    layout["body"].update(self.render_menu())
                    live.update(layout)

                    key = self.get_key()
                    if key == "q":
                        break

                    if key.isdigit():
                        idx = int(key)
                        if 0 <= idx < len(menu_options):
                            self.selected_category = menu_options[idx]

                            # Load Questions
                            if idx == 0:  # All
                                self.questions = []
                                for qs in self.categories.values():
                                    self.questions.extend(qs)
                            else:
                                self.questions = self.categories[self.selected_category]

                            random.shuffle(self.questions)
                            self.questions = self.questions[:20]  # Limit to 20
                            self.current_q_index = 0
                            self.score = 0
                            self.state = "QUIZ"

                            # Prep first question
                            self.prepare_question()

                elif self.state == "QUIZ":
                    layout["body"].update(self.render_quiz())
                    live.update(layout)

                    key = self.get_key()
                    if key == "q":
                        self.state = "MENU"
                        continue

                    if key in ["1", "2", "3", "4"]:
                        idx = int(key) - 1
                        selected_ans = self.current_choices[idx]
                        correct_ans = self.questions[self.current_q_index]["answer"]

                        if selected_ans == correct_ans:
                            self.score += 1
                            self.last_feedback = "[bold green]Correct![/]"
                        else:
                            self.last_feedback = (
                                f"[bold red]Wrong! Answer was: {correct_ans}[/]"
                            )

                        # Show feedback briefly
                        layout["body"].update(self.render_quiz())
                        live.update(layout)
                        sleep(1.5)
                        self.last_feedback = ""

                        self.current_q_index += 1
                        if self.current_q_index >= len(self.questions):
                            self.state = "RESULT"
                        else:
                            self.prepare_question()

                elif self.state == "RESULT":
                    layout["body"].update(self.render_result())
                    live.update(layout)
                    if self.get_key() == "q":
                        self.state = "MENU"

    def prepare_question(self):
        q = self.questions[self.current_q_index]
        choices = [q["answer"], q["distractor_1"], q["distractor_2"], q["distractor_3"]]
        random.shuffle(choices)
        self.current_choices = choices
