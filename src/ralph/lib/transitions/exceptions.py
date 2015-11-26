# -*- coding: utf-8 -*-


class TransitionNotAllowedError(Exception):
    def init(self, message, errors):
        super().__init__(message)
        self.errors = errors


class TransitionModelNotFoundError(Exception):
    pass
