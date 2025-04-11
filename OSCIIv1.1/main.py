from trigger import *
from enum import Enum
import time, socket, sys
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator, MultipleLocator
from scipy.fft import fft, fftfreq

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *


BUF_SIZE = 2048
SERVER_PORT = 4242
dc_ref = 1.0 
opamp_scale = 1.0
sampling_t = 30e-6 

class Domain(Enum):
    TIME = 0
    FREQ = 1

class MPL_canvas(FigureCanvas):
    def __init__(self, parent=None):
        # Graph Config
        width = 6 #inch
        height = 4 #inch
        dpi = 100

        fig = Figure(figsize=(width,height),dpi=dpi)
        self.ax = fig.add_subplot(111)
        super().__init__(fig)

        fig.subplots_adjust(top=0.95, bottom=0.09, left=0.09, right=0.99)
        self.setFixedSize(width*dpi,height*dpi)
 

class Thread(QThread):
    result = Signal(list)
    sock = socket.socket()
    SERVER_ADDR = '192.168.4.1'
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
            read_buf = b''
            while total_size > 0:
                buf = self.sock.recv(BUF_SIZE)
                total_size -= len(buf)
                read_buf += buf
    
            # Check size of data received
            if len(read_buf) != BUF_SIZE:
                raise RuntimeError('wrong amount of data read %d', len(read_buf))
    
            self.n += 1
            spec_len = 700
            set_dump_storage(self.dump, read_buf)
            self.dump = [round(i * opamp_scale - dc_ref,5)   for i in self.dump]
            ti = trgIndexRis(self.dump)
            tmp = self.dump[ti:ti + spec_len]
            self.result.emit(tmp)

            tmp.clear()  
            self.dump.clear()
            self.dump = []

            sampling_fmt_b = bytes(f't{int(sampling_t * 1e6)}', 'ascii')
            Fs = 1 / sampling_t

            self.sock.send(sampling_fmt_b)
            # print(sampling_t)
            # print(sampling_fmt_b)

    def send_data(self, data):
        self.data = data


class Main(QMainWindow):
    vol_label = None 
    time_div_label = None

    def __init__(self):
        super().__init__()

        self.setWindowTitle("OSCII v1.1") #OSCII not ASCII ONA
        self.setGeometry(100, 100, 950, 650)
        # self.setStyleSheet("background-color: rgb(49, 51, 56);")

        #time-side frame
        self.vmax_label = QLabel("Vmax : -- mV")
        self.vmin_label = QLabel("Vmin : -- mV")
        self.vpp_label = QLabel("Vpp : -- V")
        self.vrms_label = QLabel("Vrms : -- mV")
        self.vavg_label = QLabel("Vavg : -- mV")
        self.period_label = QLabel("Period : -- μs")
        self.freq_label = QLabel("Freq : -- Hz")

        #freq-side frame
        self.thd_label = QLabel("THD : --")

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
            1e-3,2e-3, 5e-3, 10e-3, 20e-3, 50e-3,0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0
        ]

        self.domain = Domain.TIME
        self.samples = 700
        self.division = 8
        # self.time_base = (self.samples * sampling_t) / self.division 

        self.time_base = self.time_div_scales[0] 
        self.t = np.arange(0, self.samples * sampling_t, sampling_t)
        self.v = []
        # self.y_max = 4
        self.y_max = 4 * self.volt_div_scales[0]

        #run other thread
        self.thread = Thread()
        self.thread.start()
        self.thread.result.connect(self.process_data_from_thread)

        #graph plotting
        self.canvas = MPL_canvas(self)

        self.timer = QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # Oscilloscope display (Matplotlib)
        main_layout.addWidget(self.canvas, 3)

        # Controls panel
        self.controls_layout = QVBoxLayout()
        main_layout.addLayout(self.controls_layout, 1)

        self.ch1_frame = self.create_channel_controls("Ch 1", "k")
        self.controls_layout.addWidget(self.ch1_frame)

        self.horizontal_frame = self.create_horizontal_controls()
        self.controls_layout.addWidget(self.horizontal_frame)

        # Buttons
        self.time_button = QPushButton("Time")
        self.time_button.setStyleSheet("background-color: red; color: white;")
        self.time_button.pressed.connect(self.change_domain_to_time)

        self.freq_button = QPushButton("Frequency")
        self.freq_button.setStyleSheet("background-color: red; color: white;")
        self.freq_button.pressed.connect(self.change_domain_to_freq)

        self.controls_layout.addWidget(self.time_button)
        self.controls_layout.addWidget(self.freq_button)

        # Measurement panel
        self.measure_time_frame = self.create_measure_time_panel()
        # self.measure_freq_frame = self.create_measure_freq_panel()

        # self.stack_layout = QStackedLayout()
        # self.stack_layout.addWidget(self.measure_time_frame)
        # self.stack_layout.addWidget(self.measure_freq_frame)
        # self.controls_layout.addLayout(self.stack_layout)

        self.controls_layout.addWidget(self.measure_time_frame)

    
    def change_domain_to_time(self):
        self.domain = Domain.TIME
        print(self.domain)

    def change_domain_to_freq(self):
        self.domain = Domain.FREQ
        print(self.domain)

    def create_channel_controls(self, label, color):
        """ Create channel control panels. """
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.Box)
        layout = QVBoxLayout()
        frame.setLayout(layout)

        h_layout = QGridLayout()
        self.vol_label = QLabel(f"{self.volt_div_scales[0]} volt/div")
        # layout.addWidget(vol_label)

        h_layout.addWidget(self.vol_label, 1,1)
        h_layout.addWidget(QLabel("Volt / Div:"),1,0)
        dial_volt = QDial()
        dial_volt.sliderMoved.connect(self.slider_position_volt)
        layout.addLayout(h_layout)
        layout.addWidget(dial_volt)
        dial_volt.setNotchesVisible(True)

        return frame
    
    def slider_position_volt(self, i):
        if i > 90:
            ind =  -1  
        else:
            ind = i // 7 

        self.y_max =  (self.division / 2) * self.volt_div_scales[ind] 
        self.vol_label.setText(f'{self.volt_div_scales[ind] } volt/div')

    def create_horizontal_controls(self):
        """ Create horizontal time base control panel. """
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.Box)
        layout = QVBoxLayout()
        frame.setLayout(layout)

        h_layout = QHBoxLayout()
        self.time_div_label = QLabel('1ns')
        h_layout.addWidget(QLabel("Time / Div:"))
        h_layout.addWidget(self.time_div_label)
        layout.addLayout(h_layout)

        dial_time = QDial()
        dial_time.sliderMoved.connect(self.slider_position_time)
        layout.addWidget(dial_time)
        dial_time.setNotchesVisible(True)

        return frame

    def slider_position_time(self, i):
        global sampling_t
        index = i // 3 

        try :
            self.time_base = self.time_div_scales[index]
            sampling_t = (self.division / self.samples) * self.time_base
            if(index in list(range(8))):
                self.time_div_label.setText("%d ns" % (self.time_base * 1e9))
        
            elif(index in  list(range(9,18))):
                self.time_div_label.setText("%d us" % (self.time_base * 1e6))

            elif(index in list(range(18,27))):
                self.time_div_label.setText("%d ms" % (self.time_base * 1e3))
            
            else :
                self.time_div_label.setText("%d s" % self.time_base)

        except IndexError as e:
            return

    def create_measure_time_panel(self):
        """ Create measurement display panel. """
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.Box)
        layout = QGridLayout()
        frame.setLayout(layout)

        layout.addWidget(self.vmax_label, 0, 0)
        layout.addWidget(self.vmin_label, 1, 0)
        layout.addWidget(self.vpp_label, 2, 0)
        layout.addWidget(self.vrms_label, 3, 0)
        layout.addWidget(self.vavg_label, 4, 0)
        layout.addWidget(self.freq_label, 5, 0)
        layout.addWidget(self.period_label, 6, 0)
        layout.addWidget(self.thd_label, 7, 0)

        return frame
        
    def create_measure_freq_panel(self):
        """ Create measurement display panel. """
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.Box)
        layout = QGridLayout()
        frame.setLayout(layout)

        layout.addWidget(self.thd_label, 0, 0)

        return frame

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

    def process_data_from_thread(self,l):
        self.v = l
        vrms = math.sqrt(
            sum([math.pow(i,2) for i in self.v ]) / len(self.v)
        ) 
        period = self.find_period(self.v)

        self.vmax_label.setText(f'Vmax : {round(max(self.v),3)}')
        self.vmin_label.setText(f'Vmin : {round(min(self.v),3)}')
        self.vpp_label.setText(f'Vpp : {round(max(self.v) - min(self.v),3)}')
        self.vrms_label.setText(f'Vrms : {round(vrms,3)}')
        self.vavg_label.setText(f'Vavg : {round(sum(self.v) / len(self.v),3)}')

        if period != None :
            self.period_label.setText(f'Period : {round(period, 6)} s')
            self.freq_label.setText(f'Freq : {int(1 / period)} Hz')

        else :
            self.period_label.setText(f'Period : -- s')
            self.freq_label.setText(f'Freq : -- Hz')

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

        self.thd_label.setText(f"THD : {round(thd, 3)}%")

        # print(self.v)
        # print(f'len {self.v}')

    def update_plot(self):
        if(self.domain == Domain.TIME) :
            #set canvas
            self.canvas.ax.cla() # Clear the canvas.
            self.canvas.ax.xaxis.set_major_locator(MultipleLocator(abs(self.time_base)))

            # self.canvas.ax.yaxis.set_major_locator(MultipleLocator((abs(2*self.y_size))/8))
            self.canvas.ax.set_xlim(0, self.time_base * 8)
            self.canvas.ax.set_ylim(-self.y_max, self.y_max)
            self.canvas.ax.grid(True)

            try :
                self.canvas.ax.plot(self.t, self.v, "b")
            except ValueError as e:
                return

            self.canvas.draw()

        else :
            self.canvas.ax.cla() # Clear the canvas.

            # Compute FFT
            fft_result = np.fft.fft(self.v)
            freqs = np.fft.fftfreq(len(self.v), d=30e-6) # 1 / fs or time_interval

            self.canvas.ax.set_ylim(0, 400)
            
            self.canvas.ax.plot(freqs[:len(freqs)//2], np.abs(fft_result[:len(freqs)//2]))
            self.canvas.ax.grid(True)

            self.canvas.draw()


if __name__ == "__main__":
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    main = Main()
    main.show()
    sys.exit(app.exec())