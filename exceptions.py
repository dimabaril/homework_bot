class SendMessageError(Exception):
    """Send Message Error."""

    def __init__(self, message="Send Message Error."):
        self.message = message
        super().__init__(self.message)
