import numpy as np

def get_dataset():
    w = 8
    n = 20 * w

    x = list(range(n))
    y = np.array([4*np.exp(0.005 * (i + np.random.normal(0, 3))) for i in x])    # example timeseries: exponential
    # ts = 4 * np.linspace(-3, 100, n)    # example timeseries: linear
    return x, y