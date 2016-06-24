import logging

logger = logging.getLogger(__name__)


class WithSignalDisabled(object):
    """
    Context manager for disabling particular signal in it's scope.
    """
    def __init__(self, signal, receiver, sender, dispatch_uid=None):
        self.signal = signal
        self.receiver = receiver
        self.sender = sender
        self.dispatch_uid = dispatch_uid

    def __enter__(self):
        logger.warning('Disabling signal {}'.format(self.dispatch_uid))
        self.signal.disconnect(
            receiver=self.receiver,
            sender=self.sender,
            dispatch_uid=self.dispatch_uid,
        )

    def __exit__(self, type, value, traceback):
        logger.warning('Enabling signal {}'.format(self.dispatch_uid))
        self.signal.connect(
            receiver=self.receiver,
            sender=self.sender,
            dispatch_uid=self.dispatch_uid,
        )
