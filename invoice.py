import os
from subprocess import Popen
from platform import system
from datetime import datetime
from InvoiceGenerator.api import Invoice, Item, Client, Provider, Creator, Address
from InvoiceGenerator.pdf import SimpleInvoice

class Invoicing(object):
    def __init__(self):
        pass

    def invoicing(self, c, lines, iva=21, invoice_num=None):
        if not invoice_num:
            invoice_num = "F000001"
        else:
            invoice_num = 'F{}'.format(str(invoice_num).zfill(6))
        # choose catalan language
        os.environ["INVOICE_LANG"] = "ca"

        client = Client(
            c.name, address=c.direccio, zip_code=c.cp, phone=c.phone, email=c.email, vat_id=c.cif,
        )
        provider = Provider(
            'Can Guix Bar Restaurant', zip_code="17800", address="Carrer Mulleras, 3", city="Olot, Girona",
            email="canguix@gmail.com", phone="+34 972 26 10 40", vat_id='E17087289',
            logo_filename="/Users/puig/Documents/codi/cash/cash/icons/logo_factura.jpg"
        )

        creator = Creator('Can Guix')

        invoice = Invoice(client, provider, creator)
        os.environ["INVOICE_LANG"] = "ca"
        invoice.currency_locale = 'ca_ES.UTF-8'
        invoice.currency = '€'
        invoice.number = invoice_num
        invoice.use_tax = True
        invoice.date = datetime.now()
        for line_product in lines:
            price_without_iva = self.extract_iva(line_product.price, iva)
            invoice.add_item(
                Item(
                    count=line_product.quant, price=float(price_without_iva), description=line_product.name, tax=iva
                )
            )

        pdf_path = "/Users/puig/Desktop/test_invoice.pdf"
        pdf = SimpleInvoice(invoice)
        pdf.gen(pdf_path, generate_qr_code=False)

        return pdf_path

    def open_invoice(self, filename):
        try:
            os_name = system().lower()
            if os_name == 'windows':
                starter = 'start'
            elif os_name == 'linux':
                starter = 'xdg-open'
            elif os_name == 'darwin':
                starter = 'open'
            start = ' '.join([starter, filename])
            Popen(start, shell=True)
        except Exception as err:
            print(err)
            pass

    @staticmethod
    def extract_iva(total, iva):
        substract = float(total) / (1 + (float(iva) / 100.0))
        return substract
