#!/usr/bin/python
from trigger import *
import socket
import sys
import struct
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
# import psutil

#set sampling attributes
factor = 3.3 / (1<< 12)
dc_ref = 1.0 
opamp_scale = 1
sampling_t = 30e-6 
SAMP_SIZE = 650 
TEST_ITERATIONS = 3000 

def on_close(event):
    event.canvas.figure.has_been_closed = True

def set_dump_storage(dump, read_buf) :
    n = 0
    j = 0
    for i in read_buf :
        if(n == 0) :
            i <<= 8 
            j = i        
            n = 1
        else : 
            j += i
            dump.append(round(j * factor,5)) 
            j = 0
            n = 0

# x = np.arange(0,sampling_t*len(sample),sampling_t)
# y = [0] * SAMP_SIZE 

fig = plt.figure()
fig.canvas.mpl_connect('close_event', on_close)
fig.has_been_closed = False
tpd = SAMP_SIZE 

# These constants should match the server
BUF_SIZE = 2048
SERVER_PORT = 4242

# Open socket to the server
sock = socket.socket()
SERVER_ADDR = '192.168.4.1'
addr = (SERVER_ADDR, SERVER_PORT)
sock.connect(addr)
n = 0 
dump = []

# Repeat test for a number of iterations
for test_iteration in range(TEST_ITERATIONS):
    if fig.has_been_closed == True:
        break

    # Read BUF_SIZE bytes from the server
    total_size = BUF_SIZE
    read_buf = b''
    while total_size > 0:
        buf = sock.recv(BUF_SIZE)
        total_size -= len(buf)
        read_buf += buf;

    # Check size of data received
    if len(read_buf) != BUF_SIZE:
        raise RuntimeError('wrong amount of data read %d', len(read_buf))

    # Send the data back to the server
    
    n += 1
    # print('count :',n)
    spec_len = 700
    set_dump_storage(dump, read_buf)
    dump = [round(i * opamp_scale - dc_ref,5)   for i in dump]
    ti = trgIndexRis(dump)
    # print(dump)

    # ti = 0
    print(dump[ti])
    # tmp = dump[ti:]
    tmp = dump[ti:ti + spec_len]
    time_base = len(tmp) / 7 * sampling_t  
    ax = fig.gca()
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=9))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=9))

    print(f"tmp len : {len(tmp)}")
    
    #test version
    # sx = dump[0:0 + (SAMP_SIZE - len(tmp))]    
    # tmp.extend(sx)

    # ===== for 1024 samples ============================= 
    # i = 0 
    # try :    
    #     while(not(abs(tmp[-1] - dump[i]) < 0.01) and abs(tmp[-12] - dump[i]) < 0.01):
    #         i += 1
    #     sx = dump[i:i + (SAMP_SIZE - len(tmp))]    
    #     # print(f"sx len : {len(sx)}")
    #     tmp.extend(sx)
    #     #print(f"tmp len : {len(tmp)}")
    # except IndexError:
    #     tmp = dump
     
    
    x = np.arange(0, len(tmp) * sampling_t, sampling_t)
    # print(f"x's len : {len(x)}")

    if len(x) == len(tmp) :
        plt.plot(x, tmp, marker='.')
        plt.xlim(sampling_t * spec_len  * sampling_t, sampling_t*spec_len - sampling_t)

    # plt.xlabel(f'time base : {time_base*1e3} ms/div')
    plt.ylim(dc_ref * -1, 4 - dc_ref)
    plt.grid()
    plt.draw()

    plt.pause(sampling_t * spec_len)
    plt.clf()

    tmp.clear() # clear old sample (prevent ram overload) 
    dump.clear()
    dump = []

    # write_len = sock.send(read_buf)
    # if write_len != BUF_SIZE:
    #     raise RuntimeError('wrong amount of data written')
    sock.send(b't123.45')
    

# All done
sock.close()
