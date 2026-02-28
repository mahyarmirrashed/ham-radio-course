import json
import random
import sys
from pathlib import Path
from time import sleep

from rich import box
from rich.console import Console
from rich.panel import Panel

from util import get_key, make_table, print_header


def select_level(console: Console) -> Path | None:
    """Display course selection screen and return the chosen filepath via a single keypress.

    Returns None if the user presses 'q' to quit.
    """
    files = {
        "1": Path("data/amateur_basic_question.json"),
        "2": Path("data/amateur_advanced_question.json"),
    }

    while True:
        print_header(console)

        table = make_table(
            ("#", {"justify": "right", "style": "cyan"}),
            ("Course", {"style": "green"}),
        )
        table.add_row("1", "Basic")
        table.add_row("2", "Advanced")

        console.print(table)
        console.print()
        console.print("[cyan]Press 1 or 2 to select a course, or 'q' to quit:[/]")

        key = get_key()

        if key == "q":
            return None

        if key in files:
            filepath = files[key]
            if not filepath.exists():
                console.clear()
                console.print(f"[red]File not found: {filepath}[/]")
                console.print(
                    "[yellow]Run 'update' command first to download question banks.[/]"
                )
                sys.exit(1)
            return filepath


class Quiz:
    def __init__(self, filepath: Path):
        self.console = Console()
        self.categories: dict = {}
        self.questions: list = []
        self.questions_answered_incorrectly: list = []
        self.current_index = 0
        self.score = 0
        self.current_choices: list = []
        self.limit_questions = True

        self._load(filepath)

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def _load(self, filepath: Path) -> None:
        """Load questions from JSON file and organize by category."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        for _, content in data.items():
            title = content["title"]
            questions = content["questions"]
            if title not in self.categories:
                self.categories[title] = []
            self.categories[title].extend(questions)

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def _show_menu(self, sorted_cats: list) -> None:
        """Display category selection menu."""
        print_header(self.console)

        table = make_table(
            ("#", {"justify": "right", "style": "cyan"}),
            ("Category", {"style": "green"}),
            ("Questions", {"justify": "right", "style": "yellow"}),
        )

        total_qs = sum(len(qs) for qs in self.categories.values())
        table.add_row("0", "All Categories", str(total_qs))

        for idx, (cat_name, qs) in enumerate(sorted_cats, 1):
            table.add_row(str(idx), cat_name, str(len(qs)))

        self.console.print(table)
        self.console.print()
        self.console.print(
            "[cyan]Press category number to start (SHIFT+number for all questions), or 'q' to return[/]"
        )

    # ------------------------------------------------------------------
    # Category selection
    # ------------------------------------------------------------------

    def _load_category(self, idx: int, sorted_cats: list) -> str | None:
        """Populate self.questions for the given category index.

        Returns the category name, or None if idx is out of range.
        """
        if idx == 0:
            self.questions = []
            for qs in self.categories.values():
                self.questions.extend(qs)
            return "All Categories"

        if 1 <= idx <= len(sorted_cats):
            cat_name = sorted_cats[idx - 1][0]
            self.questions = self.categories[cat_name].copy()
            return cat_name

        return None

    def _select_category(self, sorted_cats: list) -> str | None:
        """Wait for a keypress and resolve the chosen category.

        Returns the category name, or None if the user presses 'q'.
        """
        # Shifted digit symbols → their base digit (SHIFT+1=!, …, SHIFT+0=))
        shifted_digit_map = {
            "!": 1,
            "@": 2,
            "#": 3,
            "$": 4,
            "%": 5,
            "^": 6,
            "&": 7,
            "*": 8,
            "(": 9,
            ")": 0,
        }

        while True:
            key = get_key()

            if key == "q":
                return None

            if key.isdigit():
                self.limit_questions = True
                result = self._load_category(int(key), sorted_cats)
                if result is not None:
                    return result

            elif key in shifted_digit_map:
                self.limit_questions = False
                result = self._load_category(shifted_digit_map[key], sorted_cats)
                if result is not None:
                    return result

    # ------------------------------------------------------------------
    # Quiz flow
    # ------------------------------------------------------------------

    def _prepare_quiz(self) -> None:
        """Shuffle questions and apply the 20-question cap when appropriate."""
        random.shuffle(self.questions)
        if self.limit_questions:
            self.questions = self.questions[:20]
        self.current_index = 0
        self.score = 0
        self.questions_answered_incorrectly = []

    def _show_question(self) -> None:
        """Display the current question and its shuffled answer choices."""
        self.console.clear()

        q = self.questions[self.current_index]

        self.console.print(
            Panel(
                f"[bold]Question {self.current_index + 1} of {len(self.questions)}[/]",
                style="blue",
            )
        )
        self.console.print()

        self.console.print(
            Panel(
                f"[bold white]{q['id']}: {q['question']}[/]",
                box=box.ROUNDED,
                border_style="cyan",
                padding=(1, 2),
            )
        )
        self.console.print()

        choices = [q["answer"], q["distractor_1"], q["distractor_2"], q["distractor_3"]]
        random.shuffle(choices)
        self.current_choices = choices

        for i, choice in enumerate(choices, 1):
            self.console.print(f"  [bold cyan]{i}.[/] {choice}")

        self.console.print()
        self.console.print("[dim]Press 1-4 to answer, 'q' to return[/]")

    def _check_answer(self, choice_num: int) -> bool:
        """Validate the selected answer and display immediate feedback.

        Returns True if correct, False if wrong.
        """
        q = self.questions[self.current_index]
        selected = self.current_choices[choice_num - 1]
        correct = q["answer"]

        self.console.print()

        if selected == correct:
            self.score += 1
            self.console.print(Panel("[bold green]✓ Correct![/]", border_style="green"))
            return True
        else:
            self.questions_answered_incorrectly.append(
                {"question": q, "your_answer": selected, "correct_answer": correct}
            )
            self.console.print(
                Panel(
                    f"[bold red]✗ Wrong![/]\n\nCorrect answer: [yellow]{correct}[/]",
                    border_style="red",
                )
            )
            return False

    def _show_incorrect_questions(self) -> None:
        """Display all incorrectly answered questions for review."""
        if not self.questions_answered_incorrectly:
            return

        self.console.clear()
        self.console.print(
            Panel(
                f"[bold red]Review Incorrect Answers ({len(self.questions_answered_incorrectly)} questions)[/]",
                box=box.DOUBLE,
                border_style="red",
                padding=(1, 2),
            )
        )
        self.console.print()

        for idx, item in enumerate(self.questions_answered_incorrectly, 1):
            q = item["question"]
            self.console.print(f"[bold yellow]Question {idx}:[/] [cyan]{q['id']}[/]")
            self.console.print(f"[white]{q['question']}[/]")
            self.console.print()
            self.console.print(f"  [bold red]Your answer:[/] {item['your_answer']}")
            self.console.print(
                f"  [bold green]Correct answer:[/] {item['correct_answer']}"
            )
            self.console.print()
            self.console.print("[dim]" + "─" * 80 + "[/dim]")
            self.console.print()

        self.console.print("[cyan]Press any key to continue[/]")
        get_key()

    def _show_results(self) -> None:
        """Display the final score and optionally review incorrect answers."""
        self.console.clear()

        percentage = (self.score / len(self.questions)) * 100
        self.console.print(
            Panel(
                f"[bold gold1]Quiz Complete![/]\n\n"
                f"Score: [bold green]{self.score}[/] / {len(self.questions)}\n"
                f"Percentage: [bold yellow]{percentage:.1f}%[/]",
                box=box.DOUBLE,
                border_style="gold1",
                padding=(2, 4),
            )
        )
        self.console.print()

        if self.questions_answered_incorrectly:
            self.console.print("[cyan]Press any key to review incorrect answers[/]")
        else:
            self.console.print("[cyan]Press any key to return to menu[/]")

        get_key()

        if self.questions_answered_incorrectly:
            self._show_incorrect_questions()

    def _run_quiz(self) -> None:
        """Run one quiz session for the selected category."""
        self._prepare_quiz()

        while self.current_index < len(self.questions):
            self._show_question()

            while True:
                key = get_key()

                if key == "q":
                    return

                if key in ["1", "2", "3", "4"]:
                    correct = self._check_answer(int(key))
                    if correct:
                        sleep(2)
                    else:
                        self.console.print()
                        self.console.print("[cyan]Press any key to continue[/]")
                        get_key()
                    self.current_index += 1
                    break

        self._show_results()

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Main loop: show the category menu until the user returns to course selection."""
        sorted_cats = sorted(self.categories.items())

        while True:
            self._show_menu(sorted_cats)
            category = self._select_category(sorted_cats)

            if category is None:
                return

            self._run_quiz()
