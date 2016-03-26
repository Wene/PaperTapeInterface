#!/usr/bin/env python3

from PyQt5.QtCore import *
from PyQt5.QtSerialPort import *
from PyQt5.QtWidgets import *

class Form(QWidget):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        lay_main = QVBoxLayout(self)
        self.serial_port = QSerialPort()

        # device selection
        lay_connect = QHBoxLayout()
        lay_main.addLayout(lay_connect)
        self.port_selector = QComboBox()
        self.type_selector = QComboBox()
        self.type_selector.addItem("Lochstreifen Leser")
        self.type_selector.addItem("Lochstreifen Stanzer")
        self.btn_connect = QPushButton("Verbinden")
        self.btn_connect.clicked.connect(self.connect_to_serial)
        lay_connect.addWidget(self.port_selector)
        lay_connect.addWidget(self.type_selector)
        lay_connect.addWidget(self.btn_connect)
        lay_connect.addStretch()

        # debugging output
        self.edt_debug = QPlainTextEdit();
        self.edt_debug.setReadOnly(True)
        lay_main.addWidget(self.edt_debug)

        # initialize all the things
        self.fill_port_selector()

        # restore settings
        self.settings = QSettings("Wene", "PaperTapeInterface")
        self.move(self.settings.value("Position", QPoint(10, 10), type=QPoint))
        self.resize(self.settings.value("Size", QSize(100, 100), type=QSize))
        port_index = self.settings.value("Port", type=int)
        if isinstance(port_index, int):
            if self.port_selector.count() > port_index:
                self.port_selector.setCurrentIndex(port_index)
        self.type_selector.setCurrentIndex(self.settings.value("Type", type=int))

    # search for available serial ports and fill the QComboBox
    def fill_port_selector(self):
        self.port_selector.clear()
        self.port_selector.addItem("Port auswählen...")
        port_list = QSerialPortInfo.availablePorts()
        for port in port_list:
            assert isinstance(port, QSerialPortInfo)
            port_name = port.portName() + " (" + port.manufacturer() + " / " + port.description() + ")"
            self.port_selector.addItem(port_name, port)

    def connect_to_serial(self):
        port = self.port_selector.currentData()
        if isinstance(port, QSerialPortInfo):
            self.serial_port.setPort(port)
            self.serial_port.setBaudRate(115200)
            connected = self.serial_port.open(QIODevice.ReadWrite)
            if connected:
                self.edt_debug.appendPlainText("Verbunden")
            else:
                self.edt_debug.appendPlainText("Fehler")
        else:
            self.edt_debug.appendPlainText("kein gültiger Port")

    # save settings
    def closeEvent(self, QCloseEvent):
        self.settings.setValue("Position", self.pos())
        self.settings.setValue("Size", self.size())
        self.serial_port.close()
        self.settings.setValue("Port", self.port_selector.currentIndex())
        self.settings.setValue("Type", self.type_selector.currentIndex())

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    translator = QTranslator()
    lib_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    translator.load("qt_de.qm", lib_path)
    translator.load("qtbase_de.qm", lib_path)
    app.installTranslator(translator)

    window = Form()
    window.show()

    sys.exit(app.exec_())
