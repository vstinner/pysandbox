class RestorableDict:
    def __init__(self, dict):
        self.dict = dict
        self.original = {}
        self.delete = set()
        self.dict_update = dict.update

    def __setitem__(self, key, value):
        if (key not in self.original) and (key not in self.delete):
            if key in self.dict:
                self.original[key] = self.dict[key]
            else:
                self.delete.add(key)
        self.dict[key] = value

    def __delitem__(self, key):
        self.original[key] = self.dict.pop(key)

    def copy(self):
        return self.dict.copy()

    def restore(self):
        for key in self.delete:
            del self.dict[key]
        self.dict_update(self.original)
        self.original.clear()

