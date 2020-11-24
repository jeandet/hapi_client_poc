"""
This has to be implemented.

Many strategies are possible here, could split requests along parameters or time.
A global process pool could be created for each client process.
Maybe this needs to limit concurrent requests on the same server?
"""


class SplitDataRequest:
    def __init__(self, function):
        self.function = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)
