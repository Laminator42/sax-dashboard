from saxpy.znorm import znorm
from saxpy.paa import paa
from saxpy.sax import ts_to_string
from saxpy.alphabet import cuts_for_asize # alphabet size

def sax(T, w, a):
    # normalize timeseries so that breakpoints can be determined by N(0, 1) Gaussian
    T_normed = znorm(T)
    # perform PAA
    T_paa = paa(T, w)
    # convert PAA reduced timeseries to SAX representation using A letters
    word = ts_to_string(znorm(paa(T, w)), cuts_for_asize(a))
    # print(f"SAX representation of the timeseries: {word}")
    # print(f"frequencies of letters: {get_sax_symbol_frequency(word)}")
    return T_paa, word