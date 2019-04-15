
class Partner:
    def __init__(self, name, cif, group=None, direccio=None):
        self.name = name
        self.cif = cif
        self.direccio = direccio
        self.group = group

    def __repr__(self):
        return '{} {}'.format(self.name, self.cif)

    def __lt__(self, other):
        return self.name < other.name

    def __eq__(self, other):
        return self.name == other.name
