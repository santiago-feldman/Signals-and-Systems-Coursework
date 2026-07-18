import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as sp
import pandas as pd

def getDataFromDigilent(path):

    file = pd.read_csv(path)    

    frec = file.iloc[:,0]
    mag = file.iloc[:,1]
    phase = file.iloc[:,2]

    return frec, mag, phase

if __name__ == "__main__":
    
    frec, mag, phase = getDataFromDigilent()

    plt.plot(frec, phase)
    plt.show()