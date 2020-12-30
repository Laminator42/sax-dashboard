# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import pandas as pd
import numpy as np

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go

from saxpy.paa import paa
from saxpy.znorm import znorm
from saxpy.sax import ts_to_string
from saxpy.alphabet import cuts_for_asize


# ---------- utility functions ----------
def exponential(n):
    return np.array([100*np.exp(0.005 * i) for i in range(n)])

def sinus(n):
    return np.array([123*np.sin(2*np.pi/200 * i) + 42 for i in range(n)])

def get_timeseries(n, fct):
    # ensure reproducible results. also ensures that plotted timeseries is the same used to get sax
    np.random.seed(seed=133742)
    x = np.arange(n)
    # generate timeseries that represents an exponential growth with added gaussian noise
    y = fct(n) + np.random.normal(0, 10, size=n)
    return x, y

def get_paa(ts, w):
    # apply piecewise aggregate approximation in w dimensions
    ts_paa = paa(ts, w)
    # TODO: check if repeats are appropriate
    return np.repeat(ts_paa, len(ts)//w)

def get_sax_repr(ts, w, a):
    # as depicted in "iSAX: Indexing and Mining Terabyte Sized Time Series" (Shieh, Keogh)
    # a normalized timeseries should be used for SAX, since values should be splitted by assuming
    # a density described by normal distribution N(mu=0, sigma=1). A PAA is performed prior to
    # ensure timesereis is described by a short string of symbols.
    ts_normed = znorm(ts)
    ts_paa = paa(ts_normed, w)
    word = ts_to_string(ts_paa, cuts_for_asize(a))
    return word

def get_sax_symbol_frequency(word):
    return {key: word.count(key) for key in set(word)}


# ---------- app setup ----------
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.H1(children='SAX Sandbox'),

    html.Label('Size of Dataset N'),
    dcc.Slider(
        id="dataset-size-slider",
        min=32,
        max=1024,
        step=32,
        value=512,
        marks={i: str(i) for i in range(32, 1024+1, 32)},
    ),
    html.Label('Number of PAA batches w'),
    # check for conistency if N%w != 0
    dcc.Slider(
        id="paa-batches-slider",
        min=4,
        max=16,
        step=2,
        value=8,
        marks={i: str(i) for i in range(4, 16+1, 2)},
    ),
    html.Label('Number of SAX symbols a'),
    dcc.Slider(
        id="sax-symbols-slider",
        min=2,
        max=8,
        step=2,
        value=4,
        marks={i: str(i) for i in range(2, 8+1, 2)},
    ),
    html.Div(style={"margin": "30px"}),

    dcc.Graph(
        id='graph-exponential'
    ),
    html.Div(id='display-sax-representation-exponential'),
    
    dcc.Graph(
        id='graph-sinus'
    ),
    html.Div(id='display-sax-representation-sinus'),
    
])


# ---------- callbacks / add reactivity ----------
@app.callback(
    dash.dependencies.Output('graph-exponential', 'figure'),
    [
        dash.dependencies.Input('dataset-size-slider', 'value'),
        dash.dependencies.Input('paa-batches-slider', 'value'),
    ]
)
def update_graph_exp(n, w):
    x, y = get_timeseries(n=n, fct=exponential)
    ts_paa = get_paa(ts=y, w=w)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name="timeseries"))
    fig.add_trace(go.Scatter(x=x, y=ts_paa, mode="lines", name="paa"))
    fig.update_layout(
        title={'text': 'Arbitrary Timeseries (Exponential with Gaussian Noise) and a PAA Reduction'},
        xaxis={'title': 'index'},
        yaxis={'title': 'value'},
    )
    return fig

@app.callback(
    dash.dependencies.Output('display-sax-representation-exponential', 'children'),
    [
        dash.dependencies.Input('dataset-size-slider', 'value'),
        dash.dependencies.Input('paa-batches-slider', 'value'),
        dash.dependencies.Input('sax-symbols-slider', 'value'),
    ]
)
def set_display_sax_repr_exp(n, w, a):
    _, y = get_timeseries(n=n, fct=exponential)
    sax_repr = get_sax_repr(ts=y, w=w, a=a)
    return f"The SAX representation of the timeseries is: {sax_repr}. With frequencies of letters: {get_sax_symbol_frequency(sax_repr)}"

@app.callback(
    dash.dependencies.Output('graph-sinus', 'figure'),
    [
        dash.dependencies.Input('dataset-size-slider', 'value'),
        dash.dependencies.Input('paa-batches-slider', 'value'),
    ]
)
def update_graph_sin(n, w):
    x, y = get_timeseries(n=n, fct=sinus)
    ts_paa = get_paa(ts=y, w=w)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name="timeseries"))
    fig.add_trace(go.Scatter(x=x, y=ts_paa, mode="lines", name="paa"))
    fig.update_layout(
        title={'text': 'Arbitrary Timeseries (Sine with Gaussian Noise) and a PAA Reduction'},
        xaxis={'title': 'index'},
        yaxis={'title': 'value'},
    )
    return fig

@app.callback(
    dash.dependencies.Output('display-sax-representation-sinus', 'children'),
    [
        dash.dependencies.Input('dataset-size-slider', 'value'),
        dash.dependencies.Input('paa-batches-slider', 'value'),
        dash.dependencies.Input('sax-symbols-slider', 'value'),
    ]
)
def set_display_sax_repr_sin(n, w, a):
    _, y = get_timeseries(n=n, fct=sinus)
    sax_repr = get_sax_repr(ts=y, w=w, a=a)
    return f"The SAX representation of the timeseries is: {sax_repr}. With frequencies of letters: {get_sax_symbol_frequency(sax_repr)}"




# ---------- main ----------
if __name__ == '__main__':
    app.run_server(debug=True)
