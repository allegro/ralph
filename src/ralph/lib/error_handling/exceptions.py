class WrappedOperationalError(RuntimeError):
    def __init__(self, query, model):
        self.query = query
        self.model = model
