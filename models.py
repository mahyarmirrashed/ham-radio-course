from dataclasses import dataclass


@dataclass
class Question:
    id: str
    question: str
    answer: str
    distractor_1: str
    distractor_2: str
    distractor_3: str

    def choices(self) -> list[str]:
        """Return all answer choices in an unshuffled list."""
        return [self.answer, self.distractor_1, self.distractor_2, self.distractor_3]


@dataclass
class Category:
    title: str
    questions: list[Question]


@dataclass
class IncorrectAnswer:
    question: Question
    answer: str
    correct_answer: str
