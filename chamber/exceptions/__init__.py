class PersistenceException(Exception):

    def __init__(self, message=None):
        super().__init__()
        self.message = message

    def __str__(self):
        return repr(self.message)
