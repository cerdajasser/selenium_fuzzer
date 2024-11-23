class SeleniumFuzzerException(Exception):
    """Base exception class for the selenium fuzzer."""
    pass

class ElementNotInteractableError(SeleniumFuzzerException):
    """Exception raised when an element is not interactable."""
    pass

class ElementNotFoundError(SeleniumFuzzerException):
    """Exception raised when an element is not found."""
    pass
