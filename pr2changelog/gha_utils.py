import os
from enum import Enum


class GhaMessageLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3


def gha_message(message: any, level: int = GhaMessageLevel.INFO):
    print(message)

    match level:
        case GhaMessageLevel.DEBUG:
            level_command = "::debug::"
        case GhaMessageLevel.INFO:
            level_command = ""
        case GhaMessageLevel.WARNING:
            level_command = "::warning::"
        case GhaMessageLevel.ERROR:
            level_command = "::error::"
        case _:
            level_command = ""

    os.system(f'echo "{level_command}{str(message)}"')


def gha_warning(message: any):
    gha_message(message, GhaMessageLevel.WARNING)


def gha_error(message: any):
    gha_message(message, GhaMessageLevel.ERROR)


def gha_debug(message: any):
    gha_message(message, GhaMessageLevel.DEBUG)


def gha_print(message: any):
    gha_message(message, GhaMessageLevel.INFO)


def gha_set_output(name: str, value: any):
    os.system(f'echo "::set-output name={name}::{str(value)}"')


def gha_notice(file: str, line: int, end_line: int, title: str, message: any):
    os.system(f'echo "::notice file={file},line={line},endLine={end_line},title={title}::{message}"')


def gha_write_summary_line(markdown_line: str, append: bool = True):
    os.system(f'echo "{markdown_line}" >{">" if append else ""} $GITHUB_STEP_SUMMARY')


def gha_write_to_summary(markdown: str, append: bool = True):
    all_lines = markdown.splitlines()
    for line in all_lines:
        gha_write_summary_line(line, append)
