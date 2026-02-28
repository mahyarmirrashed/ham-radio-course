import json
import random
import sys
from pathlib import Path
from time import sleep

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from util import get_key, print_header

_console = Console()

# Shifted digit symbols → their base digit index (SHIFT+1=!, …, SHIFT+0=))
_SHIFTED_DIGIT_MAP = {
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


def quiz():
    """Run the interactive quiz."""
    while True:
        course_filepath = _prompt_for_course()

        if course_filepath is None:
            _console.clear()
            _console.print("[green]Thanks for using the quiz app![/]")
            break

        categories = _load_categories(course_filepath)
        categories_sorted = sorted(categories.items())

        while True:
            _show_category_menu(categories_sorted, categories)
            result = _prompt_for_category(categories_sorted)

            if result is None:
                break  # back to course selection

            idx, limit_questions = result
            questions = _load_category(idx, categories_sorted, categories)
            Quiz(questions, limit_questions).run()


# ------------------------------------------------------------------
# Course selection
# ------------------------------------------------------------------


def _prompt_for_course() -> Path | None:
    """Display course selection screen and return the chosen filepath via a single keypress.

    Returns None if the user presses 'q' to quit.
    """
    files = {
        "1": Path("data/amateur_basic_question.json"),
        "2": Path("data/amateur_advanced_question.json"),
    }

    while True:
        _console.clear()
        print_header(_console)

        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Course", style="green")
        table.add_row("1", "Basic")
        table.add_row("2", "Advanced")

        _console.print(table)
        _console.print()
        _console.print("[cyan]Press 1 or 2 to select a course, or 'q' to quit:[/]")

        key = get_key()

        if key == "q":
            return None

        if key in files:
            filepath = files[key]
            if not filepath.exists():
                _console.clear()
                _console.print(f"[red]File not found: {filepath}[/]")
                _console.print(
                    "[yellow]Run 'update' command first to download question banks.[/]"
                )
                sys.exit(1)
            return filepath


# ------------------------------------------------------------------
# Category selection
# ------------------------------------------------------------------


def _load_categories(filepath: Path) -> dict:
    """Load questions from a JSON file and return them organised by category."""
    categories: dict = {}

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    for _, content in data.items():
        title = content["title"]
        questions = content["questions"]
        if title not in categories:
            categories[title] = []
        categories[title].extend(questions)

    return categories


def _show_category_menu(categories_sorted: list, categories: dict) -> None:
    """Display the category selection menu."""
    _console.clear()
    print_header(_console)

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Questions", justify="right", style="yellow")

    total_qs = sum(len(qs) for qs in categories.values())
    table.add_row("0", "All Categories", str(total_qs))

    for idx, (cat_name, qs) in enumerate(categories_sorted, 1):
        table.add_row(str(idx), cat_name, str(len(qs)))

    _console.print(table)
    _console.print()
    _console.print(
        "[cyan]Press category number to start (SHIFT+number for all questions), or 'q' to return[/]"
    )


def _prompt_for_category(categories_sorted: list) -> tuple[int, bool] | None:
    """Wait for a keypress and return (category_idx, limit_questions), or None if 'q'."""
    while True:
        key = get_key()

        if key == "q":
            return None

        if key.isdigit():
            idx = int(key)
            if idx == 0 or 1 <= idx <= len(categories_sorted):
                return (idx, True)

        elif key in _SHIFTED_DIGIT_MAP:
            idx = _SHIFTED_DIGIT_MAP[key]
            if idx == 0 or 1 <= idx <= len(categories_sorted):
                return (idx, False)


def _load_category(idx: int, categories_sorted: list, categories: dict) -> list:
    """Return the list of questions for the given category index."""
    if idx == 0:
        questions = []
        for qs in categories.values():
            questions.extend(qs)
        return questions

    cat_name = categories_sorted[idx - 1][0]
    return categories[cat_name].copy()


# ------------------------------------------------------------------
# Quiz session
# ------------------------------------------------------------------


class Quiz:
    def __init__(self, questions: list, limit_questions: bool):
        self.console = Console()
        self.questions = questions
        self.limit_questions = limit_questions
        self.questions_answered_incorrectly: list = []
        self.current_index = 0
        self.score = 0
        self.current_choices: list = []

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

    def run(self) -> None:
        """Run the quiz session."""
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
