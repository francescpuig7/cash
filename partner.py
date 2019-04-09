
class Partner:
    def __init__(self, name, cif, direccio=None):
        self.name = name
        self.cif = cif
        self.direccio = direccio

    def __repr__(self):
        return '{} {}'.format(self.name, self.cif)

    def __lt__(self, other):
        return self.cif > other.cif

    def __eq__(self, other):
        return self.cif == other.cif
