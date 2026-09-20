import os
from enum import Enum
from uuid import uuid4


class GhaMessageLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


def _escape_data(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_property(value: str) -> str:
    return _escape_data(value).replace(":", "%3A").replace(",", "%2C")


def gha_message(message: str, level: GhaMessageLevel = GhaMessageLevel.INFO) -> None:
    commands = {
        GhaMessageLevel.DEBUG: "debug",
        GhaMessageLevel.WARNING: "warning",
        GhaMessageLevel.ERROR: "error",
    }
    command = commands.get(level)
    if command:
        print(f"::{command}::{_escape_data(message)}")
    else:
        print(message)


def gha_warning(message: str) -> None:
    gha_message(message, GhaMessageLevel.WARNING)


def gha_error(message: str) -> None:
    gha_message(message, GhaMessageLevel.ERROR)


def gha_debug(message: str) -> None:
    gha_message(message, GhaMessageLevel.DEBUG)


def gha_print(message: str) -> None:
    gha_message(message, GhaMessageLevel.INFO)


def gha_set_output(name: str, value: str | int | list[str]) -> None:
    if not name or any(character in name for character in "\r\n=<"):
        raise ValueError("Invalid GitHub Actions output name")

    value = str(value)
    delimiter = f"ghadelimiter_{uuid4()}"
    if delimiter in name or delimiter in value:
        raise ValueError("Output contains the GitHub Actions delimiter")

    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8", newline="") as output:
        output.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")


def gha_notice(file: str, line: int, end_line: int, title: str, message: str) -> None:
    print(f"::notice file={_escape_property(file)},line={line},endLine={end_line},"
          f"title={_escape_property(title)}::{_escape_data(message)}")


def gha_write_summary_line(markdown_line: str, append: bool = True) -> None:
    gha_write_to_summary(markdown_line, append)


def gha_write_to_summary(markdown: str, append: bool = True) -> None:
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a" if append else "w",
              encoding="utf-8", newline="") as summary:
        summary.write(markdown + "\n")
