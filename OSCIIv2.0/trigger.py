import sys, math
import matplotlib.pyplot as plt
import numpy as np
import math

ESP = 0.01 
factor = 3.3 / (1 << 12)

def trgIndexRis(arr : list) -> int :
    try :
        mxnm = max(arr)
        minm = min(arr) 
        trgp = round((mxnm + minm) / 2, 4) 
        ind = 0 

        ll = []
        for i in range(0,len(arr)) :
            ll.append(round(arr[i],1))
        rec = set(ll)

        if len(rec) == 2:
            # print('if')
            for i in range(0, len(arr)) :
                if math.isclose(round(arr[i]), round(minm)) and round(arr[i + 1],1) == round(mxnm,1) :
                    return i 
            return 0

        else :
            for i in range(0, len(arr)) :
                if math.isclose(round(arr[i]), round(trgp)) and round(arr[i + 10],1) > round(trgp,1):
                    return i 
            return 0

    except IndexError:
        # print('expept')
        for i in range(0, len(arr) - 1) :
            if round(arr[i],1) == 0.3 and round(arr[i+1],1) == 0.5:
                return i 
        return 0 

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

if __name__ == 'main' :
    pass
