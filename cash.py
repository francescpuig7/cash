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
                             QLabel, QHBoxLayout, QTextEdit, QWidget, QVBoxLayout, QLineEdit, QFormLayout, QInputDialog)
from product import Product, Menjar, Beguda
from employee import Employee
from utils import Utils
from partner import Partner
# from order import Table
import csv
import configparser
from subprocess import Popen
from platform import system

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
    def __init__(self, db, messaging):
        super(Config, self).__init__()
        uic.loadUi(TEMPLATES + '/config.ui', self)
        self.db = db
        self.messaging = messaging
        self.save_button.clicked.connect(self.save_product)

    def save_product(self):
        if self.price.text() and self.name.text():
            try:
                price = float(self.price.text())
                category = str(self.checkbox_categoria.currentText())
                with open('products.csv', 'a') as file:
                    file.write('{0},{1},{2}\n'.format(self.name.text(), price, category))
                    file.close()
                self.messaging.show('Producte entrat')
                # Reset texts
                self.price.setText('')
                self.name.setText('')
            except ValueError:
                self.messaging.show('Producte no entrat', 'warning')

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
        for partner in sorted(self.partners):
            self.combobox_partner.addItem(str(partner))
        for group in self.GROUPS.values():
            self.combobox_group.addItem(group)

    def paint(self):
        self.show()
        self.date_calendar = None

    def save_payment(self):
        base = float(self.label_base_imposable.text().replace(',', '.'))
        # todo: set default date
        iva = int(str(self.combobox_iva.currentText()).replace('%', ''))

        total = float(self.label_total.text().replace(',', '.'))
        partner_name = self.combobox_partner.currentText()
        group = self.combobox_group.currentText()
        number = self.label_invoice_number.text()
        if not self.date_calendar:
            self.date_calendar = self.date.strftime('%Y/%m/%d')
        if base == 0.0 or iva == 0 or total == 0.0:
            self.messaging.show(message='No has entrat les dades correctament', type='warning')
            return False

        self.db.insert_payment(self.date_calendar, partner_name, group, number, base, iva, total)

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
        self.combobox_iva.setCurrentIndex(1)
        self.combobox_partner.setCurrentIndex(1)
        self.combobox_group.setCurrentIndex(1)


class Listing(QDialog):

    def __init__(self, db, messaging, iva, listing_path):
        super(Listing, self).__init__()
        uic.loadUi(TEMPLATES + '/listing.ui', self)
        self.db = db
        self.iva = iva
        self.listing_path = listing_path
        self.price = 0

        self.btn_payments_monthly.clicked.connect(self.gen_report_dates)
        self.btn_payments_dates.clicked.connect(self.gen_report_dates)
        self.btn_payments_price.clicked.connect(self.gen_report_price_payments)
        self.btn_sells_monthly.clicked.connect(self.gen_report_monthly_sells)
        self.btn_sells_dates.clicked.connect(self.gen_report_price_sells)
        self.btn_sells_price.clicked.connect(self.gen_report_price_sells)

    def gen_report_dates(self):
        pass

    def gen_report_monthly_sells(self):
        month = datetime.now().month
        year = datetime.now().year
        last_day_of_month = calendar.monthrange(year, month)[1]
        di = '{}/{}/01'.format(year, str(month).zfill(2))
        df = '{}/{}/{}'.format(year, str(month).zfill(2), last_day_of_month)
        data = self.db.select_ticket('month', di=di, df=df)
        self.write_file(data, 'ingressos')

    def gen_report_price_sells(self):
        self.price = 0
        self.show_dialog_price()
        data = self.db.select_sell_by_import(self.price)
        self.write_file(data, 'ingressos')

    def gen_report_dates_sells(self):
        di = ''
        df = ''
        data = self.db.select_sell_by_import(di, df)
        self.write_file(data, 'ingressos')

    def gen_report_price_payments(self):
        self.price = 0
        self.show_dialog_price()
        data = self.db.select_payments_by_import(self.price)
        self.write_file(data, 'gastos')

    def filename(self, _type):
        _file = '{}/{}_{}.csv'.format(self.listing_path, _type, datetime.now().strftime('%Y%m%d_%H_%M_%S'))
        return _file

    def write_file(self, data, _type):
        if _type == 'ingressos':
            with open(self.filename(_type), 'w') as f:
                f.write('CONCEPTE;DIA;% IVA;IVA;SUBTOTAL;TOTAL;\n')
                for row in data:
                    taula = row[1]
                    if 'Barra' in taula:
                        concepte = 'VARIS BARRA'
                    else:
                        concepte = 'VARIS TAULA'
                    iva = (float(row[3]) * self.iva) / 100
                    subtotal = float(row[3]) - iva
                    f.write('{};{};{};{};{};{};\n'.format(
                        concepte, row[0], self.iva, "%.2f" % iva, "%.2f" % subtotal, "%.2f" % row[3])
                    )
        elif _type == 'gastos':
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write('CONCEPTE;DIA;PROVEIDOR;NFRA;GRUP;% IVA;BASE IMPOSABLE;TOTAL;\n')
                for row in data:
                    concepte = 'GASTO'
                    f.write('{};{};{};{};{};{};{};{};\n'.format(
                        concepte, row[0], row[1], row[3], row[2], "%.2f" % row[5], "%.2f" % row[4], "%.2f" % row[6])
                    )
        else:
            return False
        try:
            os_name = system().lower()
            if os_name == 'windows':
                starter = 'start'
            elif os_name == 'linux':
                starter = 'xdg-open'
            elif os_name == 'darwin':
                starter = 'open'
            start = ' '.join([starter, self.filename])
            Popen(start, shell=True)
        except Exception as err:
            print(err)
            pass

    def show_dialog_price(self):
        price, ok = QInputDialog.getText(self, 'Seleccionar', 'Entra el preu:')
        if ok:
            try:
                self.price = int(price)
            except Exception as err:
                print(err)
                pass

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
        self.comboBox_select_result.currentIndexChanged['QString'].connect(self.change_default_view)

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
        else:
            return False

        total = 1
        self.sales_view.setRowCount(0)
        for ticket in tickets:
            rowPosition = self.sales_view.rowCount()
            self.sales_view.insertRow(rowPosition)
            self.sales_view.setItem(rowPosition, 0, QTableWidgetItem(str(ticket[0])))
            self.sales_view.setItem(rowPosition, 1, QTableWidgetItem(str(ticket[1])))
            self.sales_view.setItem(rowPosition, 2, QTableWidgetItem(str(ticket[2])))
            self.sales_view.setItem(rowPosition, 3, QTableWidgetItem(str(ticket[3])))
            total += ticket[3]
        self.label_total.setText(str(total))
        self.show()
        # self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Set not editable

    def change_default_view(self, sign):
        self.view = str(sign)
        self.paint()

class Foo(QDialog):
    def __init__(self):
        super(Foo, self).__init__()
        self._products = list()
        self._employees = list()
        self._tables = list()
        self._ltables = list()
        self._lprod = list()
        self.tables = dict()
        self.products = dict()
        self.partners = list()
        self.employee = 'No. def'
        self.table_num = 'Taula 0'
        self.suplement_concept = 'varis'
        try:
            self.listing_path = str(os.environ['HOME'])
        except KeyError:
            self.listing_path = str(os.environ['USERPROFILE'])
        self.table_id = 1
        self.add_num = 1
        self.iva = 21
        self.messaging = Message()
        self._mydict = {'menu': 10, 'menucapsetmana': 25, 'vinegre': 2}
        self.db = Db()
        self.ticket_number = self.db.select_ticket_number()
        self.sales = Sales(self.db)
        self.config = Config(self.db, self.messaging)
        row = self.db.select_partner()
        for x in row:
            partner = Partner(name=x[1], cif=x[0])
            self.partners.append(partner)
        self.read_config_file()
        self.payments = Payments(self.partners, self.messaging, self.db)
        self.license = License(self.db, self.messaging)
        self.listing = Listing(self.db, self.messaging, self.iva, self.listing_path)
        self.initUi()

    def initUi(self):
        self.ui = uic.loadUi('restaurant.ui', self)

        # connect buttons
        self.btn_facturar.clicked.connect(self.invoicing)
        self.btn_obrir_taula.clicked.connect(self.show_dialog_table)
        self.btn_borrar.clicked.connect(self.delete_item)
        self.btn_llistats.clicked.connect(self.listing.paint)
        self.btn_ventas.clicked.connect(self.sales.paint)
        self.btn_config.clicked.connect(self.config.paint)
        self.btn_llicencia.clicked.connect(self.license.paint)
        self.btn_payments.clicked.connect(self.payments.paint)
        self.btn_cancel_ticket.clicked.connect(self.cancel_ticket)
        #self.btn_config.clicked.connect(self.config.login)
        #self.btn_config.clicked.connect(self.config)

        self.connect_buttons_calc()
        self.comboBox_selectDB.addItem('restaurant.db')
        self.comboBox_selectDB.addItem('cafeteria.db')
        date = time.strftime('%d/%m/%y %H:%M:%S')
        self.label_table.setText('Taula 1')
        self.label_time.setText('{0}: {1}'.format(self.label_time.text(), date))
        self.label_ticket_number.setText('{0}: {1}'.format(self.label_ticket_number.text(), self.ticket_number))
        self.order_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.db.select_ticket_number()
        #self.product_box
        #self.btn.clicked.connect(self.paint)
        _tables = self.db.select_table()

        for table in _tables:
            self.tables[table[0]] = list()  # {table: [prods]}
        print('taules: ', self.tables)
        emp_aux = self.db.select_employees()
        for employee in emp_aux:
            emp = Employee(employee[0], employee[1])
            self._employees.append(emp)

        for employee in self._employees:
            self.comboBox_selectEmployee.addItem(employee.name)
        self.comboBox_selectEmployee.currentIndexChanged['QString'].connect(self.change_default_employee)

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
        if False:
            for lbutton in _list_btn:
                x = 30
                y = 30
                width = 110
                height = 110
                it = 1
                for button in lbutton:
                    price = button.text()
                    price = str(price)
                    price = price.split(' ')
                    if len(price) > 1 and price[len(price)-1] != '1.50':
                        button.clicked.connect(lambda: self.set_product(price))
                    elif price[len(price)-1] != '1.50':
                        button.clicked.connect(self.show_dialog)

                    button.setGeometry(x,y,width,height)
                    if it!=6:
                        x = x+width
                        it = it+1
                    else:
                        it = 1
                        y = y+height
                        x = 30
        else:
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
                    if it != 6:
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
        while completed < 100:
            completed += 0.0001
            self.progressBar.setValue(completed)

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

        iva = (price_multi * self.iva) / 100
        subtotal = price_multi - iva
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

        iva = (price_multi * self.iva) / 100
        subtotal = price_multi - iva
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

    def recalc_price(self):
        total = 0
        for product in self.tables[self.table_id]:
            total += float(product.price)

        if total != 0.0:
            iva = (total * self.iva) / 100
            subtotal = total - iva
            self.subtotal_label.setText('Subtotal: ' + str("%.2f" % subtotal))
            self.total_label.setText('Total: ' + str("%.2f" % total))
            self.iva_label.setText('IVA: ' + str("%.2f" % iva))
            self.lcdNumber.display("%.2f" % total)

    def reset_displays(self):
        self.lcdNumber.display(0)
        self.subtotal_label.setText('Subtotal')
        self.iva_label.setText('IVA')
        self.total_label.setText('Total')

    def invoicing(self):
        if not self.check_license():
            self.messaging.show('Llicencia caducada', type='warning')
            return False
        if self.lcdNumber.value() == 0:
            self.messaging.show('No has afegit cap producte', 'warning')
        else:
            self.ticket_number += 1
            self.label_ticket_number.setText('Tiquet Nº: {0}'.format(self.ticket_number))
            self.write_invoice()
            self.messaging.show(message='{0} {1}'.format('Cobrat', str("%.2f" % self.lcdNumber.value())))
            self.remove_products_table()
            self.tables[self.table_id].clear()
            self.db.insert_ticket(str(time.strftime('%Y/%m/%d %H:%M:%S')), self.table_num, self.employee, float(self.lcdNumber.value()))
            self.db.update_ticket_number(1, self.ticket_number)
            self.reset_displays()
            #self.print_invoice()

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
            price_multi = float(price) * float(self.add_num)
            self.set_product_table(product.name, self.add_num, price_multi)
            result = str(self.sender().text())
            self.tables[self.table_id].append(LineProd(product.name, price_multi, self.add_num))
            self.add_num = 1

            iva = (price_multi * self.iva) / 100
            subtotal = price_multi - iva
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
            iva = (total * self.iva) / 100
            subtotal = total - iva
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
        if u.check_code(code) and u.check_license(code, dt):
            return True
        else:
            self.messaging.show('Llicencia no activada')
            return False

    def read_config_file(self):
        parser = configparser.ConfigParser()
        base_path = './configs/'
        parser.read(base_path + '/config.cfg')
        try:
            name = parser.items('NAME')[0][1]
            self.listing_path = parser.items('PATH')[0][1]
            self.setWindowTitle('Kaisher - {}'.format(name))
        except configparser.NoSectionError:
            try:
                self.listing_path = str(os.environ['HOME'])
            except KeyError:
                self.listing_path = str(os.environ['USERPROFILE'])
            self.setWindowTitle('Kaisher')

    def config(self):
        dialog = QDialog()
        dialog.ui = Ui_Dialog()
        dialog.ui.setupUi(dialog)
        dialog.exec_()
        dialog.show()

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
        self.cursor.execute('''Create table if not exists payments(id, partner, grup, number, base, iva, total)''')
        self.conn.commit()
        self.init_db()

    @property
    def db_path(self):
        return '/'.join([str(os.environ['HOME']), 'restaurant.db'])

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

    def insert_payment(self, num, partner, group, number, base, iva, total):
        _values = [(num, partner, group, number, base, iva, total)]
        self.cursor.executemany('Insert into payments values (?, ?, ?, ?, ?, ?, ?)', _values)
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
        row = [1]
        for row in self.cursor.execute('''select number from ticket_number where id=1'''):
            print(row)
        return row[0]

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Foo()
    sys.exit(app.exec_())
