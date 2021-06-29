class Markdown:
    @staticmethod
    def title(text: str, hierarchy=1):
        return f"{'#' * hierarchy} {text}\n"

    @staticmethod
    def bold(text: str):
        return f"**{text}**"

    @staticmethod
    def italit(text: str):
        return f"*{text}*"

    @staticmethod
    def ordered_list(text_list: list):
        if Markdown.is_invalid_text_list(text_list):
            raise ValueError("Was expecting list of strings, got something else")

        final_text = str()

        for index, txt in enumerate(text_list):
            final_text += f"{index + 1} {txt}\n"

        return final_text

    @staticmethod
    def unordered_list(text_list: list):
        if Markdown.is_invalid_text_list(text_list):
            raise ValueError("Was expecting list of strings, got something else")

        final_text = str()

        for idx, txt in enumerate(text_list):
            final_text += f"* {txt}\n"

        return final_text

    @staticmethod
    def inline_code(text: str):
        return f"`{text}`"

    @staticmethod
    def link(title: str, url: str):
        return f"[{title}]({url})"

    @staticmethod
    def is_invalid_text_list(text_list: list) -> bool:
        invalids = [not isinstance(i, str) for i in text_list]

        return any(invalids)