# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from data import get_dataset
from sax import sax

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

xs, ts = get_dataset()
ts_paa, sax_rep = sax(T=ts, w=8, a=4)

fig = go.Figure()
fig.add_trace(go.Scatter(x=xs, y=ts, mode="lines+markers", name="timeseries"))
fig.add_trace(go.Scatter(x=xs, y=np.repeat(ts_paa, 20), mode="lines+markers", name="paa"))

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    html.Label('Size of Dataset'),
    dcc.Slider(
        id="dataset-size-slider",
        min=16,
        max=30*4,
        step=4,
        value=32,
        marks={i: str(i) for i in range(16, 31*4, 4)},
    ),
    html.Div(style={"margin": "30px"}),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

@app.callback(
    dash.dependencies.Output('slider-output-container', 'children'),
    [dash.dependencies.Input('dataset-size-slider', 'value')])
def update_output(value):
    return 'You have selected "{}"'.format(value)

if __name__ == '__main__':
    app.run_server(debug=True)