class RestorableDict:
    def __init__(self, dict):
        self.dict = dict
        self.original = {}

    def __setitem__(self, key, value):
        if key not in self.original:
            self.original[key] = self.dict[key]
        self.dict[key] = value

    def __delitem__(self, key):
        self.original[key] = self.dict.pop(key)

    def copy(self):
        return self.dict.copy()

    def restore(self):
        self.dict.update(self.original)
        self.original.clear()

