from partner import Partner

class Client(Partner):
    def __init__(self, name, cif, direccio, cp, phone, email):
        self.name = name
        self.cif = cif
        self.direccio = direccio
        self.cp = cp
        self.phone = phone
        self.email = email