PRODUCT_TYPES = ['BAR', 'RESTAURANT']

class Product:
    def __init__(self, name, price, category=None, iva=None):
        self.name = str(name)
        self.price = float(price)
        if category:
            self.category = category
        if iva:
            self.iva = iva

    def __repr__(self):
        return '{0} {1}'.format(self.name, self.price)


class Menjar(Product):
    pass


class Beguda(Product):
    pass
