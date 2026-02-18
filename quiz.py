import json
import random
import sys
import termios
import tty
from pathlib import Path
from time import sleep

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def select_level(console):
    """Display level selection screen and return the chosen filepath via a single keypress."""
    files = {
        "1": Path("data/amateur_basic_question.json"),
        "2": Path("data/amateur_advanced_question.json"),
    }

    while True:
        console.clear()
        console.print(
            Panel(
                "[bold gold1]Canadian Amateur Radio Quiz[/]",
                box=box.DOUBLE,
                style="blue",
            )
        )
        console.print()

        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Level", style="green")
        table.add_row("1", "Basic")
        table.add_row("2", "Advanced")

        console.print(table)
        console.print()
        console.print("[cyan]Press 1 or 2 to select a level:[/]")

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

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
    def __init__(self, filepath):
        """
        Initialize Quiz with questions from a JSON file.

        Args:
            filepath: Path to JSON file containing questions
        """
        self.console = Console()
        self.categories = {}
        self.questions = []
        self.questions_answered_incorrectly = []
        self.current_index = 0
        self.score = 0
        self.current_choices = []
        self.limit_questions = True  # False when SHIFT+number is used (all questions)

        # Load and organize questions from JSON file
        self._load(filepath)

    def _load(self, filepath):
        """Load questions from JSON file and organize by category"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        for code, content in data.items():
            title = content["title"]
            questions = content["questions"]

            if title not in self.categories:
                self.categories[title] = []
            self.categories[title].extend(questions)

    def get_key(self):
        """Get single keypress from user"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key

    def show_menu(self):
        """Display category selection menu"""
        self.console.clear()

        # Title
        self.console.print(
            Panel(
                "[bold gold1]Canadian Amateur Radio Quiz[/]",
                box=box.DOUBLE,
                style="blue",
            )
        )
        self.console.print()

        # Category table
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Questions", justify="right", style="yellow")

        # Add "All Categories" option
        total_qs = sum(len(qs) for qs in self.categories.values())
        table.add_row("0", "All Categories", str(total_qs))

        # Add individual categories
        sorted_cats = sorted(self.categories.items())
        for idx, (cat_name, qs) in enumerate(sorted_cats, 1):
            table.add_row(str(idx), cat_name, str(len(qs)))

        self.console.print(table)
        self.console.print()
        self.console.print("[cyan]Press category number to start (SHIFT+number for all questions), or 'q' to quit[/]")

        return sorted_cats

    def select_category(self, sorted_cats):
        """Handle category selection"""
        # Mapping of shifted digit symbols to their base digit index
        # SHIFT+1=!, SHIFT+2=@, ..., SHIFT+9=(, SHIFT+0=)
        shifted_digit_map = {
            "!": 1, "@": 2, "#": 3, "$": 4, "%": 5,
            "^": 6, "&": 7, "*": 8, "(": 9, ")": 0,
        }

        while True:
            key = self.get_key()

            if key == "q":
                return None

            if key.isdigit():
                idx = int(key)
                self.limit_questions = True

                # All categories
                if idx == 0:
                    self.questions = []
                    for qs in self.categories.values():
                        self.questions.extend(qs)
                    return "All Categories"

                # Specific category
                elif 1 <= idx <= len(sorted_cats):
                    cat_name = sorted_cats[idx - 1][0]
                    self.questions = self.categories[cat_name].copy()
                    return cat_name

            elif key in shifted_digit_map:
                idx = shifted_digit_map[key]
                self.limit_questions = False

                # All categories (SHIFT+0)
                if idx == 0:
                    self.questions = []
                    for qs in self.categories.values():
                        self.questions.extend(qs)
                    return "All Categories"

                # Specific category (SHIFT+1 through SHIFT+9)
                elif 1 <= idx <= len(sorted_cats):
                    cat_name = sorted_cats[idx - 1][0]
                    self.questions = self.categories[cat_name].copy()
                    return cat_name

    def prepare_quiz(self):
        """Shuffle and limit questions"""
        random.shuffle(self.questions)
        if self.limit_questions:
            self.questions = self.questions[:20]
        self.current_index = 0
        self.score = 0
        self.questions_answered_incorrectly = []

    def show_question(self):
        """Display current question"""
        self.console.clear()

        q = self.questions[self.current_index]

        # Header
        self.console.print(
            Panel(
                f"[bold]Question {self.current_index + 1} of {len(self.questions)}[/]",
                style="blue",
            )
        )
        self.console.print()

        # Question text
        self.console.print(
            Panel(
                f"[bold white]{q['id']}: {q['question']}[/]",
                box=box.ROUNDED,
                border_style="cyan",
                padding=(1, 2),
            )
        )
        self.console.print()

        # Prepare shuffled choices
        choices = [q["answer"], q["distractor_1"], q["distractor_2"], q["distractor_3"]]
        random.shuffle(choices)
        self.current_choices = choices

        # Display choices
        for i, choice in enumerate(choices, 1):
            self.console.print(f"  [bold cyan]{i}.[/] {choice}")

        self.console.print()
        self.console.print("[dim]Press 1-4 to answer, 'q' to quit[/]")

    def check_answer(self, choice_num):
        """Check if answer is correct and show feedback"""
        q = self.questions[self.current_index]
        selected = self.current_choices[choice_num - 1]
        correct = q["answer"]

        self.console.print()

        if selected == correct:
            self.score += 1
            self.console.print(Panel("[bold green]✓ Correct![/]", border_style="green"))
        else:
            # Track incorrect answer
            self.questions_answered_incorrectly.append(
                {"question": q, "your_answer": selected, "correct_answer": correct}
            )
            self.console.print(
                Panel(
                    f"[bold red]✗ Wrong![/]\n\nCorrect answer: [yellow]{correct}[/]",
                    border_style="red",
                )
            )

        sleep(2)

    def show_incorrect_questions(self):
        """Display all incorrectly answered questions"""
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
            your_answer = item["your_answer"]
            correct_answer = item["correct_answer"]

            # Question header
            self.console.print(
                f"[bold yellow]Question {idx}:[/] [cyan]{q['id']}[/]",
            )
            self.console.print(f"[white]{q['question']}[/]")
            self.console.print()

            # Answers
            self.console.print(f"  [bold red]Your answer:[/] {your_answer}")
            self.console.print(f"  [bold green]Correct answer:[/] {correct_answer}")
            self.console.print()
            self.console.print("[dim]" + "─" * 80 + "[/dim]")
            self.console.print()

        self.console.print("[cyan]Press any key to continue[/]")
        self.get_key()

    def show_results(self):
        """Display final score"""
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

        # Show incorrect questions if any
        if self.questions_answered_incorrectly:
            self.console.print("[cyan]Press any key to review incorrect answers[/]")
        else:
            self.console.print("[cyan]Press any key to return to menu[/]")

        self.get_key()

        # Display incorrect questions review
        if self.questions_answered_incorrectly:
            self.show_incorrect_questions()

    def run_quiz(self, category_name):
        """Main quiz loop"""
        self.prepare_quiz()

        while self.current_index < len(self.questions):
            self.show_question()

            while True:
                key = self.get_key()

                if key == "q":
                    return False

                if key in ["1", "2", "3", "4"]:
                    self.check_answer(int(key))
                    self.current_index += 1
                    break

        self.show_results()
        return True

    def run(self):
        """Main application loop"""
        while True:
            sorted_cats = self.show_menu()
            category = self.select_category(sorted_cats)

            if category is None:
                break

            if not self.run_quiz(category):
                continue

        self.console.clear()
        self.console.print("[green]Thanks for using the quiz app![/]")
