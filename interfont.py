#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import csv
import json
import serial
import time
import traceback

from supply import Supply

class Option():
    def __init__(self, parent, row, col, text, kind='text'):
        self.label = tk.Label(parent, text = text)
        self.label.grid(row = row, column = col, sticky=tk.W)
                
        if kind == 'text': 
            self.entry = tk.Entry(parent, width=10)
            self.entry.grid(row = row, column = col + 1, sticky=tk.E)
            
    def get(self):
        return self.entry.get()
    
    def set(self, text):
        self.entry.delete(0, tk.END)
        return self.entry.insert(tk.END, text)
    
    def disable(self):
        self.entry.config(state=tk.DISABLED)
        
    def enable(self):
        self.entry.config(state=tk.NORMAL)
        
class SupplyFrame (ttk.Labelframe):
    def __init__(self, parent, row, col):
        ttk.Labelframe.__init__(self, parent, 
                                text="Configurar fuente", 
                                padding = "3 3 12 12")
        self.parent = parent
        self.grid(row = row, column = col)
                
        self.configlabel = tk.Label(self, text="Parámetros de la fuente")
        self.configlabel.grid(row=0, column=0, columnspan = 2)
        
        self.baudrate = Option(self, 1, 0, "Baud rate")
        self.baudrate.set('9600')
        self.sleeptime = Option(self, 2, 0, "Sleep time")
        self.sleeptime.set('100')
        self.pvsyntax = Option(self, 3, 0, "PV syntax")
        self.pvsyntax.set('PV {:06.3f}')
        self.pcsyntax = Option(self, 4, 0, "CV syntax")
        self.pcsyntax.set('PC {:06.2f}')
        self.port = Option(self, 5, 0, "Puerto")
        self.port.set('/dev/ttyUSB0')
        
        self.savebutton = tk.Button(self, width = 6,
                                      text="Guardar",
                                      command=self.saveconfig)
        self.savebutton.grid(row=6, column=0, sticky=tk.N)
        
        self.loadbutton = tk.Button(self, width = 6,
                                      text="Cargar",
                                      command=self.loadconfig)
        self.loadbutton.grid(row=6, column=1, sticky=tk.N)
    
                
        self.setuplabel = tk.Label(self, text="Comandos de setup:")
        self.setuplabel.grid(row=0, column = 3)
        self.setuptext = tk.Text(self, width=20,height=10)
        self.setuptext.grid(row=1, column = 3, rowspan=6)
        self.set_setup_comms([])
        
        self.scrollbar= tk.Scrollbar(self, command=self.setuptext.yview)
        self.scrollbar.grid(row=1, column=4, rowspan=6,sticky='nsew')
        self.setuptext['yscrollcommand'] = self.scrollbar.set
            
    def disable(self):
        self.baudrate.disable()
        self.sleeptime.disable()
        self.pvsyntax.disable()
        self.pcsyntax.disable()
        self.port.disable()
        self.savebutton.config(state=tk.DISABLED)
        self.loadbutton.config(state=tk.DISABLED)
        self.setuptext.config(state=tk.DISABLED)
        
    def enable(self):
        self.baudrate.enable()
        self.sleeptime.enable()
        self.pvsyntax.enable()
        self.pcsyntax.enable()
        self.port.enable()
        self.savebutton.config(state=tk.NORMAL)
        self.loadbutton.config(state=tk.NORMAL)
        self.setuptext.config(state=tk.NORMAL)
    
    def get_setup_comms(self):
        text = self.setuptext.get("0.0", tk.END)
        comms = []
        for l in text.split("\n"):
            if l != "":
                comms.append(l)
        return comms
    
    def set_setup_comms(self, comms):
        self.setuptext.delete("0.0", tk.END)
        for l in comms:
            if l != "":
                self.setuptext.insert(tk.END, l + "\n")
            
    def get(self, field):
        fields = {"baudrate":self.baudrate.get(),
                  "sleeptime":self.sleeptime.get(),
                  "pvsyntax":self.pvsyntax.get(),
                  "pcsyntax":self.pcsyntax.get(),
                  "port":self.port.get(),
                  "setup_comms":self.get_setup_comms()}
        return fields[field]
        
    def saveconfig(self):
        title = "Guardar configuración de fuente"
        f = tk.filedialog.asksaveasfilename(parent = self,
                                            title = title,
                                            defaultextension = ".json")

        if type(f) == str:
            config = {"baudrate":self.get("baudrate"),
                      "sleeptime":self.get("sleeptime"),
                      "pvsyntax":self.get("pvsyntax"),
                      "pcsyntax":self.get("pcsyntax"),
                      "port":self.get("port"),
                      "setup_comms":self.get_setup_comms()}
            with open(f, 'w') as file:
                json.dump(config, file) 
            print("saved")
        
    def loadconfig(self):
        title = "Cargar configuración de fuente"
        f = tk.filedialog.askopenfile(parent = self,
                                      title = title,
                                      mode='r')
        if f != None: # if a file is selected
            config = json.load(f)
            self.baudrate.set(config["baudrate"])
            self.sleeptime.set(config["sleeptime"])
            self.pvsyntax.set(config["pvsyntax"])
            self.pcsyntax.set(config["pcsyntax"])
            self.port.set(config["port"])
            self.set_setup_comms(config["setup_comms"])
            print("loaded")
        
        
        
class ProgFrame (ttk.Labelframe):
    def __init__(self, parent, row, col):
        ttk.Labelframe.__init__(self, parent, 
                                text="Programar fuente", 
                                padding = "3 3 12 12")
        self.parent = parent
        self.grid(row = row, column = col)
            
        # Load file
        self.label = tk.Label(self, text='Cargar un archivo csv')
        self.label.grid(row=0,column=0, columnspan=2)
        
        self.filenameentry = tk.Entry(self, width=16)
        self.filenameentry.grid(row=1,column=0, columnspan=2)
        self.filenameentry.insert(tk.END, 'pwl.csv')
    
        self.seriesbutton = tk.Button(self, text="Steps", width=5,
                                      command=self.loadseries)
        self.seriesbutton.grid(row=2,column=0)
        
        self.pwlbutton = tk.Button(self, text="Rampas", width=5,
                                   command=self.loadpwl)
        self.pwlbutton.grid(row=2,column=1)
                
        # Current mode selection
        self.currentmode = tk.BooleanVar()
        self.currentmode.set(False)
        self.vmodesel = tk.Radiobutton(self,
                                    text = "Modo tensión",
                                    variable=self.currentmode,
                                    value=False,
                                    command=parent.update_waveform)
        self.vmodesel.grid(row=3, column=0, columnspan=2)
        self.cmodesel = tk.Radiobutton(self,
                                    text = "Modo corriente",
                                    variable=self.currentmode,
                                    value=True,
                                    command=parent.update_waveform)
        self.cmodesel.grid(row=4, column=0, columnspan=2)
        
        self.repeatlabel = tk.Label(self, text="Repeticiones")
        self.repeatlabel.grid(row=5, column = 0)
        
        self.repeatentry = tk.Spinbox(self, from_=1, to=1000, width=3)
        self.repeatentry.grid(row=5,column=1)
        
        # TODO canviar consola per un text gran amb bg i tal
        self.consolelabel = tk.Label(self, text="Consola:")
        self.consolelabel.grid(row=0, column = 2)
        self.consoletext = tk.Text(self, width=20,height=10)
        self.consoletext.grid(row=1, column = 2, rowspan=6)
        self.consoletext.config(state=tk.DISABLED)
    
    
        self.scrollbar= tk.Scrollbar(self, command=self.consoletext.yview)
        self.scrollbar.grid(row=1, column=3, rowspan=6,sticky='nsew')
        self.consoletext['yscrollcommand'] = self.scrollbar.set
        
    def disable(self):
        self.filenameentry.config(state=tk.DISABLED)
        self.seriesbutton.config(state=tk.DISABLED)
        self.pwlbutton.config(state=tk.DISABLED)
        self.vmodesel.config(state=tk.DISABLED)
        self.cmodesel.config(state=tk.DISABLED)
        self.repeatentry.config(state=tk.DISABLED)
        
    def enable(self):
        self.filenameentry.config(state=tk.NORMAL)
        self.seriesbutton.config(state=tk.NORMAL)
        self.pwlbutton.config(state=tk.NORMAL)
        self.vmodesel.config(state=tk.NORMAL)
        self.cmodesel.config(state=tk.NORMAL)
        self.repeatentry.config(state=tk.NORMAL)
        
    def get(self, field):
        fields = {"currentmode":self.currentmode.get(),
                  "repeat":self.repeatentry.get()}
        return fields[field]
    
    def loadpwl(self):
        self.loadfile(pwl=True)
        
    def loadseries(self):
        self.loadfile(pwl=False)
                
    def loadfile(self, pwl = False):
        ts = []
        vs = []
        
        if pwl:
            title = "Seleccionar archivo de rampas en CSV"
        else:
            title = "Seleccionar archivo de escalones en CSV"
            
        f = tk.filedialog.askopenfile(parent = self,
                                            title = title,
                                            defaultextension = ".csv",
                                            mode = 'r')

        if f != None:
            try:
                csvreader = csv.reader(f.readlines(), delimiter=',')
                for (t, v) in csvreader:
                    ts.append(float(t))
                    vs.append(float(v))
    
                else:
                    if pwl:
                        self.parent.loadpwl(ts, vs)
                    else:
                        self.parent.loadseries(ts, vs)
            except ValueError:
                text = """Error: deben haber tantos valores de tiempo como de tensión/corriente"""
                error = InfoDialog(self, text, "Error!")
                self.parent.wait_window(error)
            
    def console_write(self, text):
        self.consoletext.config(state=tk.NORMAL)
        self.consoletext.insert(tk.END, text + "\n")
        self.consoletext.see(tk.END)
        self.consoletext.update()
        self.consoletext.config(state=tk.DISABLED)
        
    def get_console(self):
        return self.console_write
    
            
class WaveformFrame (ttk.Frame):
    def __init__(self, parent, row, col):
        ttk.Frame.__init__(self, parent, padding = "3 3 12 12")
        self.parent = parent
        self.grid(row=row, column=col, columnspan=2,
                  sticky=(tk.E, tk.W, tk.N, tk.S))
   

        self.runbutton = tk.Button(self, 
                                   text='Ejecutar',
                                   command=self.runwaveform)
        self.runbutton.grid(row = 1, column = 0, sticky = tk.E)
        
        self.stopbutton = tk.Button(self, 
                                   text='Stop',
                                   command=self.stopwaveform)
        self.stopbutton.grid(row = 1, column = 1, sticky = tk.W)
        self.running_mode(False)
        
        self.helpbutton = tk.Button(self, 
                                   text='Ayuda',
                                   command=self.show_help)
        self.helpbutton.grid(row = 1, column = 3, sticky = tk.E)
        
        self.running_mode(False)
        self.update()
            
    def update(self):
        
        xs = self.parent.ts
        ys = self.parent.vs
        
        f = Figure(figsize=(6, 2), dpi=100, facecolor='none',
                   tight_layout=True)
        
        plt = f.add_subplot(111)
        plt.step(xs, ys, '-', where='post')
        plt.set_xlabel('Tiempo (s)')
        if self.parent.progframe.get('currentmode'):
            plt.set_ylabel('Corriente (A)')
        else:
            plt.set_ylabel('Voltage (V)')
        
        self.canvas = FigureCanvasTkAgg(f, master=self)
        self.canvas.show()
        self.canvas._tkcanvas.grid(row=0,column=0, columnspan=4,
                                   sticky = tk.E)
        
    def runwaveform(self):
        self.parent.runwaveform()
        
    def stopwaveform(self):
        self.parent.stopwaveform()
        
    def show_help(self):
        
        text = """
Sleep time es el tiempo que el programa esperará entre el envío de dos comandos consecutivos. Si no se espera el tiempo suficiente es posible que la fuente ignore el segundo comando. El programa utilizarà este comando para crear las rampas a partir del archivo CSV, si se utiliza esta opción. Si en el archivo se especifican intervalos de tiempo más cortos que el sleep time es posible que se pierdan puntos del perfil.

Los campos PV syntax y PC syntax deben contener la síntaxis que debe seguir el programa para programar tensión y corriente, en forma de string formateable por Python.
Por ejemplo, PV {:06.3f} enviará comandos formados por los carácteres PV, un espacio y el valor de tensión o corriente usando 6 carácteres, 3 de ellos dedicados a la parte decimal, de manera que el programa utilizará el comando PV 05.000 para programar 5 V.

Los comandos de setup se ejecutarán antes de cada perfil. Puede usarse esta opción para enviar comandos que configuren la fuente en modo remoto, o configurar la corriente antes de programar un perfil en tensión o viceversa.

Consultar el manual de la fuente para encontrar los parámetros adecuados.
"""
        helpwindow = InfoDialog(self, text, title="Ayuda")
        self.parent.wait_window(helpwindow)
        
    def running_mode(self, running = False):
        self.running = running
        if running:
            self.runbutton.config(state=tk.DISABLED)
            self.stopbutton.config(state=tk.NORMAL)
        else:
            self.runbutton.config(state=tk.NORMAL)
            self.stopbutton.config(state=tk.DISABLED)
        
        
class MainFrame (ttk.Frame):
    def __init__(self, parent, row, col):
        ttk.Frame.__init__(self, parent, padding = "3 3 12 12")
        
        parent.report_callback_exception = self.report_callback_exception
        self.parent= parent
        self.grid(row=row, column=col, columnspan=2) 
        self.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
#        self.columnconfigure(0, weight=1)
#        self.rowconfigure(0, weight=1)
        
        self.ts = [0, 1]
        self.vs = [0, 0]
        
        self.supplyframe = SupplyFrame(self, 0, 0)
        self.progframe = ProgFrame(self, 0, 1)
        self.waveformframe = WaveformFrame(self, 1, 0)
        
        
    def linspace(self, ix, fx, n):
        xs = [ix]
        delta = (fx-ix)/n
        for i in range(1, n):
            xs.append(xs[i-1] + delta)
        return (xs)
    
    def loadpwl(self, tws, vws):
        # Calculate minimum transition time
        min_trans = float(self.supplyframe.sleeptime.get())/1000
        ts = []
        vs = []
        for i in range(1, len(tws)):
            n = max(1, int((tws[i] - tws[i-1])/min_trans))
            tr = self.linspace(tws[i-1], tws[i], n)
            vr = self.linspace(vws[i-1], vws[i], n)
            ts.extend(tr)
            vs.extend(vr)
        self.loadseries(ts, vs)
    
    def update_waveform(self):
        self.waveformframe.update()
        
    def loadseries(self, ts, vs):
        self.ts = ts
        self.vs = vs
        self.update_waveform()
        
    def disable(self):
        self.supplyframe.disable()
        self.progframe.disable()
        self.waveformframe.running_mode(True)
    
    def enable(self):
        self.supplyframe.enable()
        self.progframe.enable()
        self.waveformframe.running_mode(False)
        
    def runwaveform(self):
        port = self.supplyframe.get('port')
        baudrate = int(self.supplyframe.get('baudrate'))
        sleep_time = float(self.supplyframe.get('sleeptime'))/1000
        pvsyntax = self.supplyframe.get('pvsyntax')
        pcsyntax = self.supplyframe.get('pcsyntax')
        setup_comms = self.supplyframe.get_setup_comms()
        cm = self.progframe.get("currentmode")
        try:
            ser = serial.Serial(port = port, 
                               baudrate=baudrate,
                               write_timeout=0,
                               bytesize=serial.EIGHTBITS,
                               stopbits=serial.STOPBITS_ONE,
                               parity=serial.PARITY_NONE)
            self.s = Supply(serial=ser,
                       sleep_time=sleep_time,
                       pvsyntax=pvsyntax,
                       pcsyntax=pcsyntax,
                       output=self.progframe.get_console(),
                       verbose=True,
                       setup_comms=setup_comms)
            self.disable()
            self.s.setup()
            repeats = int(self.progframe.get("repeat"))
            for i in range(repeats):
                self.s.runseries(self.ts, self.vs, cm)
                time.sleep(self.s.sleep_time)
            print("Execution completed")
            self.enable()
            self.s.PV(0)
            self.s.PC(0)
        except serial.SerialException as e:
            print(e)
            text = """Error: Fuente no encontrada. Revisar las conexiones.
                    
            Si el sistema operativo es Windows usar el administrador de dispositivos para ver los puertos en uso.
            
            Si el sistema operativo es Linux usar ls -al /dev para ver los dispositivos tty conectados. Si el puerto pertenece a root cambiar el propietario con chown o ejecutar esta aplicación como sudoer."""
            info = InfoDialog(self.parent, text, title="Error!")
            self.parent.wait_window(info)
        
    def stopwaveform(self):
        self.s.stop = True
        
    def report_callback_exception(self, *args):
        err = traceback.format_exception(*args)
        text = """Ha habido una excepción de Python. El texto de la excepción es el siguiente:
  
{}
            
Si el programa sigue funcionando después de cerrar esta ventana, ignorar este mensaje.
            """.format(err)
        
        error = InfoDialog(self, text, 'Python exception!')
        self.parent.wait_window(error)
        
        

        
class InfoDialog(tk.Toplevel):

    def __init__(self, parent, text, title):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent

        for i, t in enumerate(text.split( "\n")):
            self.info = tk.Message(self, text=text)
            self.info.grid(row=0,column=0)

        self.okbutton = tk.Button(self, 
                                  text="Aceptar", 
                                  command=self.ok)
        self.okbutton.grid(row=i+1,column=0)
        self.title(title)
        self.grab_set()
        
        for child in self.winfo_children(): child.grid_configure(padx=5, pady=5)

    def ok(self):
        self.destroy()

    

        
root = tk.Tk()
root.title("Interfont")
mainframe = MainFrame(root, 0, 0)


for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)


root.mainloop()
