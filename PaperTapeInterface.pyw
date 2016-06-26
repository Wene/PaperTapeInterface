#!/usr/bin/env python3

from PyQt5.QtCore import *
from PyQt5.QtSerialPort import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from os import path


class Form(QWidget):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        lay_main = QVBoxLayout(self)
        self.serial_port = QSerialPort()
        self.buffer = bytearray(b'')
        self.reset_needed = False

        self.serial_read_timer = QTimer()
        # 20 ms is the punching interval - 10 ms timeout to be sure, each byte is displayed after one interval
        self.serial_read_timer.setInterval(15)
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

        # Layout for punching mode
        self.stack = QStackedWidget()
        wid_punch = QWidget()
        wid_reader = QWidget()
        lay_punch = QVBoxLayout()
        lay_punch.setContentsMargins(0, 0, 0, 0)
        lay_reader = QGridLayout()
        lay_reader.setContentsMargins(0, 0, 0, 0)
        wid_punch.setLayout(lay_punch)
        wid_reader.setLayout(lay_reader)
        self.stack.addWidget(wid_reader)
        self.stack.addWidget(wid_punch)
        self.type_selector.currentIndexChanged.connect(self.stack.setCurrentIndex)

        # punch file in ASCII with parity bit or binary section
        lay_file = QHBoxLayout()
        lay_main.addLayout(lay_file)
        self.lbl_size = QLabel("Keine Datei ausgewählt")
        lay_main.addWidget(self.lbl_size)
        lay_main.addWidget(self.stack)

        lay_punch_buttons = QHBoxLayout()
        lay_punch.addLayout(lay_punch_buttons)

        # punch human readable text section
        lay_punch_human = QHBoxLayout()
        lay_punch.addLayout(lay_punch_human)
        # lay_main.addLayout(lay_punch_human)
        self.edt_human = QLineEdit()
        self.edt_human.setValidator(QRegExpValidator(QRegExp(r'[A-Za-z0-9\\ !"#$%&\'()*+,-./:;<=>?@{|}~\[\]^_`]*')))
        lay_punch_human.addWidget(self.edt_human)
        self.btn_punch_human = QPushButton("Lesbare Zeichen stanzen")
        self.btn_punch_human.clicked.connect(self.punch_human_readable)
        lay_punch_human.addWidget(self.btn_punch_human)

        self.btn_open = QPushButton("Datei wählen...")
        self.btn_open.clicked.connect(self.open_file)
        lay_file.addWidget(self.btn_open)
        self.edt_filename = QLineEdit()
        self.edt_filename.textChanged.connect(self.update_file_size)
        lay_file.addWidget(self.edt_filename)
        self.btn_punch_ascii = QPushButton("7-Bit ASCII mit Paritätsbit stanzen")
        self.btn_punch_ascii.clicked.connect(self.punch_ascii)
        self.btn_punch_binary = QPushButton("Binärdaten stanzen")
        self.btn_punch_binary.clicked.connect(self.punch_binary)
        self.btn_punch_baudot = QPushButton("5-Bit Baudot stanzen")
        self.btn_punch_baudot.clicked.connect(self.punch_baudot)
        lay_punch_buttons.addWidget(self.btn_punch_ascii)
        lay_punch_buttons.addWidget(self.btn_punch_binary)
        lay_punch_buttons.addWidget(self.btn_punch_baudot)

        # Reader features
        self.btn_read_ascii = QPushButton("7 Bit ASCII lesen")
        self.btn_read_ascii.clicked.connect(self.read_ascii)
        self.btn_read_bin = QPushButton("Binärdaten lesen")
        self.btn_read_bin.clicked.connect(self.read_binary)
        self.btn_read_baudot = QPushButton("5 Bit Baudot Code lesen")
        self.btn_read_baudot.clicked.connect(self.read_baudot)
        self.btn_read_debug = QPushButton("Lesen im Debugging- Modus")
        self.btn_read_debug.clicked.connect(self.read_debug)
        lay_reader.addWidget(self.btn_read_ascii, 1, 0)
        lay_reader.addWidget(self.btn_read_bin, 1, 1)
        lay_reader.addWidget(self.btn_read_baudot, 1, 2)
        lay_reader.addWidget(self.btn_read_debug, 1, 3)
        self.btn_read_to_file = QPushButton("Aufzeichnung in Datei aktivieren (anhängen)")
        self.btn_read_to_file.setCheckable(True)
        self.btn_read_to_file.setChecked(False)
        self.btn_read_to_file.setEnabled(False)
        lay_reader.addWidget(self.btn_read_to_file, 0, 0, 1, 2)
        self.btn_leave_read_mode = QPushButton("Aktuellen Lesemodus verlassen")
        self.btn_leave_read_mode.clicked.connect(self.read_menu)
        self.btn_leave_read_mode.setEnabled(False)
        lay_reader.addWidget(self.btn_leave_read_mode, 0, 2, 1, 2)

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
        pol_debug = self.edt_debug.sizePolicy()
        pol_debug.setVerticalStretch(255)
        self.edt_debug.setSizePolicy(pol_debug)
        dbg_font = self.edt_debug.font()
        dbg_font.setFamily("Courier")
        self.edt_debug.setFont(dbg_font)
        lay_main.addWidget(self.edt_debug)

        # initialize all the things
        self.fill_port_selector()
        self.lock_buttons()

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
        if self.type_selector.currentIndex() == 1:      # punch mode
            filename, _ = QFileDialog.getOpenFileName(self, "Datei auswählen")
        else:
            filename, _ = QFileDialog.getSaveFileName(self, "Datei anlegen")
        if filename != "":
            self.edt_filename.setText(filename)

    def update_file_size(self):
        filename = self.edt_filename.text()
        try:
            size = path.getsize(filename)
            kb_size = size / 1024
            length = (size * 2.54) / 1000
            self.lbl_size.setText("Die Datei ist {:0.2f}".format(kb_size) +
                                  " KiB gross. Das ergibt {:0.2f}".format(length) +
                                  " Meter Lochstreifen.")
        except:
            self.lbl_size.setText("Keine Datei ausgewählt")

    def punch_human_readable(self):
        characters = bytes(self.edt_human.text(), encoding="ascii")
        if len(characters) > 0:
            self.lock_buttons()
            self.reset_needed = True
            self.serial_port.write("h")
            self.serial_port.write(characters)

    def punch_ascii(self):
        filename = self.edt_filename.text()
        if filename != "":
            self.lock_buttons()
            try:
                with open(filename, "rb") as file:
                    data = file.read()
                if self.validate_ascii(data):
                    self.serial_port.write("a")
                    self.serial_port.write(data)
                    self.reset_needed = True
                else:
                    self.edt_debug.appendPlainText("Datei enthält Zeichen die nicht als ASCII gestanzt werden können.")
                    self.unlock_buttons()
            except:
                self.edt_debug.appendPlainText("Fehler beim Lesen der Datei " + filename)
                self.unlock_buttons()

    def punch_binary(self):
        filename = self.edt_filename.text()
        if filename != "":
            self.lock_buttons()
            try:
                with open(filename, "rb") as file:
                    data = file.read()
                self.serial_port.write("b")
                self.serial_port.write(data)
            except:
                self.edt_debug.appendPlainText("Fehler beim Lesen der Datei " + filename)
                self.unlock_buttons()

    def punch_baudot(self):
        filename = self.edt_filename.text()
        if filename != "":
            self.lock_buttons()
            try:
                with open(filename, "rb") as file:
                    data = file.read()
                if self.validate_baudot(data):
                    self.serial_port.write("5")
                    self.serial_port.write(data)
                    self.reset_needed = True
                else:
                    self.edt_debug.appendPlainText("Datei enthält Zeichen die nicht als 5-Bit Baudot gestanzt werden können.")
                    self.unlock_buttons()
            except:
                self.edt_debug.appendPlainText("Fehler beim Leden der Datei " + filename)
                self.unlock_buttons()

    def read_ascii(self):
        self.lock_buttons()
        self.serial_port.write("a")

    def read_binary(self):
        self.lock_buttons()
        self.serial_port.write("b")

    def read_baudot(self):
        self.lock_buttons()
        self.serial_port.write("5")

    def read_debug(self):
        self.lock_buttons()
        self.serial_port.write("d")

    def read_menu(self):
        self.serial_port.write(chr(255))
        self.unlock_buttons()

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
        for byte in data:
            self.buffer.append(byte)
        self.serial_read_timer.start()

    def read_after_connect_proceed(self):
        self.unlock_buttons()
        self.serial_read_timer.timeout.disconnect()
        if self.type_selector.currentIndex() == 0:
            self.serial_read_timer.timeout.connect(self.read_reader_output)
        else:
            self.serial_read_timer.timeout.connect(self.read_puncher_debugging_output)
        if self.btn_simulation_mode.isChecked():
            # turn on simulation mode if inactive
            if b"Toggle (S)imulation mode: currently off" in self.buffer:
                self.serial_port.write("s")
        else:
            # turn off simulation if active
            if b"Toggle (S)imulation mode: currently on" in self.buffer:
                self.serial_port.write("s")
        self.read_puncher_debugging_output()

    def read_puncher_debugging_output(self):
        if 4 in self.buffer:
            self.buffer.remove(4)
            if self.reset_needed:
                self.serial_port.write(chr(255))
                self.reset_needed = False
                self.unlock_buttons()
        if b"Timeout" in self.buffer:
                self.unlock_buttons()
        self.edt_debug.appendPlainText(self.buffer.decode('ascii').rstrip())
        self.buffer.clear()

    def read_reader_output(self):
        filename = self.edt_filename.text()
        if filename != "" and self.btn_read_to_file.isChecked():
            try:
                with open(filename, "ab") as file:
                    file.write(self.buffer)
            except:
                self.edt_debug.appendPlainText("Fehler beim Schreiben der Datei " + filename)
        self.edt_debug.appendPlainText(self.buffer.decode('ascii').rstrip())
        self.buffer.clear()

    def validate_ascii(self, data):
        assert isinstance(data, bytes)
        for byte in data:
            if int(byte) > 127:
                return False
        return True

    def validate_baudot(self, data):
        assert isinstance(data, bytes)
        baudot_nums = list(range(65, 91))       # lowercase letters
        baudot_nums += list(range(97, 123))     # uppercase letters
        baudot_nums += list(range(48, 58))      # numbers
        baudot_nums += list(range(43, 48))      # symbols
        baudot_nums += [13, 10, 32, 5, 7, 63, 58, 61]
        baudot_nums += [40, 41, 60, 62, 123, 125, 91, 93]   # braces
        for byte in data:
            if not int(byte) in baudot_nums:
                return False
        return True

    # save settings
    def closeEvent(self, QCloseEvent):
        self.settings.setValue("Position", self.pos())
        self.settings.setValue("Size", self.size())
        self.serial_port.close()
        self.settings.setValue("Port", self.port_selector.currentIndex())
        self.settings.setValue("Type", self.type_selector.currentIndex())
        self.settings.setValue("Simulation", self.btn_simulation_mode.isChecked())

    def lock_buttons(self):
        self.btn_punch_ascii.setEnabled(False)
        self.btn_punch_binary.setEnabled(False)
        self.btn_punch_human.setEnabled(False)
        self.btn_punch_baudot.setEnabled(False)
        self.btn_read_baudot.setEnabled(False)
        self.btn_read_bin.setEnabled(False)
        self.btn_read_ascii.setEnabled(False)
        self.btn_read_debug.setEnabled(False)

    def unlock_buttons(self):
        self.btn_punch_ascii.setEnabled(True)
        self.btn_punch_binary.setEnabled(True)
        self.btn_punch_human.setEnabled(True)
        self.btn_punch_baudot.setEnabled(True)
        self.btn_read_baudot.setEnabled(True)
        self.btn_read_bin.setEnabled(True)
        self.btn_read_ascii.setEnabled(True)
        self.btn_read_debug.setEnabled(True)
        self.btn_leave_read_mode.setEnabled(True)
        self.btn_read_to_file.setEnabled(True)

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
