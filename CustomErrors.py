class GetApiAnswerError(Exception):
    """Обработка ошибок."""

    def __init__(self, *args):
        """Конструктор класса."""
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        """Метод."""
        if self.message:
            return 'GetApiAnswerError, {0} '.format(self.message)
        return 'GetApiAnswerError has been raised'


class SendMessageError(Exception):
    """Обработка ошибок."""

    def __init__(self, *args):
        """Конструктор класса."""
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        """Метод."""
        if self.message:
            return 'SendMessageError, {0} '.format(self.message)
        return 'SendMessageError has been raised'
