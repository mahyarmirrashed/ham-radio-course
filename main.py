#!/usr/bin/env python3
"""
Scrape one Canadian Basic amateur radio study question + submit to reveal correct answer.
"""

import requests
from bs4 import BeautifulSoup
import json

# Form data for this specific case (B-001-001-001)
FORM_DATA = {
    "p_answer": "A",
    "p_question_code": "1234",
    "p_question_type": "2",
    "p_question_cat": "1",
    "p_question_sub": "1",
    "p_question_no": "1",
    "Z_ACTION": "Submit",
}


def scrape_question_and_answer():
    """POST to form_validate, parse result page for complete question data."""

    url = (
        "https://apc-cap.ic.gc.ca/pls/apc_anon/apeg_study.study_questions_form_validate"
    )

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    session = requests.Session()

    # Submit the form
    response = session.post(url, data=FORM_DATA, headers=headers)
    response.raise_for_status()

    # Parse result page
    soup = BeautifulSoup(response.text, "html.parser")
    form = soup.find("form", {"action": "apeg_study.study_questions_result_validat"})

    if not form:
        raise ValueError("Could not find result form in response")

    # Extract question ID
    caption = form.find("caption")
    question_id = caption.get_text(strip=True).replace("Study Question ID: ", "")

    # Extract question text
    question_elem = form.find("b")
    question_text = question_elem.get_text(strip=True) if question_elem else ""

    # Extract choices and detect correct answer
    choices = {}
    correct_letter = None

    # Parse confirmation message first (most reliable)
    confirmation_div = soup.find("div", class_="ic_success")
    if confirmation_div:
        confirmation_text = confirmation_div.get_text(strip=True)
        if "Answer '" in confirmation_text and "' is correct!" in confirmation_text:
            correct_letter = confirmation_text.split("'")[1]

    # Parse radio choices (backup + full text)
    for div in form.find_all("div", recursive=True):
        input_tag = div.find("input", {"name": "p_answer"})
        if input_tag:
            letter = input_tag["value"]
            label = div.find("label")
            if label:
                choice_text = label.get_text(strip=True)
                # Clean up: remove leading letter and spacing
                if ") " in choice_text:
                    choice_text = choice_text.split(") ", 1)[1].strip()
                choices[letter] = choice_text

                # Detect correct via styling/attributes (backup)
                if (
                    not correct_letter
                    and "ic_success" in div.get("class", [])
                    and input_tag.has_attr("checked")
                ):
                    correct_letter = letter

    # Build final object
    question_obj = {
        "id": question_id,
        "question": question_text,
        "choices": choices,
        "correct": correct_letter,
    }

    return question_obj


if __name__ == "__main__":
    try:
        result = scrape_question_and_answer()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")
        print(
            "Response preview:",
            requests.get(
                "https://apc-cap.ic.gc.ca/pls/apc_anon/apeg_study.study_questions_intro_validate"
            ).text[:500],
        )
