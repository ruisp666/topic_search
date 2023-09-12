"""
This is to show the three topic models and their inttertopic distances
"""
import json

import requests
import pandas as pd
import os

from bertopic import BERTopic

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
from config import SECTIONS_DESCRIPTION, URL_API, SECTIONS_TITLE


if os.environ.get('TOPIC_MODELS_PATH') is not None:
    model_path = '/app/topic_models'
else:
    model_path = '../topic_models'

topic_models = {s: BERTopic.load(os.path.join(model_path, f'topic_models_{s}'), embedding_model='all-MiniLM-L6-v2') for
                s in
                SECTIONS_TITLE}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    html.H1('SEC Filings: Topics and sentiment'),
    # Three tabs, topic-model-plot, topic-interdistance-plot, topic-overtime-plot
    dcc.Tabs(style={'width': '50%'}, children=[
        dcc.Tab(label='Top Topics', children=[
            dcc.Dropdown(id='section-dropdown', style={'width': '50%'},
                         options=[{'label': s, 'value': s} for s in SECTIONS_TITLE], value='Section1'),
            html.P(id='section_description', style={'width': '50%'}),
            dcc.Graph(id='topic-model-plot')]),

        dcc.Tab(label='Intertopic Distances', children=[
            dcc.Dropdown(id='section-dropdown-1', options=[{'label': s, 'value': s} for s in SECTIONS_TITLE],
                         value='Section1'),
            dcc.Graph(id='topic-interdistance-plot')]),

        dcc.Tab(label='Topics over time', children=[
            dcc.Dropdown(id='section-dropdown-time', options=[{'label': s, 'value': s} for s in SECTIONS_TITLE],
                         value='Section1'),
            dcc.Graph(id='topic-time-plot')]),

        dcc.Tab(label='Topic sentiment over time', children=[
            dcc.Dropdown(id='section-dropdown-time-sentiment', options=[{'label': s, 'value': s} for s in SECTIONS_TITLE],
                       value='Section1'),
            dcc.Graph(id='topic-time-sentiment-plot')]),
    ])
])


@app.callback(
    Output('topic-model-plot', 'figure'),
    Output('section_description', 'children'),
    Input('section-dropdown', 'value'))
def display_topic_model(section):
    fig = topic_models[section].visualize_barchart(title=f'<b>Topic word scores: {section} <b>')
    fig.update_layout(height=800, width=1200)
    return fig, SECTIONS_DESCRIPTION[section]


@app.callback(
    Output('topic-interdistance-plot', 'figure'),
    Input('section-dropdown-1', 'value'))
def display_intertopic_dist(section):
    fig = topic_models[section].visualize_topics(title=f'<b>Intertopic Distance Map: {section} <b>')
    fig.update_layout(height=800, width=1200)
    fig.add_annotation(x=-10, y=-30,
                       text="Text annotation without arrow",
                       showarrow=False
                       )
    return fig


@app.callback(
    Output('topic-time-plot', 'figure'),
    Input('section-dropdown-time', 'value'))
def display_topic_time(section):
    data = requests.get(url=os.path.join(URL_API,'get_topics_time'), params={'top_n': '5'}).json()
    df = pd.read_json(data[section], orient='records')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df = df.set_index('Timestamp')
    fig = px.line(data_frame=df, y='Frequency', color='Name')
    fig.update_layout(
    title='Frequency over Time',
    xaxis_title='Snapshot Date',
    yaxis_title='Frequency',
    height=800, width=1200
    )
    return fig

@app.callback(
    Output('topic-time-sentiment-plot', 'figure'),
    Input('section-dropdown-time-sentiment', 'value'))
def display_topic_time_sentiment(section):
    TOP_N = 10
    data = requests.get(url=os.path.join(URL_API, 'get_topics_sentiment'), params={'freq': '3M'}).json()
    df = pd.read_json(data[section], orient='records')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df = df.set_index('Timestamp')
    fig = px.line(data_frame=df.loc[df.Topic.isin(range(1, TOP_N)), :], y='mean', color='Name')
    fig.update_layout(
        title='Topic Sentiment over time',
        xaxis_title='Snapshot Date',
        yaxis_title='Average sentiment',
        height=800, width=1200
    )
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
