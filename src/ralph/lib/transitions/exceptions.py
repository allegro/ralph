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


class RescheduleAsyncTransitionActionLater(Exception):
    pass


class FreezeAsyncTransition(Exception):
    pass


class AsyncTransitionError(TransitionError):
    pass


class MoreThanOneStartedActionError(AsyncTransitionError):
    pass


class FailedActionError(AsyncTransitionError):
    pass
