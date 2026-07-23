"""QLineEdit subclass with visual validation feedback styling."""

from PySide6.QtWidgets import QLineEdit


class ValidatedLineEdit(QLineEdit):
    """QLineEdit with visual validation feedback.

    Applies a red border and error message tooltip when marked invalid.
    """

    def __init__(self, contents: str = "", parent=None):
        super().__init__(contents, parent)
        self._is_valid: bool = True
        self._error_message: str = ""

    def set_valid(self, is_valid: bool, message: str = "") -> None:
        """Set validation state and update styling and tooltip."""
        self._is_valid = is_valid
        self._error_message = message
        self.setProperty("invalid", not is_valid)
        self.setToolTip(message if not is_valid else "")
        # Force QSS restyle
        self.style().unpolish(self)
        self.style().polish(self)

    def is_valid(self) -> bool:
        """Return current validation state."""
        return self._is_valid

    def error_message(self) -> str:
        """Return current validation error message."""
        return self._error_message
