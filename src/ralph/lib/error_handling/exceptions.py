class WrappedOperationalError(RuntimeError):
    def __init__(self, query, model, error_str):
        self.query = query
        self.model = model
        self.original_error_str = error_str
