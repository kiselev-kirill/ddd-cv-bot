from pathlib import Path

from src.config import BASE_DIR

DATA_PATH = Path(BASE_DIR / "data" )


def load_stack() -> str:
    stack_file_path = Path(DATA_PATH / "stack.md")
    with open(stack_file_path, mode="r") as file:
        return file.read()


def load_about_me() -> str:
    stack_file_path = Path(DATA_PATH / "about_me.md")
    with open(stack_file_path, mode="r") as file:
        return file.read()


def load_resume() -> str:
    stack_file_path = Path(DATA_PATH / "cv.md")
    with open(stack_file_path, mode="r") as file:
        return file.read()
