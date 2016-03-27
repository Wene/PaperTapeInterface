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

        self.serial_read_timer = QTimer()
        self.serial_read_timer.setInterval(10)
        self.serial_read_timer.setSingleShot(True)
        self.serial_read_timer.timeout.connect(self.read_after_connect_proceed)

        # device selection
        lay_connect = QHBoxLayout()
        lay_main.addLayout(lay_connect)
        self.port_selector = QComboBox()
        self.type_selector = QComboBox()
        self.type_selector.addItem("Lochstreifen Leser")
        self.type_selector.addItem("Lochstreifen Stanzer")
        self.btn_connect = QPushButton("Verbinden")
        self.btn_connect.clicked.connect(self.connect_to_serial)
        self.btn_simulation_mode = QPushButton("Simulationsmodus")
        self.btn_simulation_mode.setCheckable(True)
        self.btn_simulation_mode.setChecked(True)
        lay_connect.addWidget(self.port_selector)
        lay_connect.addWidget(self.type_selector)
        lay_connect.addWidget(self.btn_simulation_mode)
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
        self.btn_punch_human.clicked.connect(self.punch_human_readable)
        lay_punch_human.addWidget(self.btn_punch_human)

        # punch file in ASCII with parity bit or binary section
        lay_punch_file = QHBoxLayout()
        lay_main.addLayout(lay_punch_file)
        self.btn_open = QPushButton("Datei wählen...")
        self.btn_open.clicked.connect(self.open_file)
        lay_punch_file.addWidget(self.btn_open)
        self.edt_filename = QLineEdit()
        lay_punch_file.addWidget(self.edt_filename)
        self.btn_punch_ascii = QPushButton("7-Bit ASCII mit Paritätsbit stanzen")
        self.btn_punch_ascii.clicked.connect(self.punch_ascii)
        self.btn_punch_binary = QPushButton("Binärdaten stanzen")
        self.btn_punch_binary.clicked.connect(self.punch_binary)
        lay_punch_file.addWidget(self.btn_punch_ascii)
        lay_punch_file.addWidget(self.btn_punch_binary)

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
        dbg_font = self.edt_debug.font()
        dbg_font.setFamily("Courier")
        self.edt_debug.setFont(dbg_font)
        lay_main.addWidget(self.edt_debug)

        # initialize all the things
        self.fill_port_selector()
        self.lock_send_buttons()

        # restore settings
        self.settings = QSettings("Wene", "PaperTapeInterface")
        self.move(self.settings.value("Position", QPoint(10, 10), type=QPoint))
        self.resize(self.settings.value("Size", QSize(100, 100), type=QSize))
        port_index = self.settings.value("Port", type=int)
        if isinstance(port_index, int):
            if self.port_selector.count() > port_index:
                self.port_selector.setCurrentIndex(port_index)
        self.type_selector.setCurrentIndex(self.settings.value("Type", type=int))
        self.btn_simulation_mode.setChecked(self.settings.value("Simulation", type=bool))

    # open file for punching
    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Datei auswählen")
        if filename != "":
            self.edt_filename.setText(filename)

    def punch_human_readable(self):
        self.lock_send_buttons()
        self.serial_port.write("h")
        characters = bytes(self.edt_human.text(), encoding="ascii")   # TODO: find a way to ignore non ASCII characters
        self.serial_port.write(characters)

    def punch_ascii(self):
        self.lock_send_buttons()
        self.serial_port.write("a")

    def punch_binary(self):
        filename = self.edt_filename.text()
        if filename != "":
            try:
                self.lock_send_buttons()
                with open(filename, "rb") as file:
                    data = chr("b")
                    while data != "":
                        self.serial_port.write(data)
                        data = file.read(1)
            except:
                self.edt_debug.appendPlainText("Fehler")
            self.unlock_send_buttons()

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
                self.btn_simulation_mode.setEnabled(False)
                self.serial_port.readyRead.connect(self.serial_read)
                self.serial_port.write(chr(255))     # send something to get the menu
            else:
                self.edt_debug.appendPlainText("Fehler")
        else:
            self.edt_debug.appendPlainText("kein gültiger Port")

    # This slot is called whenever new data is available for read.
    def serial_read(self):
        data = self.serial_port.read(self.serial_port.bytesAvailable())
        assert isinstance(data, bytes)
        for character in data:
            self.buffer += str(chr(character))
        self.serial_read_timer.start()

    def read_after_connect_proceed(self):
        self.unlock_send_buttons()
        self.serial_read_timer.timeout.disconnect()
        self.serial_read_timer.timeout.connect(self.read_debugging_output)
        if self.btn_simulation_mode.isChecked():
            # turn on simulation mode if inactive
            if "Toggle (S)imulation mode: currently off" in self.buffer:
                self.serial_port.write("s")
        else:
            # turn off simulation if active
            if "Toggle (S)imulation mode: currently on" in self.buffer:
                self.serial_port.write("s")
        self.read_debugging_output()

    def read_debugging_output(self):
        if chr(4) in self.buffer:
            self.buffer = self.buffer.replace(chr(4), "")
            self.serial_port.write(chr(255))
            self.unlock_send_buttons()
        self.edt_debug.appendPlainText(self.buffer.rstrip())
        self.buffer = ""

    # save settings
    def closeEvent(self, QCloseEvent):
        self.settings.setValue("Position", self.pos())
        self.settings.setValue("Size", self.size())
        self.serial_port.close()
        self.settings.setValue("Port", self.port_selector.currentIndex())
        self.settings.setValue("Type", self.type_selector.currentIndex())
        self.settings.setValue("Simulation", self.btn_simulation_mode.isChecked())

    def lock_send_buttons(self):
        self.btn_punch_ascii.setEnabled(False)
        self.btn_punch_binary.setEnabled(False)
        self.btn_punch_human.setEnabled(False)

    def unlock_send_buttons(self):
        self.btn_punch_ascii.setEnabled(True)
        self.btn_punch_binary.setEnabled(True)
        self.btn_punch_human.setEnabled(True)

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
