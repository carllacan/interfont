#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time


class Supply:
    
    def __init__(self, serial, sleep_time, pvsyntax, pcsyntax, output,
                 verbose = True, setup_comms=[],):
        self.sleep_time = sleep_time 
        self.sleep = True
        self.verbose = verbose
        self.setup_comms =setup_comms
        self.pvsyntax = pvsyntax
        self.pcsyntax = pcsyntax
        self.output = output
        self.current_mode = False
        self.serial = serial
        self.stop = False
 
    def setup(self):
        for c in self.setup_comms:
            self.write_command(c)
        
    def close(self):
        self.serial.close()
        
    def write_command(self, c):
        # Adds an EOL to a command, encodes it and sends it to the serial device.
        # Make sure to wait at least 50 ms before issuing another command.
        comm = c + '\r'
        if self.verbose:
            print(comm)
        self.output(c)
        self.serial.write(comm.encode())
        if self.sleep:
            time.sleep(self.sleep_time)
        resp = self.read_buffer().rstrip("\n").rstrip("\r")  # sobra un rstrip?
        if resp != '':
            self.output(resp)
        if self.verbose:
            print(resp) 
    
    def read_buffer(self):
        # Read buffer and decode it.
        resp = self.serial.read_all()
        return resp.decode()
    
    def PV(self, V):
        # Set the power source to a certain voltage.
        self.write_command(self.pvsyntax.format(V))
    
    def PC(self, C):
        # Set the power source to a certain current.
        self.write_command(self.pcsyntax.format(C))
    
    def runseries(self, ts, vs, current_mode = False):
        # TODO: make it work without sleeps, but rather checking the time
        if len(ts) == len(vs):
            self.sleep = False
            for i in range(len(ts)):
                if not current_mode:
                    self.PV(vs[i])
                else:
                    self.PC(vs[i])
                if i == len(ts)-1:
                    deltat=0
                else:
                    deltat = ts[i+1]-ts[i]
                time.sleep(deltat)
                if self.stop:
                    self.stop= False
                    break
            self.sleep = True
        else:
            print('## Error: Time and voltage series are not equally long. ##')

            
