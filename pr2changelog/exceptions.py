class BaseError(Exception):
    pass


class MissingCategory(BaseError):
    def __init__(self, change):
        super(MissingCategory, self).__init__(
            f"Found a change without category and config is set to require them! \n{change}")
    pass


class InvalidCategory(BaseError):
    def __init__(self, got: str, valid_options: list):
        super(InvalidCategory, self).__init__(
            f"Found invalid category: {got}. "
            f"Only these categories are valid {[c for c in valid_options]}"
        )


class ChangeLogFileNotFound(BaseError):
    def __init__(self, filename: str):
        super(ChangeLogFileNotFound, self).__init__(
            f"{filename} couldn't be found and the configuration is set to don't create the changelog file if it "
            f"isn't found "
        )


class MissingContextInformation(BaseError):
    def __init__(self, info: str):
        super(MissingContextInformation, self).__init__(
            f"We're missing critical information from the context: {info}"
        )
