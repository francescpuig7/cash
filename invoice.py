import os
import configparser
from subprocess import Popen
from platform import system
from datetime import datetime
from InvoiceGenerator.api import Invoice, Item, Client, Provider, Creator, Address
from InvoiceGenerator.pdf import SimpleInvoice

ICONS = os.path.join('.', 'icons')


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
        name, cp, address, city, email, phone = self.get_config_file_info()

        provider = Provider(
            name, zip_code=cp, address=address, city=city, email=email, phone=phone, vat_id='E17087289',
            logo_filename=ICONS + '/logo_factura.jpg'
        )

        creator = Creator(name)

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

    @staticmethod
    def open_invoice(filename):
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

    @staticmethod
    def get_config_file_info():
        parser = configparser.ConfigParser()
        base_path = './configs/'
        parser.read(base_path + '/config.cfg')
        name = parser.get('P_NAME', 'p_name')
        cp = parser.get('P_CP', 'p_cp')
        address = parser.get('P_ADDRESS', 'p_address')
        city = parser.get('P_CITY', 'p_city')
        email = parser.get('P_EMAIL', 'p_email')
        phone = parser.get('P_PHONE', 'p_phone')

        return name, cp, address, city, email, phone
