# -*- coding: utf-8 -*-
import sys
import os
import time
import random
from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import (QApplication, QDialog, QPushButton, QTableWidgetItem, QMessageBox, QLabel, QHBoxLayout, QTextEdit, QWidget, QVBoxLayout, QLineEdit, QFormLayout)
from product import Menjar, Beguda
from employee import Employee
# from order import Table
import csv

class Sales(QDialog):
    def __init__(self, db):
        super(Sales, self).__init__()
        uic.loadUi('extracts.ui', self)
        self.db = db
        self.view = 'Dia'
        self.comboBox_select_result.currentIndexChanged['QString'].connect(self.change_default_view)

    def paint(self):
        if self.view == 'Dia':
            tickets = self.db.select_ticket('day')
        elif self.view == 'Mes':
            tickets = self.db.select_ticket('month')
        elif self.view == 'Any':
            tickets = self.db.select_ticket('year')
        elif self.view == 'Total':
            tickets = self.db.select_ticket('total')

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

class Foo(QDialog):
    def __init__(self):
        super(Foo, self).__init__()
        self._products = list()
        self._employees = list()
        self._tables = list()
        self._ltables = list()
        self._lprod = list()
        self.tables = dict()
        # self._ltables.append(Table(1))
        self.employee = 'No. def'
        self.table_num = 'Taula 0'
        self.table_id = 1
        self.add_num = 1
        self.messaging = Message()
        self._mydict = {'menu': 10, 'menucapsetmana': 25, 'vinegre': 2}
        self.db = Db()
        self.sales = Sales(self.db)
        self.initUi()

    def initUi(self):
        self.ui = uic.loadUi('restaurant.ui', self)
        # connect buttons
        self.btn_ventas.clicked.connect(self.sales.paint)
        self.btn_obrir_taula.clicked.connect(self.show_dialog_table)
        self.btn_borrar.clicked.connect(self.delete_item)
        self.btn_facturar.clicked.connect(self.invoicing)
        self.btn_config.clicked.connect(self.config)
        self.connect_buttons_calc()
        self.comboBox_selectDB.addItem('restaurant.db')
        self.comboBox_selectDB.addItem('cafeteria.db')
        date = time.strftime('%d/%m/%y %H:%M:%S')
        self.label_table.setText('Taula 1')
        self.label_time.setText(str(date))
        #self.btn.clicked.connect(self.paint)
        _tables = self.db.select_table()
        print('taules: ', _tables)
        for table in _tables:
            self.tables[table[0]] = list()  # {table: [prods]}
        print(self.tables)
        emp_aux = self.db.select_employees()
        for employee in emp_aux:
            emp = Employee(employee[0], employee[1])
            self._employees.append(emp)

        #self.comboBox_selectEmployee.maxVisibleItems(15)
        for employee in self._employees:
            self.comboBox_selectEmployee.addItem(employee.name)
        self.comboBox_selectEmployee.currentIndexChanged['QString'].connect(self.change_default_employee)

        #self.tabWidget
        #self.vBoxlayout = QtGui.QVBoxLayout()

        _list_btn = list()
        reader = csv.reader(open('./products.csv', 'r'))
        for index, row in enumerate(reader):
            self.db.insert(row[0].lower(), row[1])
            final_word = ''
            phrase = row[0].split(' ')
            for word in phrase:
                final_word += word
            name_button = '{0}_{1}'.format('btn', final_word.lower())
            print(name_button)
            if row[1] == '0':
                self.btn = QPushButton(row[0], self)
            else:
                m = Menjar(row[0], row[1]) # Product(name, price)
                self._products.append(m)
                text_btn = self.separa('{0} {1}'.format(str(row[0]), str(row[1])))
                #self.btn = QPushButton(text_btn,self)
                self.btn = QPushButton('{0} {1}'.format(str(row[0]), str(row[1])), self)

            _list_btn.append(self.btn)
            # X, Y, WIDTH, HEIGHT
        num_btn = self.db.select()

        x = 30
        y = 30
        width = 100
        height = 100
        it = 1
        for button in _list_btn:
            rand = random.randint(1,3)
            price = button.text()
            price = str(price)
            price = price.split(' ')
            if len(price) > 1 and price[len(price)-1] != '1.50':
                #button.clicked.connect(lambda: self.set_product(price[len(price)-1]))
                button.clicked.connect(lambda: self.set_product(price))
            elif price[len(price)-1] != '1.50':
                button.clicked.connect(self.show_dialog)

            button.setGeometry(x,y,width,height)
            if it!=4:
                if rand == 1:
                    button.setStyleSheet("background-color: springgreen;")
                elif rand == 2:
                    button.setStyleSheet("background-color: gold;")
                else:
                    button.setStyleSheet("background-color: tomato;")
                x = x+width
                it = it+1
            else:
                it = 1
                if rand == 1:
                    button.setStyleSheet("background-color: springgreen;")
                elif rand == 2:
                    button.setStyleSheet("background-color: gold;")
                else:
                    button.setStyleSheet("background-color: tomato;")
                y = y+height
                x = 30

        for prod in self._products:
            print(repr(prod))

        #self.tab1.setLayout(self.vBoxlayout)
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
        self.order_view.setItem(rowPosition, 0, QTableWidgetItem(str(product)))
        self.order_view.setItem(rowPosition, 1, QTableWidgetItem(str(quant)))
        self.order_view.setItem(rowPosition, 2, QTableWidgetItem(str(price)+u' €'))

    def remove_products_table(self):
        rows = self.order_view.rowCount()
        for i in range(rows):
            self.order_view.removeRow(0)

    def paint(self):
        completed = 0
        while completed < 100:
            completed += 0.0001
            self.progressBar.setValue(completed)

    def add_price(self, price):
        _price = float(price) + float(self.lcdNumber.value())
        self.lcdNumber.display(_price)

    def delete_price(self, discount):
        print(type(discount))
        print(type(self.lcdNumber.value()))
        _price = float(discount) - float(self.lcdNumber.value())
        self.lcdNumber.display(abs(_price))

    def set_product(self, nothing):
        print('CLICK: ', nothing)
        price = str(self.sender().text())
        price = price.split(' ')
        price_multi = float(price[len(price)-1]) * float(self.add_num)

        if len(price) > 1:
            price = price[len(price)-1]
        else:
            price = 0

        result = str(self.sender().text())
        self.set_product_table(result, self.add_num, price_multi)
        self.tables[self.table_id].append(LineProd(result, self.add_num, price_multi))
        result = result+u'€   '+str(self.add_num)
        self.add_num = 1
        #res = self.separa(result)
        #result = '%s %s' % (method, price)

        self.add_price(price_multi)

    def delete_item(self):
        if self.order_view.selectedItems():
            for _item in self.order_view.selectedItems():
                price = self.order_view.item(_item.row(), 2).text().replace(' €', '')
                self.lcdNumber.display(self.lcdNumber.value() - float(price))
                print(self.tables[self.table_id])
                self.tables[self.table_id].pop(_item.row())
                print(self.tables[self.table_id])
                self.order_view.removeRow(_item.row())

    def invoicing(self):
        if self.lcdNumber.value() == 0:
            self.messaging.show('No has afegit cap producte', 'warning')
        else:
            self.write_invoice()
            self.messaging.show(message='{0} {1}'.format('Cobrat', str(self.lcdNumber.value())))
            self.remove_products_table()
            self.tables[self.table_id].clear()
            self.db.insert_ticket(str(time.strftime('%d/%m/%y %H:%M:%S')),self.table_num, self.employee, float(self.lcdNumber.value()))
            self.lcdNumber.display(0)
            #self.print_invoice()

    def write_invoice(self):
        f = open('invoice.csv', 'w')
        f.write('TICKET\n')
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
        for index in range(self.listWidget.count()):
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
        price, ok = QtGui.QInputDialog.getText(self, 'afegir linia', 'Entra el preu:')
        if ok:
            product = self.sender().text()
            line = '{0} {1}'.format(str(product), str(price))
            self.listWidget.addItem(line)
            self.add_price(price)

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
                i = (i % 2)+1  # repet two
                if i == 1:
                    self.btn = QPushButton('{0} {1}'.format('Taula ', str(num)), self.q_diag)
                    self.btn.setGeometry(x, y, width, height)
                    if prods:
                        self.btn.setStyleSheet("background-color: tomato;")
                    else:
                        self.btn.setStyleSheet("background-color: gold;")
                    self.btn.clicked.connect(self.table_select)
                    x = x+width
                else:
                    self.btn = QPushButton('{0} {1}'.format('Taula ', str(num)), self.q_diag)
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
        self.lcdNumber.display(0)
        for product in self.tables[self.table_id]:
            self.lcdNumber.display(self.lcdNumber.value() + product.quant)
            self.set_product_table(product.name, product.price, product.quant)

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
            print('pass')
        else:
            print('nopass')
        with open('products.csv', 'w') as file:
            file.write('{0},{1}{2}'.format(self.name.text(), self.price.text(), '\n'))
            file.close()

    def cancel(self):
        pass

class Db:
    def __init__(self):
        import sqlite3
        self.conn = sqlite3.connect('restaurant.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''Drop table if exists producte''')
        self.conn.commit()
        self.cursor.execute('''Create table if not exists producte(name, price)''')
        self.conn.commit()
        self.cursor.execute('''Create table if not exists ticket(id, num_table, employee, total)''')
        self.conn.commit()

    def insert(self, name, price):
        _values = [(name, price)]
        self.cursor.executemany('Insert into producte values (?, ?)', _values)
        self.conn.commit()

    def insert_ticket(self, num, num_table, employee, total):
        _values = [(num, num_table, employee, total)]
        self.cursor.executemany('Insert into ticket values (?, ?, ?, ?)', _values)
        self.conn.commit()

    def select(self):
        prod = 0
        for row in self.cursor.execute('''select * from producte'''):
            prod = prod+1
        return prod

    def select_table(self):
        _table = list()
        for row in self.cursor.execute('''select id from taula'''):
            _table.append(row)
        return _table

    def select_employees(self):
        #_values = [(3, 'Francesc','no')]
        #self.cursor.executemany('Insert into empleat values (?, ?, ?)', _values)
        self.conn.commit()
        _employee = list()
        for row in self.cursor.execute('''select * from empleat'''):
            _employee.append(row)
        return _employee

    def select_ticket(self, option):
        _ticket = list()
        if option == 'total':
            for row in self.cursor.execute('''select * from ticket'''):
                _ticket.append(row)
        elif option == 'year':
            year = time.strftime('/%y ')
            query = '{0}{1}{2}'.format("select * from ticket where id like '%", year, "%'")
            for row in self.cursor.execute('''select * from ticket'''):
                _ticket.append(row)
        elif option == 'month':
            month = time.strftime('/%m/')
            query = '{0}{1}{2}'.format("select * from ticket where id like '%", month, "%'")
            print(query)
            for row in self.cursor.execute(query):
                _ticket.append(row)
        elif option == 'day':
            day = time.strftime('%d/')
            query = '{0}{1}{2}'.format("select * from ticket where id like '", day, "%'")
            for row in self.cursor.execute(query):
                _ticket.append(row)
        return _ticket

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
        self.price = price
        self.quant = quant

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Foo()
    sys.exit(app.exec_())
