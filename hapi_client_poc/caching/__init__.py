
class CachedRequest:
    def __init__(self, function):
        self.cache = {}
        self.function = function

    def __call__(self, *args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        if key in self.cache:
            return self.cache[key]
        else:
            result = self.function(*args, **kwargs)
            if result is not None:
                self.cache[key] = result
            return result

    def cache_clear(self):
        self.cache.clear()
