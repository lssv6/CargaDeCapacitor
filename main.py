#  ____                       _ _                      
# / ___|__ _ _ __   __ _  ___(_) |_ ___  _ __ ___  ___ 
#| |   / _` | '_ \ / _` |/ __| | __/ _ \| '__/ _ \/ __|
#| |__| (_| | |_) | (_| | (__| | || (_) | | |  __/\__ \
# \____\__,_| .__/ \__,_|\___|_|\__\___/|_|  \___||___/
#           |_|                                        
#
# Autor: Lucas Sousa Silva
# Orientador: Edinaldo Lopes Barros
#

import tkinter as tk
import tkinter.font as tkf
from matplotlib.typing import ColorType
import numpy as np
import traceback
import serial
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.backend_bases import key_press_handler
def get_arduino_connection():
    return serial.serial_for_url(url="/dev/ttyUSB0", baudrate=9600)

class MainWindow(tk.Tk):
    charge_data = None
    charge_elapsed_time = None
    discharge_data = None
    discharge_elapsed_time = None
    
    measured_voltage_in_mv = 4620

    charge_xs = [0]
    discharge_xs = [0]
    discharge_voltage_data = [0]
    charge_voltage_data = [0]

    info_statuses = (b"CHARGED", b"CHARGING", b"DISCHARGED", b"DISCHARGING")

    def update_state_label(self, state:bytes):
        statuses: dict[str, str] = {
            "CHARGED": "Capacitor carregado",
            "CHARGING": "Carregando capacitor",
            "DISCHARGED": "Capacitor descarregado",
            "DISCHARGING": "Descarregando capacitor",
        }
        status = statuses.get(state.decode(), "Problema no arduino")
        self.state_label_textvariable.set(status)
        self.update()

    def connect_arduino(self):
        print("Connecting arduino")
        try:
            self.arduino_connection = get_arduino_connection()
        except Exception:
            self.is_arduino_connected_label_textvariable.set("Problema ao conectar arduino.")
            self.is_arduino_connected_label.config(fg="#FF0000")
            traceback.print_exc()
            return
        self.is_arduino_connected_label_textvariable.set("Arduino conectado!")
        self.is_arduino_connected_label.config(fg="#00AA00")
        print("Connected arduino")
        line = self.arduino_connection.read_until(b"$")
        line = line[:-1]
        print(line)
        self.update_state_label(line)


    def generate_charge_plot(self):
        self.arduino_connection.write(b"CHARGE")
        self.raw_charge_data = []
        time_checking = False
        while True:
            line = self.arduino_connection.read_until(b"$")
            line = line[:-1]
            print(line)
            if line in self.info_statuses:
                self.update_state_label(line)
                if line == b"CHARGED":
                    break
                continue
            if time_checking:
                self.charge_elapsed_time = float(line)
                continue 
            if line.startswith(b"ELAPSED_TIME"):
                time_checking=True
                continue
            arduino_value = int(line)
            self.raw_charge_data.append(arduino_value)

        if self.charge_elapsed_time is None:
            return

        print(f"{self.raw_charge_data=}")
        self.charge_voltage_data = [(data / 1023) * self.measured_voltage_in_mv for data in self.raw_charge_data]
        self.charge_xs = np.arange(0,self.charge_elapsed_time, (self.charge_elapsed_time/len(self.charge_voltage_data)))
        self.charge_line.set_data(self.charge_xs, self.charge_voltage_data)
        ax = self.plot_canvas.figure.axes[0]
        ax.set_xlim(min([min(self.discharge_xs), min(self.charge_xs)]), max([max(self.discharge_xs), max(self.charge_xs)]))
        ax.set_ylim(min([min(self.discharge_voltage_data), min(self.charge_voltage_data)]), max([max(self.discharge_voltage_data), max(self.charge_voltage_data)]))
        self.plot_canvas.draw()

    def generate_discharge_plot(self):
        self.arduino_connection.write(b"DISCHARGE")
        self.raw_discharge_data = []
        time_checking = False
        while True:
            line = self.arduino_connection.read_until(b"$")
            line = line[:-1]
            if line in self.info_statuses:
                self.update_state_label(line)
                if line == b"DISCHARGED": break
                continue
            if time_checking:
                self.discharge_elapsed_time = float(line)
                continue 
            if line.startswith(b"ELAPSED_TIME"):
                time_checking=True
                continue
            arduino_value = int(line)
            self.raw_discharge_data.append(arduino_value)

        if self.discharge_elapsed_time is None:
            return

        self.discharge_voltage_data = [(data / 1023) * self.measured_voltage_in_mv for data in self.raw_discharge_data]
        self.discharge_xs = np.arange(0,self.discharge_elapsed_time, (self.discharge_elapsed_time/len(self.discharge_voltage_data)))
        self.discharge_line.set_data(self.discharge_xs, self.discharge_voltage_data)
        ax = self.plot_canvas.figure.axes[0]
        ax.set_xlim(min([min(self.discharge_xs), min(self.charge_xs)]), max([max(self.discharge_xs), max(self.charge_xs)]))
        ax.set_ylim(min([min(self.discharge_voltage_data), min(self.charge_voltage_data)]), max([max(self.discharge_voltage_data), max(self.charge_voltage_data)]))
        self.plot_canvas.draw()

    def __init__(self, title):
        super().__init__(baseName=title)
        super().config(bg="#FFFFFF")
        self.rowconfigure(0, weight=1)

        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)


        self.figure = Figure()

        self.ax = self.figure.add_subplot()

        self.charge_line, = self.ax.plot([*range(100)], [0 for _ in range(100)])
        self.charge_line.set_color("#00AA00")
        self.discharge_line, = self.ax.plot([*range(100)], [0 for _ in range(100)])
        self.discharge_line.set_color("#AA0000")

        self.ax.set_ylabel("Tensão (mV)")
        self.ax.set_xlabel("Tempo em milisegundos (ms)")

        self.plot_frame = tk.Frame(master=self)
        self.plot_frame.grid(row=0, column=0)

        self.plot_canvas = FigureCanvasTkAgg(figure=self.figure,master=self.plot_frame)
        self.plot_canvas.draw()
        self.plot_canvas.get_tk_widget().grid(row=0, column=0)
        
        self.toolbar = NavigationToolbar2(self.plot_canvas)
        self.toolbar.update()

        self.plot_canvas.mpl_connect("key_press_event", lambda event: print(f"you pressed {event.key}")) # type:ignore
        self.plot_canvas.mpl_connect("key_press_event",key_press_handler) # type: ignore  


        self.control_frame = tk.Frame(master=self, bg="#FFFFFF")
        self.control_frame.grid(row=0, column=1)
        self.control_frame.rowconfigure(0)

        self.title_label = tk.Label(master=self.control_frame, text="Gerador de gráfico de carga de um capacitor.", bg="#FFFFFF")
        self.title_label.grid(row=0, column=0, columnspan=2)


        self.generate_charge_plot_button = tk.Button(master=self.control_frame, text="Carregar capacitor", bg="#a3f26f", command=self.generate_charge_plot)
        self.generate_charge_plot_button.grid(row=1, column=0)

        self.generate_discharge_plot_button = tk.Button(master=self.control_frame, text="Descarregar capacitor", bg="#f29192", command=self.generate_discharge_plot)
        self.generate_discharge_plot_button.grid(row=1,column=1)

        self.connect_arduino_button = tk.Button(master=self.control_frame, text="Conectar arduino", bg="#9999ff", command=self.connect_arduino)
        self.connect_arduino_button.grid(row=2, columnspan=2, pady=(200,0))

        self.is_arduino_connected_label_textvariable = tk.StringVar(value="Arduino ainda não conectado com o programa")
        self.is_arduino_connected_label = tk.Label(master=self.control_frame, textvariable=self.is_arduino_connected_label_textvariable, font=tkf.Font(family="Serif", slant="italic"), bg="#FFFFFF")

        self.is_arduino_connected_label.grid(row=3, columnspan=2)


        self.cap_state = tk.Label(master=self.control_frame, text="Estado do capacitor:", font=tkf.Font(family="Monospace", slant="roman"), bg="#FFFFFF")
        self.state_label_textvariable = tk.StringVar(value="DESCONHECIDO")
        self.state_label = tk.Label(master=self.control_frame, textvariable=self.state_label_textvariable, bg="#FFFFFF")
        self.cap_state.grid(row=4, column=0)
        self.state_label.grid(row=4, column=1)


root = MainWindow("Programa dos capacitores")
root.mainloop()


