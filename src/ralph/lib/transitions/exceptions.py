# -*- coding: utf-8 -*-


class TransitionError(Exception):
    pass


class TransitionNotAllowedError(TransitionError):
    def __init__(self, message, errors):
        super().__init__(message)
        self.message = message
        self.errors = errors


class TransitionModelNotFoundError(TransitionError):
    pass
