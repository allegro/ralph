from django.core.validators import RegexValidator

class NoWhiteSpaceValidator(RegexValidator):
    def __init__(self):
        super().__init__(
            regex='\\s',
            inverse_match=True,
            message="Value cannot contain any whitespaces"
        )
