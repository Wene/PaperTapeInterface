#!/usr/bin/env python3

from PyQt5.QtCore import *
from PyQt5.QtSerialPort import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QFrame


class Form(QWidget):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        lay_main = QVBoxLayout(self)
        self.serial_port = QSerialPort()
        self.buffer = ""

        self.read_timer = QTimer()
        self.read_timer.setInterval(10)
        self.read_timer.setSingleShot(True)
        self.read_timer.timeout.connect(self.read_proceed)

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

        # horizontal line
        self.h_line_1 = QFrame()
        self.h_line_1.setLineWidth(3)
        self.h_line_1.setFrameStyle(QFrame.HLine)
        self.h_line_1.setFrameShadow(QFrame.Sunken)
        lay_main.addWidget(self.h_line_1)

        # punch human readable text section
        lay_punch_human = QHBoxLayout()
        lay_main.addLayout(lay_punch_human)
        self.edt_human = QLineEdit()
        lay_punch_human.addWidget(self.edt_human)
        self.btn_punch_human = QPushButton("Lesbare Zeichen stanzen")

        # punch file in ASCII with parity bit or binary section
        lay_punch_file = QHBoxLayout()
        lay_main.addLayout(lay_punch_file)
        self.btn_open = QPushButton("Datei wählen...")
        self.btn_open.clicked.connect(self.open_file)
        lay_punch_file.addWidget(self.btn_open)
        self.edt_filename = QLineEdit()
        lay_punch_file.addWidget(self.edt_filename)
        self.btn_punch_ascii = QPushButton("7-Bit ASCII mit Paritätsbit stanzen")
        self.btn_punch_binary = QPushButton("Binärdaten stanzen")
        lay_punch_file.addWidget(self.btn_punch_ascii)
        lay_punch_file.addWidget(self.btn_punch_binary)
        lay_punch_human.addWidget(self.btn_punch_human)

        # horizontal line
        self.h_line_2 = QFrame()
        self.h_line_2.setLineWidth(3)
        self.h_line_2.setFrameStyle(QFrame.HLine)
        self.h_line_2.setFrameShadow(QFrame.Sunken)
        lay_main.addWidget(self.h_line_2)

        # debugging output
        self.lbl_debug = QLabel("Debugging Ausgabe:")
        lay_main.addWidget(self.lbl_debug)
        self.edt_debug = QPlainTextEdit()
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

    # open file for punching
    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Datei auswählen")
        if filename != "":
            self.edt_filename.setText(filename)

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
            self.serial_port.setFlowControl(QSerialPort.SoftwareControl)
            connected = self.serial_port.open(QIODevice.ReadWrite)
            if connected:
                self.edt_debug.appendPlainText("Verbunden")
                self.btn_connect.setEnabled(False)
                self.type_selector.setEnabled(False)
                self.port_selector.setEnabled(False)
                self.serial_port.readyRead.connect(self.read_serial)
                self.serial_port.write(chr(255))     # send something to get the menu
            else:
                self.edt_debug.appendPlainText("Fehler")
        else:
            self.edt_debug.appendPlainText("kein gültiger Port")

    # This slot is called whenever new data is available for read.
    def read_serial(self):
        data = self.serial_port.read(self.serial_port.bytesAvailable())
        assert isinstance(data, bytes)
        for character in data:
            self.buffer += str(chr(character))
        self.read_timer.start()

    def read_proceed(self):
        self.edt_debug.appendPlainText(self.buffer)
        self.buffer = ""

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
