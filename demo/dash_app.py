"""
This is to show the three topic models and their inttertopic distances
"""
import json

import requests
import pandas as pd
import os

from bertopic import BERTopic
from collections import Counter

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px
from config import SECTIONS_DESCRIPTION, DOCKER, SECTIONS_TITLE, FED_TOPIC_MAPPINGS
import dash_loading_spinners as dls

# Change the URL according to whether we are in docker or not (this can be made better)
if not DOCKER:
    URL_API = 'http://127.0.0.1:8080'
else:
    URL_API = 'http://0.0.0.0:8000'
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
            dcc.Dropdown(id='section-dropdown', style={'width': '70.75%'},
                         options=[{'label': s, 'value': s} for s in SECTIONS_TITLE], value='Section1'),
            html.P(id='section_description', style={'width': '50%'}),
            dls.Roller(
                dcc.Graph(id='topic-model-plot'))]),

        dcc.Tab(label='Intertopic Distances', children=[
            dcc.Dropdown(id='section-dropdown-1',style={'width': '70.75%'}, options=[{'label': s, 'value': s} for s in SECTIONS_TITLE],
                         value='Section1'),
            dls.Roller(children=[dcc.Graph(id='topic-interdistance-plot'),dcc.Graph(id='topic-hierarchical-plot')])]),

        dcc.Tab(label='Topics over time', children=[
            dcc.Dropdown(id='section-dropdown-time', style={'width': '70.75%'}, options=[{'label': s, 'value': s} for s in SECTIONS_TITLE],
                         value='Section1'),
            dls.Roller(
                dcc.Graph(id='topic-time-plot'))]),

        dcc.Tab(label='Topic sentiment over time', children=[
            dcc.Dropdown(id='section-dropdown-time-sentiment',style={'width': '70.75%'},
                         options=[{'label': s, 'value': s} for s in SECTIONS_TITLE],
                         value='Section1'),
            dcc.Checklist(id='adjust-to-fiscal-year',
                          options=[{'label': 'Adjust to Fiscal Year', 'value': 1}],
                          value=[]
                          ),
            dls.Roller(
            dcc.Graph(id='topic-time-sentiment-plot'))]),

        dcc.Tab(label='Topics in web addresses', children=[
            dcc.Input(id='search-topics-url',style={'width': '52%'}, placeholder='Enter URL...', value='https://www.federalreserve.gov/newsevents/pressreleases/bcreg20230829b.htm'),
            dls.Roller(dcc.Graph(id='return-topics-url'))]),
    ])
])



@app.callback(
    Output('topic-model-plot', 'figure'),
        Output('section_description', 'children'),
    Output('topic-hierarchical-plot', 'figure'),
            Input('section-dropdown', 'value'))
def display_topic_model(section):
    fig_top = topic_models[section].visualize_barchart(title=f'<b>Topic word scores: {section} <b>')
    fig_hier = topic_models[section].visualize_hierarchy(top_n_topics=50, title=f'<b>Topic Hierarchical structure <b>')
    fig_top.update_layout(height=800, width=1200)
    return fig_top, SECTIONS_DESCRIPTION[section], fig_hier


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
    TOP_N = 15
    data = requests.get(url=os.path.join(URL_API, 'get_topics_time'), params={'top_n': f'{TOP_N}'}).json()
    df = pd.read_json(data[section], orient='records')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    fig = topic_models[section].visualize_topics_over_time(df)
    fig.update_layout(
        height=800, width=1200
    )
    return fig


@app.callback(
    Output('topic-time-sentiment-plot', 'figure'),
    Input('section-dropdown-time-sentiment', 'value'),
    Input('adjust-to-fiscal-year', 'value'))
def display_topic_time_sentiment(section, adjust_flag):
    TOP_N = 15
    FREQ = '1Y'
    data = requests.get(url=os.path.join(URL_API, 'get_topics_sentiment'), params={'freq': f'{FREQ}'}).json()
    df = pd.read_json(data[section], orient='records')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    if adjust_flag:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'].dt.year - 1, format='%Y')
    df = df.set_index('Timestamp')
    fig = px.line(data_frame=df.loc[df.Topic.isin(range(0, TOP_N)), :], y='mean', color='Name')
    fig.update_layout(
        title='Topic Sentiment over time',
        xaxis_title='Snapshot Date',
        yaxis_title='Average sentiment',
        height=800, width=1200
    )
    if adjust_flag:
        fig.update_xaxes(
            tickformat='%Y'
        )
    return fig


@app.callback(
    Output('return-topics-url', 'figure'),
    Input('search-topics-url', 'value'))
def get_topics_url(url):
    keep_all = True
    text = requests.get(url=os.path.join(URL_API,"get_topics_url"), params={'url': url, 'keep_all': f'{keep_all}'}).json()
    # text is a dictionary with keys the sections, and values the topics found per section.
    topics_list = [topics  for section, topics_section in text.items() for topics in topics_section]
    count = Counter(topics_list)
    labels = list(count.keys())
    values = list(count.values())

    # Sort lists
    values_sorted = sorted(values, reverse=False)
    labels_sorted_ = [x for _,x in sorted(zip(values,labels), reverse=False)]
    if url=='https://www.federalreserve.gov/newsevents/pressreleases/bcreg20230829b.htm':
        labels_sorted = [FED_TOPIC_MAPPINGS[t] for t in labels_sorted_]
    else:
        labels_sorted = labels_sorted_
    fig = go.Figure(go.Bar(
        x=values_sorted,
        y=labels_sorted,
        orientation='h',
        marker_color='blue',
    ))
    fig.update_layout(
        title=f'Topic frequency on {url}',
        xaxis_title='Frequency',
        yaxis_title='Topic (all sections merged)',
        height=800, width=1200
    )
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
