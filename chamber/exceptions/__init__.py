class PersistenceException(Exception):

    def __init__(self, message=None, error_dict=None):
        super().__init__()
        self.message = message
        self.error_dict = error_dict

    def __str__(self):
        return repr(self.message)
