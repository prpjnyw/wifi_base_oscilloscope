# 15/3/2025
#1072 lack of vmax label,vmin label, ... and mates

from trigger import *
from enum import Enum
import time, socket, sys
import numpy as np
import numpy as np, math
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator, MultipleLocator
from matplotlib.widgets import Cursor 
from scipy.fft import fft, fftfreq
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *

# from Out_Data import data as test_data, t as test_t, sampling_t as test_sampling_t #FOR TESTING
# Default
BUF_SIZE = 2048
SERVER_PORT = 4242
# dc_ref = 1.663 
dc_ref = 1.0
sampling_t = 30e-6 

class Domain(Enum):
    TIME = 0
    FREQ = 1


class MPL_canvas(FigureCanvas):
    def __init__(self, parent=None):
        # Graph Config
        width = 10 #inch
        height = 6 #inch
        dpi = 100

        fig = Figure(figsize=(width,height),dpi=dpi)
        self.ax = fig.add_subplot(111)
        super().__init__(fig)

        fig.subplots_adjust(top=0.95, bottom=0.05, left=0.03, right=0.96)
        #self.setFixedSize(width*dpi,height*dpi)

class Thread(QThread):
    result = Signal(list)
    sock = socket.socket()
    SERVER_ADDR = "192.168.4.1"
    addr = (SERVER_ADDR, SERVER_PORT)
    sock.connect(addr)
    
    n = 0 
    dump = []

    @Slot()
    def run(self):
        self.data = None
        self.is_running = True
        print("Thread start")

        while self.is_running:
            total_size = BUF_SIZE
            read_buf = b""
            while total_size > 0:
                buf = self.sock.recv(BUF_SIZE)
                total_size -= len(buf)
                read_buf += buf;
    
            # Check size of data received
            if len(read_buf) != BUF_SIZE:
                raise RuntimeError("wrong amount of data read %d", len(read_buf))
    
            self.n += 1
            spec_len = 700
            set_dump_storage(self.dump, read_buf)
            self.dump = [round(i - dc_ref,5)   for i in self.dump]
            ti = trgIndexRis(self.dump)
            tmp = self.dump[ti:ti + spec_len]
            self.result.emit(tmp)

            tmp.clear()  
            self.dump.clear()
            self.dump = []

            sampling_fmt_b = bytes(f"t{int(sampling_t * 1e6)}", "ascii")
            self.sock.send(sampling_fmt_b)
            # print(sampling_t)
            # print(sampling_fmt_b)

    def send_data(self, data):
        self.data = data

class Style(Enum):

    lineEdit_width = 70
    button_width = 60
    button_width_2 = 40
    dial_width = 90
    vh_width = 160
    vh_height = 300
    measure_height = 120

    square_button = 30

    head_style = """
            font-size: 15px;
            font: bold;
        """

    label_style_normal = """
            font-size: 10px;
        """

    label_style_bold = """
            font-size: 10px;
            font: bold;
        """

    lineEdit_style = """
            background-color: rgb(49, 51, 56);
            border-width: 1px;
            border-style: solid;
            border-color: rgb(10,10,10);
            border-radius: 5px;
        """

    line_style = """
                background-color: rgb(49, 51, 56);
                border-width: 1px;
            """

    dial_style = """
            QDial {
                background: #dbdee1;
            }
            QDial:handle {
            }
        """
    frame_style = """
            background-color: rgb(35, 36, 40);
            border-radius: 10px;
        """
    button_style_2 = """
            QPushButton {
                font-size: 20px;
                background-color: rgb(76,76,76);
                border-width: 1px;
                border-style: solid;
                border-color: rgb(10, 10, 10);
                border-radius: 5px;
                color: rgb(231, 72, 86);
                font-weight: 700;
                padding-bottom: 5px;
            }
            QPushButton:hover {
                font-size: 20px;
                background-color: rgb(69,69,69);
                border-width: 1px;
                border-style: solid;
                border-color: rgb(10, 10, 10);
                border-radius: 5px;
                color: rgb(231, 72, 86);
                font-weight: 700;
                padding-bottom: 5px;
            }
            QPushButton:pressed {
                font-size: 20px;
                background-color: rgb(58,58,58);
                border-width: 1px;
                border-style: solid;
                border-color: rgb(10, 10, 10);
                border-radius: 5px;
                color: rgb(178,57,69);
                font-weight: 900;
                padding-bottom: 5px;
            }
        """

    button_style = """
            QPushButton {
                background-color: rgb(76,76,76);
                border-width: 1px;
                border-style: solid;
                border-color: rgb(10, 10, 10);
                border-radius: 5px;
                color: rgb(231, 72, 86);
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: rgb(69,69,69);
                border-width: 1px;
                border-style: solid;
                border-color: rgb(10, 10, 10);
                border-radius: 5px;
                color: rgb(231, 72, 86);
                font-weight: 700;
            }
            QPushButton:pressed {
                background-color: rgb(58,58,58);
                border-width: 1px;
                border-style: solid;
                border-color: rgb(10, 10, 10);
                border-radius: 5px;
                color: rgb(178,57,69);
                font-weight: 900;
            }
        """

class Main(QMainWindow):

    def __init__(self):
        super().__init__()

        #time-side frame
        self.vmax_label = QLabel("Vmax : -- mV")
        self.vmin_label = QLabel("Vmin : -- mV")
        self.vpp_label = QLabel("Vpp : -- V")
        self.vrms_label = QLabel("Vrms : -- mV")
        self.vavg_label = QLabel("Vavg : -- mV")
        self.period_label = QLabel("Period : -- μs")
        self.freq_label = QLabel("Freq : -- Hz")

        # config
        self.time_div_scales = [
            1e-9, 2e-9, 5e-9,  # 1 ns, 2 ns, 5 ns
            10e-9, 20e-9, 50e-9,  # 10 ns, 20 ns, 50 ns
            100e-9, 200e-9, 500e-9,  # 100 ns, 200 ns, 500 ns
            1e-6, 2e-6, 5e-6,  # 1 µs, 2 µs, 5 µs
            10e-6, 20e-6, 50e-6,  # 10 µs, 20 µs, 50 µs
            100e-6, 200e-6, 500e-6,  # 100 µs, 200 µs, 500 µs
            1e-3, 2e-3, 5e-3,  # 1 ms, 2 ms, 5 ms
            10e-3, 20e-3, 50e-3,  # 10 ms, 20 ms, 50 ms
            100e-3, 200e-3, 500e-3,  # 100 ms, 200 ms, 500 ms
            1.0, 2.0, 5.0,  # 1 s, 2 s, 5 s
            10.0, 20.0, 50.0  # 10 s, 20 s, 50 s
        ]
        
        self.volt_div_scales = [
            1e-3,2e-3, 5e-3, # 1 ms, 2 ms, 5 ms
            10e-3, 20e-3, 50e-3, # 10 ms, 20 ms, 50 ms
            0.1, 0.2, 0.5, # 100 ms, 200 ms, 500 ms
            1.0, 2.0, 5.0,
            10.0
        ]

        self.domain = Domain.TIME
        self.samples = 700
        self.division = 8
        self.sample_per_div = 100
        # self.time_base = (self.samples * sampling_t) / self.division

        self.time_per_div = self.time_div_scales[22]
        range_t_max = (self.samples * sampling_t)/2
        self.t = np.arange(-range_t_max, range_t_max, sampling_t)
        self.v = np.array([0.0] * len(self.t))
        # self.y_max = 4
        self.volt_per_div = self.volt_div_scales[10]

        
        #run other thread
        self.thread = Thread()
        self.thread.start()
        self.thread.result.connect(self.process_data_from_thread)
        
        self.volt_offset = 0.0
        self.time_offset = 0.0

        self.plot_ref = None
        self.x1 = -2 * self.time_per_div
        self.x2 = 2 * self.time_per_div
        self.y1 = -2 * self.volt_per_div
        self.y2 = 2 * self.volt_per_div

        self.creat_main_gui()
        self.setStyleSheet("color: white;")

    # GUI--------------------------------------------------------------------

    def creat_main_gui(self):
        self.setWindowTitle("OSCII v2.0 (beta)") #OSCII not ASCII [ONA]
        self.setBaseSize(QSize(1000,500))
        self.setStyleSheet("background-color: rgb(49, 51, 56);")
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QGridLayout()
        main_widget.setLayout(main_layout)

        self.graph_frame = self.creat_graph_gui()
        self.run_and_connect_frame = self.creat_run_and_connect_gui()
        self.domain_changes_frame = self.creat_domain_changes_gui()
        self.address_input_frame = self.creat_address_input_gui()
        self.channel_controls_frame = self.creat_channel_controls_gui()
        self.horizontal_controls_frame = self.creat_horizontal_controls_gui()
        self.measure_frame = self.creat_measure_gui()
        self.cursor_controls_frame = self.creat_cursor_controls_gui()

        main_layout.addWidget(self.canvas,0,0,4,2)
        main_layout.addWidget(self.run_and_connect_frame,0,2,1,4)
        main_layout.addWidget(self.domain_changes_frame,1,2,1,2)
        main_layout.addWidget(self.address_input_frame,1,4,1,2)
        main_layout.addWidget(self.channel_controls_frame,2,2,1,2)
        main_layout.addWidget(self.horizontal_controls_frame,2,4,1,2)
        main_layout.addWidget(self.measure_frame,4,0,1,2)
        main_layout.addWidget(self.cursor_controls_frame,3,2,2,4)


        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)
        main_layout.setColumnStretch(2, 0)
        main_layout.setColumnStretch(3, 0)
        main_layout.setColumnStretch(4, 0)

        main_layout.setRowStretch(0, 1)
        main_layout.setRowStretch(1, 0)
        main_layout.setRowStretch(2, 0)
        main_layout.setRowStretch(3, 0) 
        main_layout.setRowStretch(4, 0)  
        main_layout.setRowStretch(5, 0)
        main_layout.setRowStretch(6, 0)
        main_layout.setRowStretch(7, 0)
        main_layout.setRowStretch(8, 0)

        #self.showMaximized()

    def creat_graph_gui(self):
        self.canvas = MPL_canvas(self)

        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def creat_run_and_connect_gui(self):
        frame = QFrame()
        frame.setStyleSheet(Style.frame_style.value)
        layout = QGridLayout(frame)

        self.run_button = QPushButton("Paused")
        self.run_button.setFixedHeight(30)
        self.run_button.setStyleSheet(Style.button_style.value)
        self.run_button.setCheckable(True)
        self.run_button.setChecked(False)
        self.run_button.clicked.connect(lambda value: self.run_pause_click(value))

        self.connect_button = QPushButton("Disconnected")
        self.connect_button.setFixedHeight(30)
        self.connect_button.setStyleSheet(Style.button_style.value)
        self.connect_button.setCheckable(True)
        self.connect_button.setChecked(False)
        self.connect_button.clicked.connect(lambda value: self.connect_click(value))

        layout.addWidget(self.run_button,0,0,1,1)
        layout.addWidget(self.connect_button,0,1,1,3)

        return frame
    
    def creat_domain_changes_gui(self):
        frame = QFrame()
        frame.setStyleSheet(Style.frame_style.value)
        layout = QGridLayout(frame)

        head_label = QLabel("Domain")
        head_label.setStyleSheet(Style.head_style.value)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(Style.line_style.value)

        self.time_button = QPushButton("Time")
        self.time_button.setStyleSheet(Style.button_style.value)
        self.time_button.clicked.connect(lambda value,domain=Domain.TIME: self.change_domain(value,domain))

        self.freq_button = QPushButton("Frequency")
        self.freq_button.setStyleSheet(Style.button_style.value)
        self.freq_button.clicked.connect(lambda value,domain=Domain.FREQ: self.change_domain(value,domain))
        
        layout.addWidget(head_label,0,0,1,1)
        layout.addWidget(line,1,0,1,1)
        layout.addWidget(self.time_button,2,0,1,1)
        layout.addWidget(self.freq_button,3,0,1,1)

        return frame

    def creat_address_input_gui(self):
        frame = QFrame()
        frame.setStyleSheet(Style.frame_style.value)
        layout = QGridLayout(frame)

        head_label = QLabel("Address")
        head_label.setStyleSheet(Style.head_style.value)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(Style.line_style.value)

        ip_label = QLabel("IP:")
        ip_label.setStyleSheet(Style.label_style_bold.value)
        port_label = QLabel("Port:")
        port_label.setStyleSheet(Style.label_style_bold.value)

        self.ip_lineEdit = QLineEdit()
        self.ip_lineEdit.setStyleSheet(Style.lineEdit_style.value)
        self.ip_lineEdit.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.ip_lineEdit.editingFinished.connect(lambda lineEdit=self.ip_lineEdit: self.address_enter(lineEdit))

        self.port_lineEdit = QLineEdit()
        self.port_lineEdit.setStyleSheet(Style.lineEdit_style.value)
        self.port_lineEdit.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.port_lineEdit.editingFinished.connect(lambda lineEdit=self.port_lineEdit: self.address_enter(lineEdit))

        layout.addWidget(head_label,0,0,1,2)
        layout.addWidget(line,1,0,1,2)
        layout.addWidget(ip_label,2,0)
        layout.addWidget(port_label,3,0)
        layout.addWidget(self.ip_lineEdit,2,1)
        layout.addWidget(self.port_lineEdit,3,1)

        return frame

    def creat_channel_controls_gui(self):
        frame = QFrame()
        frame.setStyleSheet(Style.frame_style.value)
        frame.setFixedHeight(Style.vh_height.value)
        frame.setFixedWidth(Style.vh_width.value)
        layout = QGridLayout(frame)

        head_label = QLabel("Vertical")
        head_label.setStyleSheet(Style.head_style.value)

        div_label = QLabel(f"Volt/Div:")
        div_label.setStyleSheet(Style.label_style_bold.value)

        offset_label = QLabel(f"Offset:")
        offset_label.setStyleSheet(Style.label_style_bold.value)

        self.volt_div_lineEdit = QLineEdit(f"{self.unit_prefix(self.volt_per_div)}V")
        self.volt_div_lineEdit.setObjectName("volt div")
        self.volt_div_lineEdit.setStyleSheet(Style.lineEdit_style.value)
        self.volt_div_lineEdit.setFixedWidth(Style.lineEdit_width.value)
        self.volt_div_lineEdit.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.volt_div_lineEdit.editingFinished.connect(lambda lineEdit=self.volt_div_lineEdit: self.volt_time_lineEdit_enter(lineEdit))

        self.volt_offset_lineEdit = QLineEdit(f"{self.unit_prefix(self.volt_offset)}V")
        self.volt_offset_lineEdit.setObjectName("volt offset")
        self.volt_offset_lineEdit.setStyleSheet(Style.lineEdit_style.value)
        self.volt_offset_lineEdit.setFixedWidth(Style.lineEdit_width.value)
        self.volt_offset_lineEdit.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.volt_offset_lineEdit.editingFinished.connect(lambda lineEdit=self.volt_offset_lineEdit: self.volt_time_lineEdit_enter(lineEdit))

        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet(Style.line_style.value)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet(Style.line_style.value)

        self.volt_div_dial = QDial()
        self.volt_div_dial.setObjectName("volt div")
        self.volt_div_dial.setRange(0,len(self.volt_div_scales) - 1)
        self.volt_div_dial.setValue(self.volt_div_scales.index(self.volt_per_div))
        self.volt_div_dial.setNotchesVisible(True)
        self.volt_div_dial.setFixedHeight(Style.dial_width.value)
        self.volt_div_dial.setStyleSheet(Style.dial_style.value)
        self.volt_div_dial.valueChanged.connect(lambda value, dial=self.volt_div_dial: self.volt_time_dial_change(value,dial))

        volt_max_range = int(self.division * self.sample_per_div /4) * 2

        self.volt_offset_dial = QDial()
        self.volt_offset_dial.setObjectName("volt offset")
        self.volt_offset_dial.setRange(-volt_max_range,volt_max_range)
        self.volt_offset_dial.setFixedHeight(Style.dial_width.value)
        self.volt_offset_dial.setStyleSheet(Style.dial_style.value)
        self.volt_offset_dial.valueChanged.connect(lambda value, dial=self.volt_offset_dial: self.volt_time_dial_change(value,dial))

        volt_reset_button = QPushButton("RESET")
        volt_reset_button.setStyleSheet(Style.button_style.value)
        volt_reset_button.setFixedWidth(Style.button_width.value)
        volt_reset_button.clicked.connect(lambda value,button="volt": self.volt_time_reset_click(value,button))

        volt_div_up_button = QPushButton("+")
        volt_div_up_button.setStyleSheet(Style.button_style_2.value)
        volt_div_up_button.setFixedSize(Style.square_button.value,Style.square_button.value)
        volt_div_up_button.clicked.connect(lambda value,button="+ volt div": self.volt_time_fine_click(value,button))

        volt_div_down_button = QPushButton("-")
        volt_div_down_button.setStyleSheet(Style.button_style_2.value)
        volt_div_down_button.setFixedSize(Style.square_button.value,Style.square_button.value)
        volt_div_down_button.clicked.connect(lambda value,button="- volt div": self.volt_time_fine_click(value,button))

        volt_offset_up_button = QPushButton("+")
        volt_offset_up_button.setStyleSheet(Style.button_style_2.value)
        volt_offset_up_button.setFixedSize(Style.square_button.value,Style.square_button.value)
        volt_offset_up_button.clicked.connect(lambda value,button="+ volt off": self.volt_time_fine_click(value,button))

        volt_offset_down_button = QPushButton("-")
        volt_offset_down_button.setStyleSheet(Style.button_style_2.value)
        volt_offset_down_button.setFixedSize(Style.square_button.value,Style.square_button.value)
        volt_offset_down_button.clicked.connect(lambda value,button="- volt off": self.volt_time_fine_click(value,button))

        layout.addWidget(head_label,0,0,1,2)
        layout.addWidget(volt_reset_button,0,1,1,1,alignment=(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight))
        layout.addWidget(line1,1,0,1,0,alignment=(Qt.AlignmentFlag.AlignTop))
        layout.addWidget(div_label,2,0,1,1)
        layout.addWidget(self.volt_div_lineEdit,2,1)
        layout.addWidget(self.volt_div_dial,3,0,2,2,alignment=(Qt.AlignmentFlag.AlignLeft))
        layout.addWidget(volt_div_up_button,3,1,1,1,alignment=(Qt.AlignmentFlag.AlignRight))
        layout.addWidget(volt_div_down_button,4,1,1,1,alignment=(Qt.AlignmentFlag.AlignRight))
        layout.addWidget(line2,5,0,1,0,alignment=(Qt.AlignmentFlag.AlignTop))
        layout.addWidget(offset_label,6,0)
        layout.addWidget(self.volt_offset_lineEdit,6,1)
        layout.addWidget(self.volt_offset_dial,8,0,2,0,alignment=(Qt.AlignmentFlag.AlignLeft))
        layout.addWidget(volt_offset_up_button,8,1,1,1,alignment=(Qt.AlignmentFlag.AlignRight))
        layout.addWidget(volt_offset_down_button,9,1,1,1,alignment=(Qt.AlignmentFlag.AlignRight))

        return frame

    def creat_horizontal_controls_gui(self):
        frame = QFrame()
        frame.setStyleSheet(Style.frame_style.value)
        frame.setFixedHeight(Style.vh_height.value)
        frame.setFixedWidth(Style.vh_width.value)
        layout = QGridLayout(frame)

        head_label = QLabel("Horizontal")
        head_label.setStyleSheet(Style.head_style.value)

        div_label = QLabel(f"Time/Div:")
        div_label.setStyleSheet(Style.label_style_bold.value)

        offset_label = QLabel(f"Offset:")
        offset_label.setStyleSheet(Style.label_style_bold.value)

        self.time_div_lineEdit = QLineEdit(f"{self.unit_prefix(self.time_per_div)}s")
        self.time_div_lineEdit.setObjectName("time div")
        self.time_div_lineEdit.setStyleSheet(Style.lineEdit_style.value)
        self.time_div_lineEdit.setFixedWidth(Style.lineEdit_width.value)
        self.time_div_lineEdit.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.time_div_lineEdit.editingFinished.connect(lambda lineEdit=self.time_div_lineEdit: self.volt_time_lineEdit_enter(lineEdit))

        self.time_offset_lineEdit = QLineEdit(f"{self.unit_prefix(self.time_offset)}s")
        self.time_offset_lineEdit.setObjectName("time offset")
        self.time_offset_lineEdit.setStyleSheet(Style.lineEdit_style.value)
        self.time_offset_lineEdit.setFixedWidth(Style.lineEdit_width.value)
        self.time_offset_lineEdit.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.time_offset_lineEdit.editingFinished.connect(lambda lineEdit=self.time_offset_lineEdit: self.volt_time_lineEdit_enter(lineEdit))

        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet(Style.line_style.value)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet(Style.line_style.value)

        self.time_div_dial = QDial()
        self.time_div_dial.setObjectName("time div")
        self.time_div_dial.setRange(0,len(self.time_div_scales) - 1)
        self.time_div_dial.setValue(self.time_div_scales.index(self.time_per_div))
        self.time_div_dial.setNotchesVisible(True)
        self.time_div_dial.setFixedHeight(Style.dial_width.value)
        self.time_div_dial.setStyleSheet(Style.dial_style.value)
        self.time_div_dial.valueChanged.connect(lambda value, dial=self.time_div_dial: self.volt_time_dial_change(value,dial))

        time_max_range = self.division * self.sample_per_div

        self.time_offset_dial = QDial()
        self.time_offset_dial.setObjectName("time offset")
        self.time_offset_dial.setRange(-time_max_range,time_max_range)
        self.time_offset_dial.setFixedHeight(Style.dial_width.value)
        self.time_offset_dial.setStyleSheet(Style.dial_style.value)
        self.time_offset_dial.valueChanged.connect(lambda value, dial=self.time_offset_dial: self.volt_time_dial_change(value,dial))

        time_reset_button = QPushButton("RESET")
        time_reset_button.setStyleSheet(Style.button_style.value)
        time_reset_button.setFixedWidth(Style.button_width.value)
        time_reset_button.clicked.connect(lambda value,button="time": self.volt_time_reset_click(value,button))

        time_div_up_button = QPushButton("+")
        time_div_up_button.setStyleSheet(Style.button_style_2.value)
        time_div_up_button.setFixedSize(Style.square_button.value,Style.square_button.value)
        time_div_up_button.clicked.connect(lambda value,button="+ time div": self.volt_time_fine_click(value,button))

        time_div_down_button = QPushButton("-")
        time_div_down_button.setStyleSheet(Style.button_style_2.value)
        time_div_down_button.setFixedSize(Style.square_button.value,Style.square_button.value)
        time_div_down_button.clicked.connect(lambda value,button="- time div": self.volt_time_fine_click(value,button))

        time_offset_up_button = QPushButton("+")
        time_offset_up_button.setStyleSheet(Style.button_style_2.value)
        time_offset_up_button.setFixedSize(Style.square_button.value,Style.square_button.value)
        time_offset_up_button.clicked.connect(lambda value,button="+ time off": self.volt_time_fine_click(value,button))

        time_offset_down_button = QPushButton("-")
        time_offset_down_button.setStyleSheet(Style.button_style_2.value)
        time_offset_down_button.setFixedSize(Style.square_button.value,Style.square_button.value)
        time_offset_down_button.clicked.connect(lambda value,button="- time off": self.volt_time_fine_click(value,button))

        layout.addWidget(head_label,0,0,1,2)
        layout.addWidget(time_reset_button,0,1,1,1,alignment=(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight))
        layout.addWidget(line1,1,0,1,0,alignment=(Qt.AlignmentFlag.AlignTop))
        layout.addWidget(div_label,2,0,1,1)
        layout.addWidget(self.time_div_lineEdit,2,1)
        layout.addWidget(self.time_div_dial,3,0,2,2,alignment=(Qt.AlignmentFlag.AlignLeft))
        layout.addWidget(time_div_up_button,3,1,1,1,alignment=(Qt.AlignmentFlag.AlignRight))
        layout.addWidget(time_div_down_button,4,1,1,1,alignment=(Qt.AlignmentFlag.AlignRight))
        layout.addWidget(line2,5,0,1,0,alignment=(Qt.AlignmentFlag.AlignTop))
        layout.addWidget(offset_label,6,0)
        layout.addWidget(self.time_offset_lineEdit,6,1)
        layout.addWidget(self.time_offset_dial,8,0,2,0,alignment=(Qt.AlignmentFlag.AlignLeft))
        layout.addWidget(time_offset_up_button,8,1,1,1,alignment=(Qt.AlignmentFlag.AlignRight))
        layout.addWidget(time_offset_down_button,9,1,1,1,alignment=(Qt.AlignmentFlag.AlignRight))

        return frame

    def creat_measure_gui(self):

        frame = QFrame()
        frame.setStyleSheet(Style.frame_style.value)
        frame.setFixedHeight(Style.measure_height.value)
        layout = QGridLayout(frame)

        head_label = QLabel("Measure")
        head_label.setStyleSheet(Style.head_style.value)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(Style.line_style.value)

        time_domain_parameters = ["Vmax","Vmin","Vpp","Vrms","Vavg","Period","Freq"]
        cursor_parameters = ["X1","X2","ΔX","Y1","Y2","ΔY"]

        parameter_label = {}
        self.measure_output_label = {}

        row = 0
        column = 0

        for i in range(len(time_domain_parameters)):
            row = i+2
            column = 0

            if i >= 4:
                row = row - 4
                column = column + 2

            parameter_label[time_domain_parameters[i]] = QLabel(f"{time_domain_parameters[i]} =")
            parameter_label[time_domain_parameters[i]].setStyleSheet(Style.label_style_bold.value)
            layout.addWidget(parameter_label[time_domain_parameters[i]],row,column,alignment=(Qt.AlignmentFlag.AlignRight))

            if "V" in time_domain_parameters[i]:
                unit = "V"
            elif time_domain_parameters[i] == "Period":
                unit = "s"
            elif time_domain_parameters[i] == "Freq":
                unit = "Hz"

            self.measure_output_label[time_domain_parameters[i]] = QLabel(f"-- {unit}")
            self.measure_output_label[time_domain_parameters[i]].setStyleSheet(Style.label_style_normal.value)
            layout.addWidget(self.measure_output_label[time_domain_parameters[i]],row,column+1,alignment=(Qt.AlignmentFlag.AlignRight))


        parameter_label["THD"] = QLabel("THD =")
        parameter_label["THD"].setStyleSheet(Style.label_style_bold.value)
        layout.addWidget(parameter_label["THD"],2,4,alignment=(Qt.AlignmentFlag.AlignRight))

        self.measure_output_label["THD"] = QLabel("--")
        self.measure_output_label["THD"].setStyleSheet(Style.label_style_normal.value)
        layout.addWidget(self.measure_output_label["THD"],2,5,alignment=(Qt.AlignmentFlag.AlignRight))

        for i in range(len(cursor_parameters)):
            row = i+2
            column = 6

            if i >= 3:
                row = row - 3
                column = column + 2

            parameter_label[cursor_parameters[i]] = QLabel(f"{cursor_parameters[i]} =")
            parameter_label[cursor_parameters[i]].setStyleSheet(Style.label_style_bold.value)
            layout.addWidget(parameter_label[cursor_parameters[i]],row,column,alignment=(Qt.AlignmentFlag.AlignRight))

            if "X" in cursor_parameters[i]:
                unit = "s"
            elif "Y" in cursor_parameters[i]:
                unit = "V"

            self.measure_output_label[cursor_parameters[i]] = QLabel(f"-- {unit}")
            self.measure_output_label[cursor_parameters[i]].setStyleSheet(Style.label_style_normal.value)
            layout.addWidget(self.measure_output_label[cursor_parameters[i]],row,column+1,alignment=(Qt.AlignmentFlag.AlignRight))

        layout.addWidget(head_label,0,0,1,0)
        layout.addWidget(line,1,0,1,0)


        return frame

    def creat_cursor_controls_gui(self):
        frame = QFrame()
        frame.setStyleSheet(Style.frame_style.value)
        frame.setFixedHeight(Style.vh_height.value)
        layout = QGridLayout(frame)

        head_label = QLabel("Cursor")
        head_label.setStyleSheet(Style.head_style.value)

        parameters = ["X1","X2","Y1","Y2"]
        max_range = self.sample_per_div * self.division

        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet(Style.line_style.value)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet(Style.line_style.value)

        invisible_line = QFrame()
        invisible_line.setFixedWidth(10)

        cursor_reset_button = QPushButton("RESET")
        cursor_reset_button.setStyleSheet(Style.button_style.value)
        cursor_reset_button.setFixedWidth(Style.button_width.value)
        cursor_reset_button.clicked.connect(lambda value: self.cursor_reset_click(value))

        label = {}
        self.cursor_lineEdit = {}
        self.cursor_dial = {}
        cursor_fine_button = {}
        self.cursor_enable_button = {}

        for name in parameters:
            label[name] = QLabel(f"{name}:")
            label[name].setStyleSheet(Style.label_style_bold.value)

            if "X" in name:
                unit = "s"
                per_div = self.time_per_div
                row = 2
            else:
                unit = "V"
                per_div = self.volt_per_div
                row = 6

            if "1" in name:
                set_value = -2 * per_div
                column = 0
            else:
                set_value = 2 * per_div
                column = 4

            self.cursor_lineEdit[name] = QLineEdit(f"{self.unit_prefix(set_value)}{unit}")
            self.cursor_lineEdit[name].setStyleSheet(Style.lineEdit_style.value)
            self.cursor_lineEdit[name].setFixedWidth(Style.lineEdit_width.value)
            self.cursor_lineEdit[name].setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            self.cursor_lineEdit[name].editingFinished.connect(lambda lineEdit=name: self.cursor_lineEdit_enter(lineEdit))

            self.cursor_dial[name] = QDial()
            self.cursor_dial[name].setRange(-max_range,max_range)

            max_range = int(self.sample_per_div * self.division / 2)
            dial_position = int((set_value*self.sample_per_div)/(per_div))

            self.cursor_dial[name].setRange(-max_range,max_range)
            self.cursor_dial[name].setValue(dial_position)
            self.cursor_dial[name].setFixedHeight(Style.dial_width.value)
            self.cursor_dial[name].setStyleSheet(Style.dial_style.value)
            self.cursor_dial[name].valueChanged.connect(lambda value, dial=(name): self.cursor_dial_change(value,dial))

            self.cursor_enable_button[name] = QPushButton("OFF")
            self.cursor_enable_button[name].setStyleSheet(Style.button_style.value)
            self.cursor_enable_button[name].setFixedWidth(Style.button_width_2.value)
            self.cursor_enable_button[name].setCheckable(True)
            self.cursor_enable_button[name].setChecked(False)
            self.cursor_enable_button[name].clicked.connect(lambda value,button=(name): self.cursor_enable_click(value,button))

            cursor_fine_button[f"{name}_up"] = QPushButton("+")
            cursor_fine_button[f"{name}_up"].setStyleSheet(Style.button_style_2.value)
            cursor_fine_button[f"{name}_up"].setFixedSize(Style.square_button.value,Style.square_button.value)
            cursor_fine_button[f"{name}_up"].clicked.connect(lambda value,button=(f"+ {name}"): self.cursor_fine_click(value,button))

            cursor_fine_button[f"{name}_down"] = QPushButton("-")
            cursor_fine_button[f"{name}_down"].setStyleSheet(Style.button_style_2.value)
            cursor_fine_button[f"{name}_down"].setFixedSize(Style.square_button.value,Style.square_button.value)
            cursor_fine_button[f"{name}_down"].clicked.connect(lambda value,button=(f"- {name}"): self.cursor_fine_click(value,button))

            layout.addWidget(label[name],row,column,1,1)
            layout.addWidget(self.cursor_enable_button[name],row,column+1,1,1)
            layout.addWidget(self.cursor_lineEdit[name],row,column+2,1,1)
            layout.addWidget(self.cursor_dial[name],row+1,column,1,3,alignment=(Qt.AlignmentFlag.AlignLeft))
            layout.addWidget(cursor_fine_button[f"{name}_up"],row+1,column+2,1,1,alignment=(Qt.AlignmentFlag.AlignRight))
            layout.addWidget(cursor_fine_button[f"{name}_down"],row+2,column+2,1,1,alignment=(Qt.AlignmentFlag.AlignRight))

        layout.addWidget(head_label,0,0,1,2)
        layout.addWidget(cursor_reset_button,0,6,1,1,alignment=(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight))
        layout.addWidget(invisible_line,2,3,1,1)
        layout.addWidget(line1,1,0,1,0,alignment=(Qt.AlignmentFlag.AlignTop))
        layout.addWidget(line2,5,0,1,0,alignment=(Qt.AlignmentFlag.AlignTop))

        return frame

    # Command--------------------------------------------------------------------

    def cursor_reset_click(self, unused):
        self.x1 = -2 * self.time_per_div
        self.x2 = 2 * self.time_per_div
        self.y1 = -2 * self.volt_per_div
        self.y2 = 2 * self.volt_per_div

        value = [self.x1,self.x2,self.y1,self.y2]
        parameter = ["X1","X2","Y1","Y2"]

        for i in range(len(parameter)):
            if "X" in parameter[i]:
                unit = "s"
            else:
                unit = "V"
            self.cursor_lineEdit[parameter[i]].setText(f"{self.unit_prefix(value[i])}{unit}")

    def cursor_enable_click(self, state, name):
        if state == True:
            text = "ON"
        else:
            text = "OFF"
        self.cursor_enable_button[name].setText(text)
        
    def cursor_lineEdit_enter(self, name):
        lineEdit = self.cursor_lineEdit[name]
        text = lineEdit.text()

        str_num = "".join([Char for Char in text if Char.isdigit() or Char == "."])
        float_num = 0.0
        unit = ""

        if len("".join([Char for Char in text if Char == "."])) > 1:
            first_dot = str_num.find(".")
            second_dot = str_num.find(".", first_dot + 1)
            str_num = str_num[:second_dot]
        
        if not(str_num == ""):
            float_num = float(str_num)

        if ("-" in text):
            float_num = float_num * -1.0

        if "m" in text:
            float_num = float_num * 1e-3
        elif "u" in text or "µ" in text:
            float_num = float_num * 1e-6
        elif "n"in text:
            float_num = float_num * 1e-9

        if "X" in name:
            unit = "s"
            if "X1" in name:
                self.x1 = float_num
            elif "X2" in name:
                self.x2 = float_num
        else:
            unit = "V"
            if "Y1" in name:
                self.y1 = float_num
            elif "Y2" in name:
                self.y2 = float_num

        lineEdit.setText(f"{self.unit_prefix(float_num)}{unit}")

    def cursor_dial_change(self, value, dial):
        if "X" in dial:
            per_div = self.time_per_div
            unit = "s"
            if "1" in dial:
                self.x1 = (value*per_div)/self.sample_per_div
                value = self.x1
            else:
                self.x2 = (value*per_div)/self.sample_per_div
                value = self.x2
        else:
            per_div = self.volt_per_div
            unit = "V"
            if "1" in dial:
                self.y1 = (value*per_div)/self.sample_per_div
                value = self.y1
            else:
                self.y2 = (value*per_div)/self.sample_per_div
                value = self.y2
        self.cursor_lineEdit[dial].setText(f"{self.unit_prefix(value)}{unit}")

    def cursor_fine_click(self, unused, button):
        name = button[2:]

        dial = self.cursor_dial[name]
        lineEdit = self.cursor_lineEdit[name]

        if "X" in name:
            per_div = self.time_per_div
        else:
            per_div = self.volt_per_div

        if dial.minimum() <= dial.value() <= dial.maximum():
            if "+" in button:
                move = 1
            else:
                move = -1
            dial.setValue(dial.value() + move)
            value = (dial.value() * per_div) / self.sample_per_div
            if "X1" in name:
                lineEdit = self.cursor_lineEdit[name]
                self.x1 = value
            elif "X2" in name:
                self.x2 = value
            elif "Y1" in name:
                self.y1 = value
            elif "Y2" in name:
                self.y2 = value

    def run_pause_click(self, state):
        if state == True:
            self.run_button.setText("Running")
        else:
            self.run_button.setText("Paused")

    def connect_click(self, state): # REMINDER
        pass # REMINDER

    def address_enter(self, lineEdit): # REMINDER
        pass

    def change_domain(self, unused, domain):
        self.domain = domain
                
    def volt_time_reset_click(self, unused, button):
        if button == "volt":
            default = 10
            self.volt_per_div = self.volt_div_scales[default]
            self.volt_div_dial.setValue(default)
            self.volt_div_lineEdit.setText(f"{self.unit_prefix(self.volt_per_div)}V")
            self.volt_offset = 0.0
            self.volt_offset_dial.setValue(0)
            self.volt_offset_lineEdit.setText(f"{self.unit_prefix(self.volt_offset)}V")
        else:
            default = 22
            self.time_per_div = self.time_div_scales[default]
            self.time_div_dial.setValue(default)
            self.time_div_lineEdit.setText(f"{self.unit_prefix(self.time_per_div)}s")
            self.time_offset = 0.0
            self.time_offset_dial.setValue(0)
            self.time_offset_lineEdit.setText(f"{self.unit_prefix(self.time_offset)}s")      

    def volt_time_dial_change(self, value, dial):
        if "div" in dial.objectName():
            if "volt" in dial.objectName():
                self.volt_per_div = self.volt_div_scales[value]
                self.volt_div_lineEdit.setText(f"{self.unit_prefix(self.volt_per_div)}V")
                self.volt_offset = self.volt_offset_dial.value() * self.volt_per_div/self.sample_per_div
                self.volt_offset_lineEdit.setText(f"{self.unit_prefix(self.volt_offset)}s")
                self.y1 = (self.cursor_dial["Y1"].value() * self.volt_per_div )/self.sample_per_div
                self.cursor_lineEdit["Y1"].setText(f"{self.unit_prefix(self.y1)}s")
                self.y2 = (self.cursor_dial["Y2"].value() * self.volt_per_div )/self.sample_per_div
                self.cursor_lineEdit["Y2"].setText(f"{self.unit_prefix(self.y2)}s")
                
            else:
                self.time_per_div = self.time_div_scales[value]
                self.time_div_lineEdit.setText(f"{self.unit_prefix(self.time_per_div)}s")
                self.time_offset = self.time_offset_dial.value() * self.time_per_div/self.sample_per_div
                self.time_offset_lineEdit.setText(f"{self.unit_prefix(self.time_offset)}s")
                self.x1 = (self.cursor_dial["X1"].value() * self.time_per_div )/self.sample_per_div
                self.cursor_lineEdit["X1"].setText(f"{self.unit_prefix(value)}s")
                self.x2 = (self.cursor_dial["X2"].value() * self.time_per_div )/self.sample_per_div
                self.cursor_lineEdit["X2"].setText(f"{self.unit_prefix(value)}s")
        else:
            if "volt" in dial.objectName():
                self.volt_offset = value/self.sample_per_div * self.volt_per_div
                self.volt_offset_lineEdit.setText(f"{self.unit_prefix(self.volt_offset)}V")
            else:
                self.time_offset =  value/self.sample_per_div * self.time_per_div
                self.time_offset_lineEdit.setText(f"{self.unit_prefix(self.time_offset)}s")

    def volt_time_lineEdit_enter(self, lineEdit):
        text = lineEdit.text()

        str_num = "".join([Char for Char in text if Char.isdigit() or Char == "."])
        float_num = 0.0
        unit = ""

        if len("".join([Char for Char in text if Char == "."])) > 1:
            first_dot = str_num.find(".")
            second_dot = str_num.find(".", first_dot + 1)
            str_num = str_num[:second_dot]
        
        if not(str_num == ""):
            float_num = float(str_num)

        if ("-" in text) and ("offset" in lineEdit.objectName()):
            float_num = float_num * -1.0

        if "m" in text:
            float_num = float_num * 1e-3
        elif "u" in text or "µ" in text:
            float_num = float_num * 1e-6
        elif "n"in text:
            float_num = float_num * 1e-9

        if "div" in lineEdit.objectName():
            if float_num == 0.0:
                if "volt" in lineEdit.objectName():
                    float_num = self.volt_per_div
                else:
                    float_num = self.time_per_div
            else:
                if "volt" in lineEdit.objectName():
                    self.volt_per_div = float_num
                else:
                    self.time_per_div = float_num

        else:
            if "volt" in lineEdit.objectName():
                self.volt_offset = float_num
            else:
                self.time_offset = float_num

        if "volt" in lineEdit.objectName():
            unit = "V"
        else:
            unit = "s"

        lineEdit.setText(f"{self.unit_prefix(float_num)}{unit}")

    def volt_time_fine_click(self, unused, button):

        if "volt" in button:
            div_value = self.volt_per_div
            offset_value = self.volt_offset
            scale = self.volt_div_scales
            div_dial = self.volt_div_dial
            offset_dial = self.volt_offset_dial
            div_lineEdit = self.volt_div_lineEdit
            offset_lineEdit = self.volt_offset_lineEdit
            unit = "V"
        else:
            div_value = self.time_per_div
            offset_value = self.time_offset
            scale = self.time_div_scales
            div_dial = self.time_div_dial
            offset_dial = self.time_offset_dial
            div_lineEdit = self.time_div_lineEdit
            offset_lineEdit = self.time_offset_lineEdit
            unit = "s"
        
        if "div" in button:
            dial = div_dial
            value = div_value
        else:
            dial = offset_dial
            value = offset_value


        if dial.minimum() <= dial.value() <= dial.maximum():
            if "+" in button:
                move = 1
            else:
                move = -1
            dial.setValue(dial.value() + move)
            if "div" in button:
                value = scale[dial.value()]
                offset_value = offset_dial.value() * div_value
                div_lineEdit.setText(f"{self.unit_prefix(value)}{unit}")
                offset_lineEdit.setText(f"{self.unit_prefix(offset_value)}{unit}")
            else:
                value = dial.value() * div_value/self.sample_per_div
                offset_lineEdit.setText(f"{self.unit_prefix(value)}{unit}")
            
    def process_data_from_thread(self,l):
        try:
            self.v = l
            vrms = math.sqrt(
                sum([math.pow(i,2) for i in self.v ]) / len(self.v)
            ) 
            period = round(self.find_period(self.v), 6)

            self.measure_output_label["Vmax"].setText(f"{self.unit_prefix(max(self.v))} V") 
            self.measure_output_label["Vmin"].setText(f"{self.unit_prefix(min(self.v))} V") 
            self.measure_output_label["Vpp"].setText(f"{self.unit_prefix(max(self.v) - min(self.v))} V") 
            self.measure_output_label["Vrms"].setText(f"{self.unit_prefix(vrms)} V") 
            self.measure_output_label["Vavg"].setText(f"{self.unit_prefix(sum(self.v) / len(self.v))} V") 
            self.measure_output_label["Period"].setText(f"{self.unit_prefix(period)} s") 
            self.measure_output_label["Freq"].setText(f"{self.unit_prefix(1 / period)} Hz") 

            self.measure_output_label["X1"].setText(f"{self.unit_prefix(self.x1)}s")     
            self.measure_output_label["X2"].setText(f"{self.unit_prefix(self.x2)}s")     
            self.measure_output_label["Y1"].setText(f"{self.unit_prefix(self.y1)}s")     
            self.measure_output_label["Y2"].setText(f"{self.unit_prefix(self.y2)}s")     

            self.measure_output_label["ΔX"].setText(f"{self.unit_prefix(abs(self.x1 - self.x2))}s")     
            self.measure_output_label["ΔY"].setText(f"{self.unit_prefix(abs(self.y1 - self.y2))}s")     

            # #freq-side frame
            self.thd_label = QLabel("THD : --")

            N = len(self.v)
            fft_result = np.fft.fft(self.v)
            freqs = np.fft.fftfreq(len(self.v), d=30e-6)

            magnitude = np.abs(fft_result) / N 
            threshold = max(magnitude) * 0.1  # Set threshold at 10% of max magnitude
            # harmonics = [(freqs[i], magnitude[i]) for i in range(1, len(freqs)//2) if magnitude[i] > threshold]

            positive_freqs = freqs[:N//2]
            positive_magnitude = magnitude[:N//2]

            # Find the fundamental frequency (first non-zero peak)
            fundamental_idx = np.argmax(positive_magnitude[1:]) + 1  # Ignore DC (index 0)
            fundamental_freq = positive_freqs[fundamental_idx]
            A1 = positive_magnitude[fundamental_idx]  # Amplitude of fundamental

            # Extract harmonics (integer multiples of fundamental frequency)
            harmonic_indices = [
                i for i in range(len(positive_freqs)) 
                if abs(positive_freqs[i] % fundamental_freq) < ((1 / 30e-6) / N) and i != fundamental_idx
            ]
            harmonic_magnitudes = positive_magnitude[harmonic_indices]
    
            # Compute THD
            thd = np.sqrt(np.sum(harmonic_magnitudes**2)) / A1 * 100  # Percentage

            # self.thd_label.setText(f"THD : {round(thd, 2)}%")
            self.measure_output_label["THD"].setText(f"{round(thd,3)} %")


        except TypeError as e:
            print(e)
            # self.period_label.setText(f"Period : -- s")
            # self.freq_label.setText(f"Freq : -- Hz")

    def test_data(self): # REMINDER_TO_DELETE (FOR TESTING)
        self.v = test_data
        self.t = np.arange(-max(test_t)/2, max(test_t)/2, test_sampling_t)

    def update_plot(self): 

        if self.run_button.isChecked() == True: # REMINDER_TO_DELETE
            pass

        else :
            if self.plot_ref == None:
                # creat ref graph
                try:
                    self.canvas.ax.set_facecolor("#0B0B0C")
                    self.canvas.figure.patch.set_facecolor("#232428")
                    self.canvas.ax.tick_params(axis="both", colors="white")
                    plot_ref = self.canvas.ax.plot(self.t,self.v,color="#FFF428")
                    self.plot_ref = plot_ref[0]

                except ValueError as e :
                    print(e)
                    return 

            else:
                # update ref graph
                if self.domain == Domain.TIME :
                    #set canvas
                    self.canvas.ax.xaxis.set_major_locator(MultipleLocator(abs(self.time_per_div)))

                    self.canvas.ax.yaxis.set_major_locator(MultipleLocator(abs(self.volt_per_div)))

                    x_max = self.time_per_div * self.division / 2
                    y_max = self.volt_per_div * self.division / 2

                    self.canvas.ax.set_xlim(-x_max, x_max)
                    self.canvas.ax.set_ylim(-y_max, y_max)

                    try :
                        # self.plot_ref.set_xdata(self.t + [self.time_offset])
                        # self.plot_ref.set_ydata(self.v + [self.volt_offset])
                        self.plot_ref.set_xdata(self.t )
                        self.plot_ref.set_ydata(self.v )
                    except ValueError as e:
                        # print(e)
                        return

                else :
                    # Compute FFT
                    fft_result = np.fft.fft(self.v)
                    freqs = np.fft.fftfreq(len(self.v), d=30e-6) # 1 / fs or time_interval

                    x = freqs[:len(freqs)//2]
                    y = np.abs(fft_result[:len(freqs)//2])

                    x_max_round = math.ceil(round(max(x)/100))*100

                    freq_per_div = 800 
                    mag_per_div = 50

                    self.canvas.ax.xaxis.set_major_locator(MultipleLocator(freq_per_div))
                    self.canvas.ax.yaxis.set_major_locator(MultipleLocator(mag_per_div))

                    self.canvas.ax.set_xlim(0, freq_per_div * self.division)
                    self.canvas.ax.set_ylim(0, mag_per_div * self.division)

                    self.plot_ref.set_xdata(x)
                    self.plot_ref.set_ydata(y)

                cursor = ['cursor_x1', 'cursor_x2', 'cursor_y1', 'cursor_y2']

                for attr in cursor:
                    if hasattr(self, attr):
                        getattr(self, attr).remove()

                lines = [
                    (self.x1, 'axvline', 'dashed', "X1"),
                    (self.x2, 'axvline', 'dotted', "X2"),
                    (self.y1, 'axhline', 'dashed', "Y1"),
                    (self.y2, 'axhline', 'dotted', "Y2"),
                ]

                for attr, (pos, method, style, parameter) in zip(['cursor_x1', 'cursor_x2', 'cursor_y1', 'cursor_y2'], lines):
                    if self.cursor_enable_button[parameter].isChecked() == False:
                        style = ""
                    setattr(self, attr, getattr(self.canvas.ax, method)(pos, color='#1FC9CD', linestyle=style, linewidth=1))
        
            self.canvas.ax.grid(True)
            self.canvas.ax.grid(color="#232428")
            self.canvas.ax.tick_params(axis="both", labelsize=8)

            try:
                self.canvas.draw()

            except ValueError as e:
                print(e,' bug alert!!!')

    def find_period(self, data):
            DC = 0.0
            ind = []
            edge_time = []
            Period = 0.0
            for i in range(len(data) - 1):
                if data[i] < (0.0 + DC) and data[i+1] > (0.0 + DC):
                    ind.append([i,i+1])
            if len(ind) >= 2:
                for i in range(len(ind) - 1):
                    m = (data[ind[i][1]] - data[ind[i][0]]) / (ind[i][1] - ind[i][0])
                    b = data[ind[i][0]] - (m * ind[i][0])
                    edge_time.append((DC - b) / m)

            if len(edge_time) >= 2:
                Period = (edge_time[1] - edge_time[0]) * 30e-6 
            else:
                Period = None

            return Period

    def unit_prefix(self,value):
        text = "-- "
        prefix = ""
        float_digit = 3

        if isinstance(value, (int, float, np.float64)):
            abs_value = abs(float(value))
            if (abs_value >= (1.0 - 5e-3)) or (abs_value == 0.0) or (abs_value <= 1e-11):
                    value = round(value,float_digit)
            elif abs_value >= (1e-3 - 5e-6):
                value = round(value * 1e3,float_digit)
                prefix = "m"
            elif abs_value >= (1e-6 - 5e-9):
                value = round(value * 1e6,float_digit)
                prefix = "µ"
            elif abs_value >= 1e-9:
                value = round(value * 1e9,float_digit)
                prefix = "n"

            digit = len(str(int(abs(value))))

            if digit >= 3:
                float_digit = 1
            else:
                float_digit = 3 - digit

            value = f"{round(value,float_digit):.{float_digit}f}"

            text = f"{value} {prefix}"

        return text

if __name__ == "__main__":
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    main = Main()
    main.show()
    sys.exit(app.exec())
