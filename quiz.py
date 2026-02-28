import json
import random
import sys
from pathlib import Path
from time import sleep

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from models import Category, IncorrectAnswer, Question
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

        while True:
            _show_category_menu(categories)
            category = _prompt_for_category(categories)

            if category is None:
                break  # back to course selection

            category_idx, limit_questions = category
            questions = _load_category(category_idx, categories)
            Quiz(questions, limit_questions).run()


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


def _load_categories(filepath: Path) -> list[Category]:
    """Load questions from a JSON file and return categories in code order."""
    categories: list[Category] = []

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    for _, content in sorted(data.items()):
        questions = [Question(**question) for question in content["questions"]]
        categories.append(Category(title=content["title"], questions=questions))

    return categories


def _show_category_menu(categories: list[Category]) -> None:
    """Display the category selection menu."""
    _console.clear()
    print_header(_console)

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Questions", justify="right", style="yellow")

    total_questions = sum(len(c.questions) for c in categories)
    table.add_row("0", "All Categories", str(total_questions))

    for idx, category in enumerate(categories, 1):
        table.add_row(str(idx), category.title, str(len(category.questions)))

    _console.print(table)
    _console.print()
    _console.print(
        "[cyan]Press category number to start (SHIFT+number for all questions), or 'q' to return[/]"
    )


def _prompt_for_category(categories: list[Category]) -> tuple[int, bool] | None:
    """Wait for a keypress and return (category_idx, limit_questions), or None if 'q'."""
    while True:
        key = get_key()

        if key == "q":
            return None

        if key.isdigit():
            idx = int(key)
            if idx == 0 or 1 <= idx <= len(categories):
                return (idx, True)

        elif key in _SHIFTED_DIGIT_MAP:
            idx = _SHIFTED_DIGIT_MAP[key]
            if idx == 0 or 1 <= idx <= len(categories):
                return (idx, False)


def _load_category(idx: int, categories: list[Category]) -> list[Question]:
    """Return the list of questions for the given category index."""
    if idx == 0:
        questions: list[Question] = []
        for category in categories:
            questions.extend(category.questions)
        return questions

    return categories[idx - 1].questions.copy()


# ------------------------------------------------------------------
# Quiz session
# ------------------------------------------------------------------


class Quiz:
    def __init__(self, questions: list[Question], limit_questions: bool):
        self.console = Console()
        self.questions: list[Question] = questions
        self.limit_questions = limit_questions
        self.incorrect: list[IncorrectAnswer] = []
        self.current_index = 0
        self.score = 0
        self.current_choices: list[str] = []

    def _prepare_quiz(self) -> None:
        """Shuffle questions and apply the 20-question cap when appropriate."""
        random.shuffle(self.questions)
        if self.limit_questions:
            self.questions = self.questions[:20]
        self.current_index = 0
        self.score = 0
        self.incorrect = []

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
                f"[bold white]{q.id}: {q.question}[/]",
                box=box.ROUNDED,
                border_style="cyan",
                padding=(1, 2),
            )
        )
        self.console.print()

        choices = q.choices()
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

        self.console.print()

        if selected == q.answer:
            self.score += 1
            self.console.print(Panel("[bold green]✓ Correct![/]", border_style="green"))
            return True
        else:
            self.incorrect.append(
                IncorrectAnswer(question=q, answer=selected, correct_answer=q.answer)
            )
            self.console.print(
                Panel(
                    f"[bold red]✗ Wrong![/]\n\nCorrect answer: [yellow]{q.answer}[/]",
                    border_style="red",
                )
            )
            return False

    def _show_incorrect_questions(self) -> None:
        """Display all incorrectly answered questions for review."""
        if not self.incorrect:
            return

        self.console.clear()
        self.console.print(
            Panel(
                f"[bold red]Review Incorrect Answers ({len(self.incorrect)} questions)[/]",
                box=box.DOUBLE,
                border_style="red",
                padding=(1, 2),
            )
        )
        self.console.print()

        for idx, item in enumerate(self.incorrect, 1):
            self.console.print(
                f"[bold yellow]Question {idx}:[/] [cyan]{item.question.id}[/]"
            )
            self.console.print(f"[white]{item.question.question}[/]")
            self.console.print()
            self.console.print(f"  [bold red]Your answer:[/] {item.answer}")
            self.console.print(
                f"  [bold green]Correct answer:[/] {item.correct_answer}"
            )
            self.console.print()
            self.console.print("[dim]" + "─" * 80 + "[/dim]")
            self.console.print()

        self.console.print("[cyan]Press any key to continue[/]")
        _ = get_key()

    def _show_results(self) -> None:
        """Display the final score and optionally review incorrect answers."""
        self.console.clear()

        percentage = (self.score / len(self.questions)) * 100
        self.console.print(
            Panel(
                f"[bold gold1]Quiz Complete![/]\n\n"
                + f"Score: [bold green]{self.score}[/] / {len(self.questions)}\n"
                + f"Percentage: [bold yellow]{percentage:.1f}%[/]",
                box=box.DOUBLE,
                border_style="gold1",
                padding=(2, 4),
            )
        )
        self.console.print()

        if self.incorrect:
            self.console.print("[cyan]Press any key to review incorrect answers[/]")
        else:
            self.console.print("[cyan]Press any key to return to menu[/]")

        _ = get_key()

        if self.incorrect:
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
                        _ = get_key()
                    self.current_index += 1
                    break

        self._show_results()
