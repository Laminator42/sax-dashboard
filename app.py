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
def sine(A, T, c, size):
    return np.array([A*np.sin(2*np.pi/T * i) + c for i in range(size)])

def exponential(A, k, c, size):
    return np.array([A*np.exp(k * i) + c for i in range(size)])

def get_timeseries(n, mode):
    # ensure reproducible results. also ensures that plotted timeseries is the same used to get sax
    np.random.seed(seed=133742)
    x = np.arange(n)
    if mode=="nonseasonal":
        # hard coded test data for non-seasonal data
        y = exponential(A=100, k=0.005, c=0, size=n)
    elif mode=="seasonal":
        # hard coded test data for seasonal data
        y = sine(A=123, T=200, c=42, size=n) + sine(A=20, T=10, c=0, size=n) + sine(A=10, T=50, c=0, size=n) + sine(A=22, T=8, c=0, size=n)
    else:
        raise ValueError("please choose seasonal or nonseasonal mode.")
    y += np.random.normal(0, 10, size=n)    # add gaussian noise
    return x, y

def get_paa(ts, w):
    # apply piecewise aggregate approximation in w dimensions
    ts_paa = paa(ts, w)
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

def deflate_ts(ts, tol=0.1):
    # fourier transform timeseries
    ts_fourier = np.fft.fft(ts)
    # compute threshold as fraction of maximum absolute amplitude
    # use absolute since fourier transformed values are complex
    threshold = tol*np.max(np.abs(ts_fourier))
    # only get elements above threshold and save their respective indices
    ft_deflated = [[idx, t] for idx, t in enumerate(ts_fourier) if abs(t) >= threshold]
    return ft_deflated, len(ts)

def inflate_ts(ft, n):
    # create an array containing complex valued zeros
    ft_inflated = np.zeros(n).astype(np.complex64)
    # only fill elements of non-neglected frequencies
    for idx, f in ft:
        ft_inflated[idx] = f
    # inverse transform to original space and convert back to floats
    return np.fft.ifft(ft_inflated).astype(float)

def transform_tolerance_slider_value(value):
    return {
                0: 1,
                1: 0.3,
                2: 0.1,
                3: 0.03,
                4: 0.01,
                5: 0.003,
                6: 0.001,
                7: 0.0003,
                8: 0.00001,
            }[value]


# ---------- app setup ----------
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.layout = html.Div(children=[
    # ---------- SAX ----------
    html.H1(children='SAX Sandbox'),

    html.Div(children=[
        html.Div(children=[
            html.Label('size of dataset N'),
            dcc.Slider(
                id="dataset-size-slider",
                min=32,
                max=1024,
                step=32,
                value=512,
                marks={i: str(i) for i in range(32, 1024+1, 32)},
            ),
        ], className="eight columns"),
        html.Div(children=[
            html.Label('number of PAA batches w'),
            # check for conistency if N%w != 0
            dcc.Slider(
                id="paa-batches-slider",
                min=4,
                max=16,
                step=2,
                value=8,
                marks={i: str(i) for i in range(4, 16+1, 2)},
            ),
        ], className="two columns"),
        html.Div(children=[
            html.Label('number of SAX symbols a'),
            dcc.Slider(
                id="sax-symbols-slider",
                min=2,
                max=8,
                step=2,
                value=4,
                marks={i: str(i) for i in range(2, 8+1, 2)},
            ),
        ], className="two columns")
    ], className="row"),

    html.Div(style={"margin": "30px"}),

    html.Div(children=[
            dcc.Graph(
                id='graph-exponential-sax',
                className="eight columns"
            ),
            dcc.Graph(
                id='bar-exponential',
                className="four columns"
            ),
        ],
        className='row'
    ),
    
    html.Div(children=[
            dcc.Graph(
                id='graph-sinus-sax',
                className="eight columns"
            ),
            dcc.Graph(
                id='bar-sinus',
                className="four columns"
            ),
        ],
        className='row'
    ),
    
    # ---------- FFT ----------
    html.H1(children='FFT Sandbox'),

    html.Div(children=[
        html.Label('tolerance (frequencies lower than this fraction of maximum amplitude are dropped after FFT)'),
        dcc.Slider(
            id="tolerance-slider",
            min=0,
            max=9,
            step=1,
            value=4,
            marks={i: str(transform_tolerance_slider_value(i)) for i in range(9)},
        ),
    ]),

    html.Div(style={"margin": "30px"}),

    html.Div(children=[
            dcc.Graph(
                id='graph-exponential-fft',
                className="eight columns"
            ),
            dcc.Graph(
                id='freq-exponential',
                className="four columns"
            ),
        ],
        className='row'
    ),
    
    html.Div(children=[
            dcc.Graph(
                id='graph-sinus-fft',
                className="eight columns"
            ),
            dcc.Graph(
                id='freq-sinus',
                className="four columns"
            ),
        ],
        className='row'
    ),
])


# ---------- callbacks / add reactivity ----------
@app.callback(
    dash.dependencies.Output('graph-exponential-sax', 'figure'),
    [
        dash.dependencies.Input('dataset-size-slider', 'value'),
        dash.dependencies.Input('paa-batches-slider', 'value'),
    ]
)
def update_graph_exp(n, w):
    x, y = get_timeseries(n=n, mode="nonseasonal")
    ts_paa = get_paa(ts=y, w=w)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="timeseries"))
    fig.add_trace(go.Scatter(x=x, y=ts_paa, mode="lines", name="paa"))
    fig.update_layout(
        title={'text': 'Arbitrary timeseries (exponential with gaussian noise) and respective PAA reduction'},
        xaxis={'title': 'index'},
        yaxis={'title': 'value'},
    )
    return fig

@app.callback(
    dash.dependencies.Output('bar-exponential', 'figure'),
    [
        dash.dependencies.Input('dataset-size-slider', 'value'),
        dash.dependencies.Input('paa-batches-slider', 'value'),
        dash.dependencies.Input('sax-symbols-slider', 'value'),
    ]
)
def update_bar_exp(n, w, a):
    _, y = get_timeseries(n=n, mode="nonseasonal")
    sax_repr = get_sax_repr(ts=y, w=w, a=a)
    hist = pd.Series([c for c in sax_repr]).value_counts().sort_index()

    fig = go.Figure(data=[go.Bar(
        x=hist.index,
        y=hist.values,
        text=y,
    )])
    fig.update_layout(
        title={'text': f'Frequency of SAX symbols. SAX string: {sax_repr}'},
        xaxis={'title': 'symbol'},
        yaxis={'title': 'frequency'},
    )
    return fig

@app.callback(
    dash.dependencies.Output('graph-sinus-sax', 'figure'),
    [
        dash.dependencies.Input('dataset-size-slider', 'value'),
        dash.dependencies.Input('paa-batches-slider', 'value'),
    ]
)
def update_graph_sin(n, w):
    x, y = get_timeseries(n=n, mode="seasonal")
    ts_paa = get_paa(ts=y, w=w)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="timeseries"))
    fig.add_trace(go.Scatter(x=x, y=ts_paa, mode="lines", name="paa"))
    fig.update_layout(
        title={'text': 'Arbitrary timeseries (sine with gaussian noise) and respective PAA reduction'},
        xaxis={'title': 'index'},
        yaxis={'title': 'value'},
    )
    return fig

@app.callback(
    dash.dependencies.Output('bar-sinus', 'figure'),
    [
        dash.dependencies.Input('dataset-size-slider', 'value'),
        dash.dependencies.Input('paa-batches-slider', 'value'),
        dash.dependencies.Input('sax-symbols-slider', 'value'),
    ]
)
def update_bar_sin(n, w, a):
    _, y = get_timeseries(n=n, mode="seasonal")
    sax_repr = get_sax_repr(ts=y, w=w, a=a)
    hist = pd.Series([c for c in sax_repr]).value_counts().sort_index()

    fig = go.Figure(data=[go.Bar(
        x=hist.index,
        y=hist.values,
        text=y,
    )])
    fig.update_layout(
        title={'text': f'Frequency of SAX symbols. SAX string: {sax_repr}'},
        xaxis={'title': 'symbol'},
        yaxis={'title': 'frequency'},
    )
    return fig

@app.callback(
    dash.dependencies.Output('graph-exponential-fft', 'figure'),
    [
        dash.dependencies.Input('dataset-size-slider', 'value'),
        dash.dependencies.Input('tolerance-slider', 'value'),
    ]
)
def update_graph_exp_fft(n, tol):
    tol = transform_tolerance_slider_value(tol)
    x, y = get_timeseries(n=n, mode="nonseasonal")
    
    ft_deflated, size = deflate_ts(y, tol=tol)
    y_retrieved = inflate_ts(ft_deflated, size)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="timeseries"))
    fig.add_trace(go.Scatter(x=x, y=y_retrieved, mode="lines", name="retrieved"))
    fig.update_layout(
        title={'text': f'Arbitrary timeseries (exponential with gaussian noise). Compressed to {len(ft_deflated)}/{n} ({round(len(ft_deflated)/n*100, 2)}%)'},
        xaxis={'title': 'index'},
        yaxis={'title': 'value'},
    )
    return fig

@app.callback(
    dash.dependencies.Output('freq-exponential', 'figure'),
    [
        dash.dependencies.Input('dataset-size-slider', 'value'),
        dash.dependencies.Input('tolerance-slider', 'value'),
    ]
)
def update_graph_exp_freq(n, tol):
    tol = transform_tolerance_slider_value(tol)
    x, y = get_timeseries(n=n, mode="nonseasonal")
    
    ft = np.fft.fft(y)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=np.abs(ft), mode="lines", name="fourier transform"))
    fig.add_trace(go.Scatter(x=x, y=[tol*np.max(np.abs(ft)) for i in range(n)], mode="lines", name="threshold"))
    fig.update_layout(
        title={'text': 'Fourier transformed timeseries'},
        xaxis={'title': 'index'},
        yaxis={'title': 'FFT(value)'},
        legend={'yanchor': 'top', 'y': 0.99, 'xanchor': 'right', 'x': 0.99}
    )
    fig.update_yaxes(type='log')
    return fig


@app.callback(
    dash.dependencies.Output('graph-sinus-fft', 'figure'),
    [
        dash.dependencies.Input('dataset-size-slider', 'value'),
        dash.dependencies.Input('tolerance-slider', 'value'),
    ]
)
def update_graph_sin_fft(n, tol):
    tol = transform_tolerance_slider_value(tol)
    x, y = get_timeseries(n=n, mode="seasonal")
    
    ft_deflated, size = deflate_ts(y, tol=tol)
    y_retrieved = inflate_ts(ft_deflated, size)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="timeseries"))
    fig.add_trace(go.Scatter(x=x, y=y_retrieved, mode="lines", name="retrieved"))
    fig.update_layout(
        title={'text': f'Arbitrary timeseries (sine with gaussian noise). Compressed to {len(ft_deflated)}/{n} ({round(len(ft_deflated)/n*100, 2)}%)'},
        xaxis={'title': 'index'},
        yaxis={'title': 'value'},
    )
    return fig

@app.callback(
    dash.dependencies.Output('freq-sinus', 'figure'),
    [
        dash.dependencies.Input('dataset-size-slider', 'value'),
        dash.dependencies.Input('tolerance-slider', 'value'),
    ]
)
def update_graph_sin_freq(n, tol):
    tol = transform_tolerance_slider_value(tol)
    x, y = get_timeseries(n=n, mode="seasonal")
    
    ft = np.fft.fft(y)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=np.abs(ft), mode="lines", name="fourier transform"))
    fig.add_trace(go.Scatter(x=x, y=[tol*np.max(np.abs(ft)) for i in range(n)], mode="lines", name="threshold"))
    fig.update_layout(
        title={'text': 'Fourier transformed timeseries'},
        xaxis={'title': 'index'},
        yaxis={'title': 'FFT(value)'},
        legend={'yanchor': 'top', 'y': 0.99, 'xanchor': 'right', 'x': 0.99},
    )
    fig.update_yaxes(type='log')
    return fig


# ---------- main ----------
if __name__ == '__main__':
    app.run_server(debug=True)
