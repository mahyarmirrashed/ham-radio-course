# HAM Radio Course

A simple terminal-based quiz app for studying Canadian Amateur Radio exam questions.

## Usage

### 1. Download Questions

First, download the latest official question banks:

```sh
python main.py update
```

This downloads and processes both Basic and Advanced question sets into `data/` directory.

### 2. Run Quiz

Start the interactive quiz:

```sh
python main.py quiz
```

You'll be prompted to select Basic (1) or Advanced (2) level, then you can:

- Choose from different question categories or practice all questions
- Answer 20 random questions per session
- Get immediate feedback on your answers
- See your final score

## Controls

- **Number keys (0-9)**: Select menu options
- **1-4**: Select answer choices
- **q**: Quit or return to menu

## Data Source

Questions are sourced from the official Canadian Amateur Radio question banks:

- Basic: https://apc-cap.ic.gc.ca/datafiles/amat_basic_quest.zip
- Advanced: https://apc-cap.ic.gc.ca/datafiles/amat_adv_quest.zip
