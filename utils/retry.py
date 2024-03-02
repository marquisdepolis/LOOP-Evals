import time
from functools import wraps

def retry_except(exceptions_to_catch=(Exception,), tries=4, delay=1):
    """
    Retry decorator with customizable parameters.

    Args:
        exceptions_to_catch: A tuple of exceptions to catch and retry on.
                             Defaults to catching all Exceptions.
        tries: The maximum number of attempts.
        delay: The delay in seconds between retries.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, tries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions_to_catch as e:
                    print(f"Exception caught: {e}. Retrying in {delay} seconds (attempt {attempt}/{tries})")
                    time.sleep(delay)
            else:  # No exception in the final attempt
                return func(*args, **kwargs) 

        return wrapper
    return decorator
