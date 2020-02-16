# -*- coding: utf-8 -*-
import sys
import os
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from PyQt5 import uic, QtGui
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QDialog, QPushButton, QTableWidgetItem, QMessageBox,
                             QLabel, QHBoxLayout, QTextEdit, QWidget, QVBoxLayout, QLineEdit, QFormLayout, QInputDialog,
                             QGridLayout, QDialogButtonBox, QDateEdit)
from product import Product, Menjar, Beguda
from employee import Employee
from utils import Utils
from partner import Partner
from client import Client
from invoice import Invoicing
# from order import Table
import csv
import configparser
from subprocess import Popen
from platform import system
import logging

TEMPLATES = os.path.join('.', 'templates')

#TEMPLATES = os.path.join(
#    os.path.dirname(os.path.realpath(__file__)), 'templates'
#)


class Login(QDialog):
    def __init__(self):
        super(Login, self).__init__()
        uic.loadUi(TEMPLATES + '/login.ui', self)
        self.buttonBox.accepted.connect(self.accept)
        self.show()

    def login(self):
        self.show()

    def accept(self):
        if self.user_label.text() == 'admin' and self.password_label.text() == 'admin':
            return True
        return False


class Config(QDialog):
    def __init__(self, parent, db, messaging, partners, employee):
        super(Config, self).__init__(parent)
        uic.loadUi(TEMPLATES + '/config.ui', self)
        self.db = db
        self.messaging = messaging
        self.partners = partners
        self._employees = list()

        emp_aux = self.db.select_employees()
        for employee in emp_aux:
            emp = Employee(employee[0], employee[1])
            self._employees.append(emp)

        for employee in self._employees:
            self.comboBox_selectEmployee.addItem(employee.name)
        self.comboBox_selectEmployee.currentIndexChanged['QString'].connect(self.change_default_employee)
        #self.save_product_button.clicked.connect(self.save_product)
        self.save_partner_button.clicked.connect(self.save_partner)

    def change_default_employee(self, sign):
        print(sign)

    def save_product(self):
        try:
            if self.price.text() and self.name.text():
                price = float(self.price.text())
                category = str(self.checkbox_categoria.currentText())
                with open('products.csv', 'a') as file:
                    file.write('{0},{1},{2}\n'.format(self.name.text(), price, category))
                    file.close()
                self.messaging.show('Producte entrat')
                # Reset texts
                self.price.setText('')
                self.name.setText('')
        except Exception as err:
            self.messaging.show('Producte no entrat', 'warning')

    def save_partner(self):
        if self.label_partner_name.text() and self.label_partner_cif.text():
            try:
                partner_name = self.label_partner_name.text()
                partner_cif = self.label_partner_cif.text()
                partner_address = self.label_partner_address.text()
                p = Partner(name=partner_name, cif=partner_cif, direccio=partner_address)
                self.db.insert_partner(p.cif, p.name)
                self.partners.append(p)
                self.messaging.show('Proveidor entrat')
                # Reset texts
                self.label_partner_name.setText('')
                self.label_partner_cif.setText('')
                self.label_partner_address.setText('')
            except ValueError:
                self.messaging.show('Proveidor no entrat', 'warning')

    def paint(self):
        self.show()


class Payments(QDialog):

    GROUPS = {
        1: "COMPRES",
        2: "ADQUISICIONS INTRACOM.",
        3: "BENS D'INVERSIÓ",
        4: "SOUS I SALARIS",
        5: "SEG. SOCIAL",
        6: "AUTONOMS",
        7: "TREBALLS ALTRE EMPRESES",
        8: "PRIMES ASSEGURANCES",
        9: "TRIBUTS I TAXES",
        10: "ALTRES DESPESES",
        11: "REPARACIONS/MANTENIMENT",
        12: "AMORTITZACIONS",
        13: "SUBMINISTRAMENTS",
        14: "SERVEIS PROFESSIONALS",
        15: "ALTRES SERVEIS"
    }

    def __init__(self, partners, messaging, db):
        super(Payments, self).__init__()
        uic.loadUi(TEMPLATES + '/invoice.ui', self)
        self.partners = partners
        self.messaging = messaging
        self.db = db
        self.date = datetime.now()
        self.buttonBox.accepted.connect(self.save_payment)
        self.buttonBox.rejected.connect(self.reject)
        self.calendar.clicked[QDate].connect(self.set_date)
        """for partner in sorted(self.partners):
            self.combobox_partner.addItem(str(partner))"""
        for group in self.GROUPS.values():
            self.combobox_group.addItem(group)
        self.label_iva_exempt.stateChanged.connect(self.activate_desactivate_ivas)

    def paint(self):
        for partner in sorted(self.partners):
            self.combobox_partner.addItem(str(partner))
        self.show()
        self.date_calendar = None

    def activate_desactivate_ivas(self):
        if self.label_iva_exempt.isChecked():
            self.label_iva_4.setEnabled(False)
            self.label_iva_10.setEnabled(False)
            self.label_iva_21.setEnabled(False)
        else:
            self.label_iva_4.setEnabled(True)
            self.label_iva_10.setEnabled(True)
            self.label_iva_21.setEnabled(True)

    def save_payment(self):
        base4 = float(self.label_base_imposable4.text())
        base10 = float(self.label_base_imposable10.text())
        base21 = float(self.label_base_imposable21.text())
        if not self.label_iva_exempt.isChecked():
            iva_4 = float(self.label_iva_4.text())
            iva_10 = float(self.label_iva_10.text())
            iva_21 = float(self.label_iva_21.text())
        else:
            iva_4 = 0.0
            iva_10 = 0.0
            iva_21 = 0.0

        # todo: set default date
        total = float(self.label_total.text())
        partner_name = self.combobox_partner.currentText()
        group = self.combobox_group.currentText()
        number = self.label_invoice_number.text()
        if not self.date_calendar:
            self.date_calendar = self.date.strftime('%Y/%m/%d')
        if total == 0.0:
            self.messaging.show(message='No has entrat les dades correctament', type='warning')
            return False

        self.db.insert_payment(
            self.date_calendar, partner_name, group, number, base4, iva_4, base10, iva_10, base21, iva_21, total
        )
        message = 'Pagament entrat correctament: {} - {}, {}€'.format(partner_name, self.date, total)
        self.messaging.show(message)
        self.reset_values()

    def set_date(self, date):
        year, month, day = date.getDate()
        self.date_calendar = datetime(year, month, day).strftime('%Y/%m/%d')

    def reset_values(self):
        self.label_invoice_number.setText('')
        self.label_total.setValue(0.0)
        self.label_base_imposable.setValue(0.0)
        self.label_iva_4.setValue(0.0)
        self.label_iva_10.setValue(0.0)
        self.label_iva_21.setValue(0.0)
        self.label_iva_exempt.setChecked(False)
        self.combobox_partner.setCurrentIndex(1)
        self.combobox_group.setCurrentIndex(1)


class Listing(QDialog):

    def __init__(self, db, messaging, iva, listing_path, logger):
        super(Listing, self).__init__()
        uic.loadUi(TEMPLATES + '/listing.ui', self)
        self.db = db
        self.iva = iva
        self.listing_path = listing_path
        self.price = 0
        self.di = None
        self.df = None
        self.logger = logger

        self.btn_sells_monthly.clicked.connect(self.gen_report_monthly_sells)
        self.btn_sells_dates.clicked.connect(self.gen_report_dates_sells)
        self.btn_sells_price.clicked.connect(self.gen_report_price_sells)

        self.btn_payments_monthly.clicked.connect(self.gen_report_monthly_payments)
        self.btn_payments_dates.clicked.connect(self.gen_report_dates_payments)
        self.btn_payments_price.clicked.connect(self.gen_report_price_payments)

    @staticmethod
    def get_dates():
        _date = datetime.now() - relativedelta(months=1)
        month = _date.month
        year = _date.year
        last_day_of_month = calendar.monthrange(year, month)[1]
        di = '{}/{}/01'.format(year, str(month).zfill(2))
        df = '{}/{}/{}'.format(year, str(month).zfill(2), last_day_of_month)

        return di, df

    def gen_report_monthly_sells(self):
        try:
            di, df = self.get_dates()
            data = self.db.select_ticket('month', di=di, df=df)
            self.write_file(data, 'ingressos')
        except Exception as err:
            self.logger.error(str(err))

    def gen_report_monthly_payments(self):
        try:
            di, df = self.get_dates()
            data = self.db.select_payments_by_dates(di=di, df=df)
            self.write_file(data, 'gastos')
        except Exception as err:
            self.logger.error(str(err))

    def gen_report_dates_sells(self):
        try:
            self.show_dialog_dates()
            if self.di and self.df:
                data = self.db.select_ticket('month', di=self.di, df=self.df)
                self.di = None
                self.df = None
                self.write_file(data, 'ingressos')
        except Exception as err:
            self.logger.error(str(err))

    def gen_report_dates_payments(self):
        try:
            self.show_dialog_dates()
            if self.di and self.df:
                data = self.db.select_payments_by_dates(di=self.di, df=self.df)
                self.di = None
                self.df = None
                self.write_file(data, 'gastos')
        except Exception as err:
            self.logger.error(str(err))

    def gen_report_price_sells(self):
        try:
            self.price = 0
            self.show_dialog_price()
            data = self.db.select_sell_by_import(self.price)
            self.write_file(data, 'ingressos')
        except Exception as err:
            self.logger.error(str(err))

    def gen_report_price_payments(self):
        try:
            self.price = 0
            self.show_dialog_price()
            data = self.db.select_payments_by_import(self.price)
            self.write_file(data, 'gastos')
        except Exception as err:
            self.logger.error(str(err))

    def filename(self, _type):
        _file = '{}/{}_{}.csv'.format(self.listing_path, _type, datetime.now().strftime('%Y%m%d_%H_%M_%S'))
        return _file

    def write_file(self, data, _type):
        filename = self.filename(_type)
        if _type == 'ingressos':
            with open(filename, 'w') as f:
                f.write('CONCEPTE;DIA;% IVA;IVA;SUBTOTAL;TOTAL;\n')
                for row in data:
                    taula = row[1]
                    if 'Barra' in taula:
                        concepte = 'VARIS BARRA'
                    else:
                        concepte = 'VARIS TAULA'
                    subtotal = float(row[3]) / (1 + (self.iva / 100.0))
                    iva = float(row[3] - subtotal)
                    f.write('{};{};{};{};{};{};\n'.format(
                        concepte, row[0], self.iva,
                        ("%.2f" % iva).replace('.', ','),
                        ("%.2f" % subtotal).replace('.', ','),
                        ("%.2f" % row[3]).replace('.', ',')
                    ))
        elif _type == 'gastos':
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('CONCEPTE;DIA;PROVEIDOR;NUM FACTURA;GRUP;BASE IMPOSABLE;% IVA 4;% IVA 10;% IVA 21;TOTAL;\n')
                for row in data:
                    concepte = 'GASTO'
                    dia = row[0]
                    partner = row[1]
                    grup = row[2]
                    nfra = row[3]
                    base = row[4]
                    iva4 = row[5]
                    iva10 = row[6]
                    iva21 = row[7]
                    total = row[8]
                    f.write('{};{};{};{};{};{};{};{};{};{};\n'.format(
                        concepte, dia, partner, nfra, grup,
                        ("%.2f" % base).replace('.', ','),
                        ("%.2f" % iva4).replace('.', ','),
                        ("%.2f" % iva10).replace('.', ','),
                        ("%.2f" % iva21).replace('.', ','),
                        ("%.2f" % total).replace('.', ',')
                    ))
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

    def show_dialog_price(self):
        price, ok = QInputDialog.getText(self, 'Seleccionar', 'Entra el preu:')
        if ok:
            try:
                self.price = int(price)
            except ValueError:
                self.price = 0

    def show_dialog_dates(self):
        self.q_diag_dates = QDialog(self)
        self.q_diag_dates.resize(270, 113)

        gridLayout_2 = QGridLayout(self.q_diag_dates)
        gridLayout_2.setObjectName("gridLayout_2")
        gridLayout = QGridLayout()
        label_init_date = QLabel(self.q_diag_dates)
        label_init_date.setText("Data Inici")
        gridLayout.addWidget(label_init_date, 0, 0, 1, 1)
        self.init_date = QDateEdit(self.q_diag_dates)
        gridLayout.addWidget(self.init_date, 0, 1, 1, 1)
        label_end_date = QLabel(self.q_diag_dates)
        label_end_date.setText("Data Final")
        gridLayout.addWidget(label_end_date, 1, 0, 1, 1)
        self.end_date = QDateEdit(self.q_diag_dates)
        gridLayout.addWidget(self.end_date, 1, 1, 1, 1)
        gridLayout_2.addLayout(gridLayout, 0, 0, 1, 1)
        buttonBox = QDialogButtonBox(self.q_diag_dates)

        buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        gridLayout_2.addWidget(buttonBox, 1, 0, 1, 1)
        buttonBox.accepted.connect(self.accept_dates)
        buttonBox.rejected.connect(self.reject_dates)
        self.q_diag_dates.exec_()

    def accept_dates(self):
        self.di = '{year}/{month}/{day}'.format(
            year=str(self.init_date.date().year()),
            month=str(self.init_date.date().month()).zfill(2),
            day=str(self.init_date.date().day()).zfill(2)
        )
        self.df = '{year}/{month}/{day}'.format(
            year=str(self.end_date.date().year()),
            month=str(self.end_date.date().month()).zfill(2),
            day=str(self.end_date.date().day()).zfill(2)
        )
        self.q_diag_dates.close()

    def reject_dates(self):
        self.di = None
        self.df = None
        self.q_diag_dates.close()

    def paint(self):
        self.show()


class License(QDialog):
    def __init__(self, db, messaging):
        super(License, self).__init__()
        uic.loadUi(TEMPLATES + '/license.ui', self)
        self.db = db
        self.messaging = messaging
        self.buttonBox.accepted.connect(self.activate_license)
        self.buttonBox.rejected.connect(self.reject)

    def activate_license(self):
        code = self.license_box.text()
        u = Utils()
        if u.check_code(code):
            dt = (datetime.now() + relativedelta(years=1)).strftime('%Y/%m/%d')
            self.db.insert_license(code, dt)
            self.messaging.show('Llicencia activada')
        else:
            self.messaging.show('Llicencia no valida', type='warning')
            return False

    def paint(self):
        self.show()


class Sales(QDialog):
    def __init__(self, db):
        super(Sales, self).__init__()
        uic.loadUi(TEMPLATES + '/extracts.ui', self)
        self.db = db
        self.view = 'Dia'
        self.btn_delete.setVisible(False)
        self.comboBox_select_result.currentIndexChanged['QString'].connect(self.change_default_view)
        self.checkbox_editable.stateChanged.connect(self.activate_delete_button)
        self.btn_delete.clicked.connect(self.delete_item)

    def paint(self):
        if self.view == 'Dia':
            tickets = self.db.select_ticket('day', di=time.strftime('%Y/%m/%d'))
        elif self.view == 'Mes':
            month = datetime.now().month
            year = datetime.now().year
            last_day_of_month = calendar.monthrange(year, month)[1]
            di = '{}/{}/01'.format(year, str(month).zfill(2))
            df = '{}/{}/{}'.format(year, str(month).zfill(2), last_day_of_month)
            tickets = self.db.select_ticket('month', di=di, df=df)
        elif self.view == 'Any':
            tickets = self.db.select_ticket('year', di=time.strftime('%Y'))
        elif self.view == 'Total':
            tickets = self.db.select_ticket('total')
        elif self.view == 'Pagaments':
            tickets = self.db.select_payments_by_import(0)
        else:
            return False

        total = 0
        self.sales_view.setRowCount(0)
        for ticket in tickets:
            rowPosition = self.sales_view.rowCount()
            self.sales_view.insertRow(rowPosition)
            self.sales_view.setItem(rowPosition, 0, QTableWidgetItem(str(ticket[0])))
            self.sales_view.setItem(rowPosition, 1, QTableWidgetItem(str(ticket[1])))
            self.sales_view.setItem(rowPosition, 2, QTableWidgetItem(str(ticket[2])))
            if self.view == 'Pagaments':
                self.sales_view.setItem(rowPosition, 3, QTableWidgetItem(str(ticket[8])))
                total += ticket[8]
            else:
                self.sales_view.setItem(rowPosition, 3, QTableWidgetItem(str(ticket[3])))
                total += ticket[3]
        self.label_total.setText(str("%.2f" % total))
        self.show()
        # self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Set not editable

    def change_default_view(self, sign):
        self.view = str(sign)
        self.paint()

    def activate_delete_button(self):
        if self.checkbox_editable.isChecked():
            self.btn_delete.setVisible(True)
        else:
            self.btn_delete.setVisible(False)

    def delete_item(self):
        if self.sales_view.selectedItems():
            for _item in self.sales_view.selectedItems():
                _id = self.sales_view.item(_item.row(), 0).text()
                if self.view == 'Pagaments':
                    table = 'payments'
                    partner = self.sales_view.item(_item.row(), 1).text()
                    total = self.sales_view.item(_item.row(), 3).text()
                else:
                    table = 'ticket'
                self.sales_view.removeRow(_item.row())
                break
            if self.view == 'Pagaments':
                self.db.delete_payment(table, _id, partner, total)
            else:
                self.db.delete_ticket(table, _id)


class Foo(QDialog):
    def __init__(self, logger):
        super(Foo, self).__init__()
        self._products = list()
        self._employees = list()
        self._tables = list()
        self._ltables = list()
        self._lprod = list()
        self.tables = dict()
        self.products = dict()
        self.partners = list()
        self.clients = list()
        self.employee = 'No. def'
        self.table_num = 'Taula 0'
        self.suplement_concept = 'varis'
        self.main_view = 'restaurant.ui'
        self.logger = logger
        try:
            self.listing_path = str(os.environ['HOME'])
        except KeyError:
            self.listing_path = str(os.environ['USERPROFILE'])
        self.table_id = 1
        self.add_num = 1
        self.iva = 10
        self.messaging = Message()
        self._mydict = {'menu': 10, 'menucapsetmana': 25, 'vinegre': 2}
        self.db = Db()
        self.ticket_number = self.db.select_ticket_number()
        self.sales = Sales(self.db)
        #self.config = Config(self.db, self.messaging, self.employee)
        row = self.db.select_partner()
        for x in row:
            partner = Partner(name=x[1], cif=x[0])
            self.partners.append(partner)
        self.read_config_file()
        self.payments = Payments(self.partners, self.messaging, self.db)
        self.license = License(self.db, self.messaging)
        self.listing = Listing(self.db, self.messaging, self.iva, self.listing_path, self.logger)
        self.initUi()

    def initUi(self):
        self.ui = uic.loadUi(TEMPLATES + '/' + self.main_view, self)
        self.set_main_title()

        # connect buttons
        self.btn_facturar.clicked.connect(self.invoicing)
        self.btn_obrir_taula.clicked.connect(self.show_dialog_table)
        self.btn_borrar.clicked.connect(self.delete_item)
        self.btn_llistats.clicked.connect(self.listing.paint)
        self.btn_ventas.clicked.connect(self.sales.paint)
        self.btn_config.clicked.connect(self.open_configs)
        self.btn_llicencia.clicked.connect(self.license.paint)
        self.btn_payments.clicked.connect(self.payments.paint)
        self.btn_cancel_ticket.clicked.connect(self.cancel_ticket)
        self.btn_factura.clicked.connect(self.gen_invoice)
        #self.btn_config.clicked.connect(self.config.login)
        #self.btn_config.clicked.connect(self.config)

        self.connect_buttons_calc()
        date = time.strftime('%d/%m/%y')
        self.label_table.setText('Taula 1')
        self.label_time.setText('{0}: {1}'.format(self.label_time.text(), date))
        self.label_ticket_number.setText('{0}: {1}'.format(self.label_ticket_number.text(), self.ticket_number))
        self.order_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.db.select_ticket_number()
        #self.btn.clicked.connect(self.paint)
        _tables = self.db.select_table()

        for table in _tables:
            self.tables[table[0]] = list()  # {table: [prods]}
        emp_aux = self.db.select_employees()
        for employee in emp_aux:
            emp = Employee(employee[0], employee[1])
            self._employees.append(emp)
        self.employee = str(emp_aux[0][1])

        #for employee in self._employees:
        #    self.comboBox_selectEmployee.addItem(employee.name)
        #self.comboBox_selectEmployee.currentIndexChanged['QString'].connect(self.change_default_employee)

        _list_btn_rest = dict()
        _list_btn_bar = dict()
        _list_btn_beguda = dict()
        reader = csv.reader(open('./products.csv', 'r'))
        for index, row in enumerate(reader):
            self.db.insert(row[0].lower(), row[1])
            final_word = ''
            phrase = row[0].split(' ')
            for word in phrase:
                final_word += word
            name_button = '{0}_{1}'.format('btn', final_word.lower())

            # 0: Restaurant, 1: Bar, 2: Begudes
            self.product_box.setCurrentWidget(self.product_box.widget(0))
            if row[2] == 'Bar':
                self.product_box.setCurrentWidget(self.product_box.widget(1))
            elif row[2] == 'Beguda':
                self.product_box.setCurrentWidget(self.product_box.widget(2))
            if row[1] == '0':
                self.btn = QPushButton(row[0], self.product_box.currentWidget())
            else:
                m = Menjar(row[0], row[1]) # Product(name, price)
                self._products.append(m)
                #self.btn = QPushButton('{0} {1}'.format(str(row[0]), str(row[1])), self.product_box.currentWidget())
                self.btn = QPushButton('{0}'.format(str(row[0])), self.product_box.currentWidget())
            p = Product(row[0], row[1], row[2])
            self.products[p.name] = p

            print(row)
            if row[2] == 'Restaurant' and row[0] == self.suplement_concept:
                self.btn.setStyleSheet("background-color: gold;")
                _list_btn_rest[p] = self.btn
            elif row[2] == 'Restaurant':
                self.btn.setStyleSheet("background-color: springgreen;")
                _list_btn_rest[p] = self.btn
            elif row[2] == 'Bar':
                self.btn.setStyleSheet("background-color: tomato;")
                _list_btn_bar[p] = self.btn
            elif row[2] == 'Beguda':
                self.btn.setStyleSheet("background-color: gold;")
                _list_btn_beguda[p] = self.btn

            # X, Y, WIDTH, HEIGHT
        num_btn = self.db.select()
        _list_btn = [_list_btn_rest, _list_btn_bar, _list_btn_beguda]
        for lbutton in _list_btn:
            x = 30
            y = 30
            width = 110
            height = 110
            it = 1
            for product, button in lbutton.items():
                if product.name != self.suplement_concept:
                    button.clicked.connect(lambda: self.set_product(product))
                else:
                    button.clicked.connect(self.show_dialog)
                button.setGeometry(x, y, width, height)
                if it != 5:
                    x = x + width
                    it = it + 1
                else:
                    it = 1
                    y = y + height
                    x = 30

        self.show()
        self.paint()

    def separa(self, text):
        if len(text) > 8 and len(text.split(' ')) == 3:
            return '{0}{1}{2}'.format(text[0:-2],'\n',text.split(' ')[-1])
        elif len(text) > 8 and len(text.split(' ')) == 2:
            return '{0}{1}{2}'.format(text[0:-2],'\n',text.split(' ')[-1])
        else:
            return text

    def set_product_table(self, product, quant, price):
        rowPosition = self.order_view.rowCount()
        self.order_view.insertRow(rowPosition)
        if isinstance(price, str):
            price = float(price)
        self.order_view.setItem(rowPosition, 0, QTableWidgetItem(str(product)))
        self.order_view.setItem(rowPosition, 1, QTableWidgetItem(str(quant)))
        self.order_view.setItem(rowPosition, 2, QTableWidgetItem(str("%.2f" % price)+u' €'))

    def remove_products_table(self):
        rows = self.order_view.rowCount()
        for i in range(rows):
            self.order_view.removeRow(0)

    def paint(self):
        completed = 0
        """while completed < 100:
            completed += 0.0001
            self.progressBar.setValue(completed)"""

    def add_price(self, total, subtotal=None, iva=None):
        if subtotal:
            _subtotal = self.subtotal_label.toPlainText().split(':')
            if len(_subtotal) > 1:
                _subtotal = float(_subtotal[1]) + subtotal
            else:
                _subtotal = subtotal
            self.subtotal_label.setText('Subtotal: ' + str("%.2f" % _subtotal))
        if iva:
            _iva = self.iva_label.toPlainText().split(':')
            if len(_iva) > 1:
                _iva = float(_iva[1]) + iva
            else:
                _iva = iva
            self.iva_label.setText('IVA: ' + str("%.2f" % _iva))

        _price = float(total) + float(self.lcdNumber.value())
        self.lcdNumber.display("%.2f" % _price)
        self.total_label.setText('Total: ' + str("%.2f" % _price))

    def delete_price(self, discount):
        print(type(discount))
        print(type(self.lcdNumber.value()))
        _price = float(discount) - float(self.lcdNumber.value())
        self.lcdNumber.display(abs(_price))

    def set_product(self, nothing):
        product = self.products[str(self.sender().text())]
        price = product.price
        price_multi = float(price) * float(self.add_num)

        self.set_product_table(product.name, self.add_num, price_multi)

        result = str(self.sender().text())
        self.tables[self.table_id].append(LineProd(result, price_multi, self.add_num))
        result = result+u'€   '+str(self.add_num)
        self.add_num = 1

        subtotal = self.calc_iva(price_multi)
        iva = price_multi - subtotal
        # Patched iva
        #iva = (price_multi * self.iva) / 100
        #subtotal = price_multi - iva
        self.add_price(price_multi, subtotal, iva)

    def set_product_to_del(self, nothing):
        print('CLICK: ', nothing)
        price = str(self.sender().text())
        price = price.split(' ')
        if len(price) > 1:
            price_multi = float(price[len(price) - 1]) * float(self.add_num)
        else:
            price_multi = float(price[len(price)-1]) * float(self.add_num)

        if len(price) > 1:
            price = price[len(price)-1]
        else:
            price = 0

        result = str(self.sender().text())
        self.set_product_table(result, self.add_num, price_multi)
        self.tables[self.table_id].append(LineProd(result, price_multi, self.add_num))
        result = result+u'€   '+str(self.add_num)
        self.add_num = 1
        #res = self.separa(result)
        #result = '%s %s' % (method, price)

        subtotal = self.calc_iva(price_multi)
        iva = price_multi - subtotal
        # Patched iva
        #iva = (price_multi * self.iva) / 100
        #subtotal = price_multi - iva
        self.add_price(price_multi, subtotal, iva)

    def delete_item(self):
        if self.order_view.selectedItems():
            for _item in self.order_view.selectedItems():
                #price = self.order_view.item(_item.row(), 2).text().replace(' €', '')
                #self.lcdNumber.display(self.lcdNumber.value() - float(price))
                print(self.tables[self.table_id])
                self.tables[self.table_id].pop(_item.row())
                print(self.tables[self.table_id])
                self.order_view.removeRow(_item.row())
                self.recalc_price()
                break

    def cancel_ticket(self):
        self.remove_products_table()
        self.reset_displays()
        self.tables[self.table_id] = []

    def calc_iva(self, total):
        substract = float(total) / (1 + (self.iva / 100.0))
        return substract

    def recalc_price(self):
        total = 0
        for product in self.tables[self.table_id]:
            total += float(product.price)

        if total != 0.0:
            subtotal = self.calc_iva(total)
            iva = total - subtotal
            # Patched iva
            #iva = (total * self.iva) / 100
            #subtotal = total - iva
            self.subtotal_label.setText('Subtotal: ' + str("%.2f" % subtotal))
            self.total_label.setText('Total: ' + str("%.2f" % total))
            self.iva_label.setText('IVA: ' + str("%.2f" % iva))
            self.lcdNumber.display("%.2f" % total)
        else:
            self.reset_displays()

    def reset_displays(self):
        self.lcdNumber.display(0)
        self.subtotal_label.setText('Subtotal')
        self.iva_label.setText('IVA')
        self.total_label.setText('Total')

    def invoicing(self):
        try:
            if not self.check_license():
                self.messaging.show('Llicencia caducada', type='warning')
                return False
        except Exception as err:
            self.logger.error(str(err))
        if self.lcdNumber.value() == 0:
            self.messaging.show('No has afegit cap producte', 'warning')
        else:
            self.ticket_number += 1
            self.label_ticket_number.setText('Tiquet Nº: {0}'.format(self.ticket_number))
            #self.write_invoice()
            self.messaging.show(message='{0} {1}'.format('Cobrat', str("%.2f" % self.lcdNumber.value())))
            self.remove_products_table()
            self.tables[self.table_id].clear()
            self.db.insert_ticket(str(time.strftime('%Y/%m/%d %H:%M:%S')), self.table_num, self.employee, float(self.lcdNumber.value()))
            self.db.update_ticket_number(1, self.ticket_number)
            self.reset_displays()
            #self.print_invoice()

    def gen_invoice(self):
        if self.lcdNumber.value() == 0:
            self.messaging.show('No has afegit cap producte', 'warning')
            return False
        pi = PrintInvoice(self, self.db, self.messaging, self.tables[self.table_id], self.ticket_number)
        pi.show()

    def write_invoice(self):
        f = open('invoice.csv', 'w')
        f.write('{0} #{1}{2}'.format('TICKET', self.ticket_number, '\n')),
        f.write(time.strftime('%d/%m/%y %H:%M:%S'))
        f.write('\n')
        f.write('------------\n')
        f.write('\n')
        f.write(self.table_num)
        f.write('\n')
        f.write(self.employee)
        f.write('\n')
        f.write('------------\n')
        f.write('RESUM:\n')
        to_write = ''
        for index in range(2):
            to_write = ''
            #to_write = str(self.listWidget.item(index).text())
        f.write(to_write)
        f.write('\n')
        f.write('\n\n')
        f.write('TOTAL:\n')
        f.write('------------\n')
        f.write(str(self.lcdNumber.value()))
        f.write('\n\nGracies')
        f.close()

    def print_invoice(self):
        if sys.platform == 'win32':
            pass
        else:
            os.startfile('./invoice.csv', 'print')

    def open_configs(self):
        config = Config(self, self.db, self.messaging, self.partners, self.employee)
        config.show()

    def change_mode(self):
        diag = QDialog()
        layout = QHBoxLayout()
        total = QLabel()
        cash = QTextEdit()
        bill = QPushButton()
        layout.addWidget(total)
        layout.addWidget(cash)
        layout.addWidget(bill)
        diag.setLayout(layout)
        diag.show()
        self.lcdNumber.value()

    def show_dialog(self):
        price, ok = QInputDialog.getText(self, 'afegir linia', 'Entra el preu:')
        if ok:
            product = self.products[str(self.sender().text())]
            try:
                price_multi = float(price) * float(self.add_num)
            except ValueError:
                return False
            self.set_product_table(product.name, self.add_num, price_multi)
            result = str(self.sender().text())
            self.tables[self.table_id].append(LineProd(product.name, price_multi, self.add_num))
            self.add_num = 1

            subtotal = self.calc_iva(price_multi)
            iva = price_multi - subtotal
            # Patched iva
            #iva = (price_multi * self.iva) / 100
            #subtotal = price_multi - iva
            self.add_price(price_multi, subtotal, iva)

    def show_dialog_table(self):
        if self.tables:
            self.q_diag = QDialog(self)
            #self.q_diag.setWindowTittle('Taula')
            print(self.tables)
            x = 10
            y = 10
            width = 100
            height = 100
            i = 0
            for num, prods in self.tables.items():
                if num == 5:
                    text = 'Barra '
                else:
                    text = 'Taula '
                i = (i % 2)+1  # repet two
                if i == 1:
                    self.btn = QPushButton('{0} {1}'.format(text, str(num)), self.q_diag)
                    self.btn.setGeometry(x, y, width, height)
                    if prods:
                        self.btn.setStyleSheet("background-color: tomato;")
                    else:
                        self.btn.setStyleSheet("background-color: gold;")
                    self.btn.clicked.connect(self.table_select)
                    x = x+width
                else:
                    self.btn = QPushButton('{0} {1}'.format(text, str(num)), self.q_diag)
                    self.btn.setGeometry(x, y, width, height)
                    if prods:
                        self.btn.setStyleSheet("background-color: tomato;")
                    else:
                        self.btn.setStyleSheet("background-color: gold;")
                    self.btn.clicked.connect(self.table_select)
                    y = y+height
                    x = 10
            self.q_diag.exec_()
        else:
            self.messaging.show('Taules no definides', 'warning')

    def open_table(self):
        pass

    def table_select(self):
        self.table_num = str(self.sender().text())
        num = self.table_num.split(' ')[2]
        if int(num) != self.table_id:
            self.table_id = int(num)
            self.change_table()
            self.label_table.setText('{0}{1}'.format('Taula ', str(num)))
        self.q_diag.close()

    def change_table(self):
        self.remove_products_table()
        self.reset_displays()
        total = 0
        for product in self.tables[self.table_id]:
            total += float(product.price)
            self.set_product_table(product.name, product.quant, product.price)

        if total != 0.0:
            subtotal = self.calc_iva(total)
            iva = total - subtotal
            # Patched iva
            #iva = (total * self.iva) / 100
            #subtotal = total - iva
            self.subtotal_label.setText('Subtotal: ' + str("%.2f" % subtotal))
            self.total_label.setText('Total: ' + str("%.2f" % total))
            self.iva_label.setText('IVA: ' + str("%.2f" % iva))
            _total = self.lcdNumber.value() + float(total)
            self.lcdNumber.display("%.2f" % _total)

    def change_default_employee(self, sign):
        print('employee, ', sign)
        self.employee = str(sign)

    def connect_buttons_calc(self):
        self.btn_num0.clicked.connect(lambda: self.add_opper(0))
        self.btn_num1.clicked.connect(lambda: self.add_opper(1))
        self.btn_num2.clicked.connect(lambda: self.add_opper(2))
        self.btn_num3.clicked.connect(lambda: self.add_opper(3))
        self.btn_num4.clicked.connect(lambda: self.add_opper(4))
        self.btn_num5.clicked.connect(lambda: self.add_opper(5))
        self.btn_num6.clicked.connect(lambda: self.add_opper(6))
        self.btn_num7.clicked.connect(lambda: self.add_opper(7))
        self.btn_num8.clicked.connect(lambda: self.add_opper(8))
        self.btn_num9.clicked.connect(lambda: self.add_opper(9))
        self.btn_numc.clicked.connect(lambda: self.add_opper(0))

    def add_opper(self, num):
        if num == 0:
            self.add_num = 1
        else:
            self.add_num = num

    def check_license(self):
        try:
            code, dt = self.db.select_license()
        except:
            self.messaging.show('Llicencia no activada')
            return False
        u = Utils()
        if u.three_days_warning(dt):
            self.messaging.show('Llicencia caduca el {0}'.format(dt), type='warning')
        if u.check_code(code) and u.check_license(code, dt):
            return True
        else:
            self.messaging.show('Llicencia no activada')
            return False

    def read_config_file(self):
        parser = configparser.ConfigParser()
        base_path = './configs/'
        parser.read(base_path + '/config.cfg')
        iva = parser.getint('IVA', 'iva')
        self.iva = iva
        try:
            self.listing_path = parser.get('PATH', 'path')
        except configparser.NoSectionError:
            try:
                self.listing_path = str(os.environ['HOME'])
            except KeyError:
                self.listing_path = str(os.environ['USERPROFILE'])
        try:
            self.main_view = parser.get('VIEW', 'view')
        except configparser.NoSectionError:
            self.main_view = 'restaurant.ui'

    def set_main_title(self):
        parser = configparser.ConfigParser()
        base_path = './configs/'
        parser.read(base_path + '/config.cfg')
        name = parser.get('NAME', 'name')
        try:
            self.setWindowTitle('Compta Cash - {}'.format(name))
        except configparser.NoSectionError:
            self.setWindowTitle('Compta Cash')

    def config(self):
        dialog = QDialog()
        dialog.ui = Ui_Dialog()
        dialog.ui.setupUi(dialog)
        dialog.exec_()
        dialog.show()


class PrintInvoice(QDialog):
    def __init__(self, parent, db, messaging, info_table, ticket_number):
        super(PrintInvoice, self).__init__(parent)
        uic.loadUi(TEMPLATES + '/invoice_print.ui', self)
        self.db = db
        self.messaging = messaging
        self.table = info_table
        self.ticket_number = ticket_number
        self.clients = list()
        self.selected_client = False
        for c in self.db.select_client():
            self.clients.append(Client(name=c[1], cif=c[0], direccio=c[2], cp=c[3], phone=c[4], email=c[5]))
        for client in sorted(self.clients):
            self.combobox_client.addItem(str(client))

        self.combobox_client.currentIndexChanged['QString'].connect(self.change_client)
        self.flag_client.stateChanged.connect(self.activate_desactivate_labels)
        self.print_button.clicked.connect(self.print_invoice)

    def activate_desactivate_labels(self):
        if self.flag_client.isChecked():
            self.label_name.setEnabled(False)
            self.label_cif.setEnabled(False)
            self.label_cp.setEnabled(False)
            self.label_address.setEnabled(False)
            self.label_phone.setEnabled(False)
            self.label_email.setEnabled(False)
        else:
            self.label_name.setEnabled(True)
            self.label_cif.setEnabled(True)
            self.label_cp.setEnabled(True)
            self.label_address.setEnabled(True)
            self.label_phone.setEnabled(True)
            self.label_email.setEnabled(True)

    def change_client(self):
        client = self.combobox_client.currentText()
        for c in self.clients:
            if str(c) == client:
                self.selected_client = c
                break

    def print_invoice(self):
        if self.flag_client.isChecked():
            client = self.combobox_client.currentText()
            for c in self.clients:
                if str(c) == client:
                    self.selected_client = c
                    break
        else:
            name = self.label_name.text()
            cif = self.label_cif.text()
            cp = self.label_cp.text()
            address = self.label_address.text()
            phone = self.label_phone.text()
            email = self.label_email.text()
            if name == '' or cif == '' or address == '' or cp == '':
                self.messaging.show('Client no entrat correctament', 'warning')
                self.close()
                return False

            self.selected_client = Client(name=name, cif=cif, direccio=address, cp=cp, phone=phone, email=email)
            self.db.insert_client(cif=cif, name=name, address=address, cp=cp, phone=phone, email=email)
        i = Invoicing()
        for product in self.table:
            print(product)
        filename = i.invoicing(self.selected_client, self.table, 10, self.ticket_number)
        i.open_invoice(filename)
        self.close()


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(358, 125)
        l1 = QLabel("Nom")
        self.name = QLineEdit()
        l2 = QLabel("Preu")
        self.price = QLineEdit()
        fbox = QFormLayout()
        fbox.addRow(l1, self.name)
        fbox.addRow(l2, self.price)
        btn_ok = QPushButton('Ok')
        btn_cancel = QPushButton('Cancelar')
        fbox.addRow(btn_ok, btn_cancel)

        btn_ok.clicked.connect(self.ok)
        btn_cancel.clicked.connect(self.cancel)
        Dialog.setLayout(fbox)

    def ok(self):
        if self.price.text() and self.name.text():
            try:
                price = float(self.price.text())
                with open('products.csv', 'a') as file:
                    file.write('{0},{1}{2}'.format(self.name.text(), price, '\n'))
                    file.close()
            except ValueError:
                pass

    def cancel(self):
        pass


class Db:
    def __init__(self):
        import sqlite3
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''Drop table if exists producte''')
        self.conn.commit()
        self.cursor.execute('''Create table if not exists producte(name, price)''')
        self.conn.commit()
        self.cursor.execute('''Create table if not exists ticket(id, num_table, employee, total)''')
        self.conn.commit()
        self.cursor.execute('''Create table if not exists ticket_number(id, number)''') # Innit zero with id 1
        self.conn.commit()
        self.cursor.execute('''Create table if not exists llicencia(code, timestamp)''')
        self.conn.commit()
        self.cursor.execute('''Drop table if exists taula''')
        self.conn.commit()
        self.cursor.execute('''Create table if not exists taula(id, description)''')
        self.conn.commit()
        self.cursor.execute('''Create table if not exists proveidor(nif, name, grup)''')
        self.conn.commit()
        self.cursor.execute('''Create table if not exists empleat(id, name, password)''')
        self.conn.commit()
        self.cursor.execute('''Create table if not exists payments(id, partner, grup, number, base, iva4, iva10, iva21, total)''')
        self.conn.commit()
        self.cursor.execute('''Create table if not exists client(nif, name, address, cp, telf, email)''')
        self.conn.commit()
        self.init_db()

    @property
    def db_path(self):
        try:
            return '/'.join([str(os.environ['HOME']), 'restaurant.db'])
        except KeyError:
            return '/'.join([str(os.environ['USERPROFILE']), 'restaurant.db'])

    def init_db(self):
        employees = [x for x in self.cursor.execute('''select * from empleat''')]
        tables = [x for x in self.cursor.execute('''select * from taula''')]
        if not employees:
            _values = [(1, 'Empleat 1', 'No')]
            self.cursor.executemany('Insert into empleat values (?, ?, ?)', _values)
            self.conn.commit()
        if not tables:
            self.insert_tables()

    def insert(self, name, price):
        _values = [(name, price)]
        self.cursor.executemany('Insert into producte values (?, ?)', _values)
        self.conn.commit()

    def insert_ticket(self, num, num_table, employee, total):
        _values = [(num, num_table, employee, total)]
        self.cursor.executemany('Insert into ticket values (?, ?, ?, ?)', _values)
        self.conn.commit()

    def insert_payment(self, num, partner, group, number, base4, iva4, base10, iva10, base21, iva21, total):
        _values = [(num, partner, group, number, base4, iva4, base10, iva10, base21, iva21, total)]
        self.cursor.executemany('Insert into payments values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', _values)
        self.conn.commit()

    def insert_partner(self, cif, name, group=''):
        _values = [(cif, name, group)]
        self.cursor.executemany('Insert into proveidor values (?, ?, ?)', _values)
        self.conn.commit()

    def insert_client(self, cif, name, address, cp, phone='', email=''):
        _values = [(cif, name, address, cp, phone, email)]
        self.cursor.executemany('Insert into client values (?, ?, ?, ?, ?, ?)', _values)
        self.conn.commit()

    def insert_license(self, code, dt):
        self.cursor.execute('delete from llicencia')
        self.conn.commit()
        _values = [(code, dt)]
        self.cursor.executemany('Insert into llicencia values (?, ?)', _values)
        self.conn.commit()

    def insert_tables(self):
        for i in range(1, 5):
            _values = [(i, "Taula")]
            self.cursor.executemany('Insert into taula values (?, ?)', _values)
            self.conn.commit()
        _values = [(i + 1, "Barra")]
        self.cursor.executemany('Insert into taula values (?, ?)', _values)
        self.conn.commit()

    def update_ticket_number(self, id, number):
        self.cursor.execute('Update ticket_number set number={0} where id={1}'.format(number, id))
        self.conn.commit()

    def select(self):
        prod = 0
        for row in self.cursor.execute('''select * from producte'''):
            prod = prod+1
        return prod

    def select_table(self):
        _table = list()
        for row in self.cursor.execute('''select * from taula'''):
            _table.append(row)
        return _table

    def select_ticket_number(self):
        try:
            for row in self.cursor.execute('''select number from ticket_number where id=1'''):
                print('ticket number')
                print(row)
            ret = row[0]
        except:
            _values = [(1, 1)]
            self.cursor.executemany('Insert into ticket_number values (?, ?)', _values)
            self.conn.commit()
            ret = 1

        return ret

    def select_employees(self):
        self.conn.commit()
        _employee = list()
        for row in self.cursor.execute('''select * from empleat'''):
            _employee.append(row)
        return _employee

    def select_ticket(self, option, di=None, df=None):
        _ticket = list()
        if option == 'total':
            for row in self.cursor.execute('''select * from ticket'''):
                _ticket.append(row)
        elif option == 'year':
            di += '%'
            for row in self.cursor.execute("select * from ticket where id like :di", {"di": di}):
                _ticket.append(row)
        elif option == 'month':
            month = time.strftime('/%m/')
            for row in self.cursor.execute("select * from ticket where id >=:di and id <=:df", {"di": di, "df": df}):
                _ticket.append(row)
        elif option == 'day':
            di += '%'
            for row in self.cursor.execute("select * from ticket where id like :di", {"di": di}):
                _ticket.append(row)
        return _ticket

    def select_sell_by_dates(self, di, df):
        inform = list()
        for row in self.cursor.execute("select * from ticket where id >=:di and id <=:df", {"di": di, "df": df}):
            inform.append(row)
        return inform

    def select_sell_by_import(self, price):
        inform = list()
        for row in self.cursor.execute("select * from ticket where total >=:price", {"price": price}):
            inform.append(row)
        return inform

    def select_payments_by_dates(self, di, df):
        inform = list()
        for row in self.cursor.execute("select * from payments where id >=:di and id <=:df", {"di": di, "df": df}):
            inform.append(row)
        return inform

    def select_payments_by_import(self, price):
        inform = list()
        for row in self.cursor.execute("select * from payments where total >=:price", {"price": price}):
            inform.append(row)
        return inform

    def select_license(self):
        _license = list()
        for row in self.cursor.execute('''select code, timestamp from llicencia'''):
            _license.append(row)
        return _license[0]

    def select_partner(self):
        _partner = list()
        for row in self.cursor.execute('''select * from proveidor'''):
            _partner.append(row)
        return _partner

    def select_client(self):
        _costumer = list()
        for row in self.cursor.execute('''select * from client'''):
            _costumer.append(row)
        return _costumer

    def delete_ticket(self, table, _id):
        query = "delete from {} where id='{}'".format(table, _id)
        print(query)
        self.cursor.execute(query)
        self.conn.commit()

    def delete_payment(self, table, _id, partner, total):
        query = "delete from {} where id='{}' and partner='{}' and total={}".format(table, _id, partner, total)
        print(query)
        self.cursor.execute(query)
        self.conn.commit()

    def alter_payments(self):
        drop_column = "ALTER TABLE payments DELETE COLUMN iva"
        #self.cursor.execute(drop_column)
        try:
            add_column = "ALTER TABLE payments ADD COLUMN iva4"
            self.cursor.execute(add_column)
            add_column = "ALTER TABLE payments ADD COLUMN iva10"
            self.cursor.execute(add_column)
            add_column = "ALTER TABLE payments ADD COLUMN iva21"
            self.cursor.execute(add_column)
        except Exception:
            return False


class Message:

    def show(self, message=None, type=None):
        name = 'name'
        if not type:
            QMessageBox.information(None, name, message)
        elif type == 'warning':
            QMessageBox.warning(None, name, message)
        else:
            QMessageBox.information(None, name, message)

class LineProd:
    def __init__(self, name, price, quant):
        self.name = name
        self.price = "%.2f" % price
        self.quant = quant


# LOGS
def setup_log():
    logger = logging.getLogger('Compta cash')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    try:
        user_path = r'{0}/{1}'.format(os.environ['HOME'], 'logs_compta_cash.log')
    except KeyError:
        user_path = r'{0}/{1}'.format(os.environ['USERPROFILE'], 'logs_compta_cash.log')
    hdlr = logging.FileHandler(user_path)
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    logs = logger

    return logs


if __name__ == '__main__':
    logger = setup_log()
    app = QApplication(sys.argv)
    ex = Foo(logger)
    sys.exit(app.exec_())
