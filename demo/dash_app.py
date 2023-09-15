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
from config import SECTIONS_DESCRIPTION, DOCKER, SECTIONS_TITLE
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
            dcc.Dropdown(id='section-dropdown', style={'width': '50%'},
                         options=[{'label': s, 'value': s} for s in SECTIONS_TITLE], value='Section1'),
            html.P(id='section_description', style={'width': '50%'}),
            dls.Roller(
                dcc.Graph(id='topic-model-plot'))]),

        dcc.Tab(label='Intertopic Distances', children=[
            dcc.Dropdown(id='section-dropdown-1', options=[{'label': s, 'value': s} for s in SECTIONS_TITLE],
                         value='Section1'),
            dls.Clock(dcc.Graph(id='topic-interdistance-plot'), speed_multiplier=0.5)]),

        dcc.Tab(label='Topics over time', children=[
            dcc.Dropdown(id='section-dropdown-time', options=[{'label': s, 'value': s} for s in SECTIONS_TITLE],
                         value='Section1'),
            dls.Hourglass(
                dcc.Graph(id='topic-time-plot'))]),

        dcc.Tab(label='Topic sentiment over time', children=[
            dcc.Dropdown(id='section-dropdown-time-sentiment',
                         options=[{'label': s, 'value': s} for s in SECTIONS_TITLE],
                         value='Section1'),
            dcc.Checklist(id='adjust-to-fiscal-year',
                          options=[{'label': 'Adjust to Fiscal Year', 'value': 1}],
                          value=[]
                          ),
            dls.Hourglass(
            dcc.Graph(id='topic-time-sentiment-plot'))]),

        dcc.Tab(label='Topics in web addresses', children=[
            dcc.Input(id='search-topics-url', placeholder='Enter URL...'),
            dls.Roller(dcc.Graph(id='return-topics-url'))]),
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
    data = requests.get(url=os.path.join(URL_API, 'get_topics_time'), params={'top_n': '5'}).json()
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
    Input('section-dropdown-time-sentiment', 'value'),
    Input('adjust-to-fiscal-year', 'value'))
def display_topic_time_sentiment(section, adjust_flag):
    TOP_N = 10
    data = requests.get(url=os.path.join(URL_API, 'get_topics_sentiment'), params={'freq': '1y'}).json()
    df = pd.read_json(data[section], orient='records')
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    if adjust_flag:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'].dt.year - 1, format='%Y')
    df = df.set_index('Timestamp')
    fig = px.line(data_frame=df.loc[df.Topic.isin(range(1, TOP_N)), :], y='mean', color='Name')
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
    topic_mappings = {
        '1309_lending practices_prudential standards_fdic nccob_banking': 'lending practices regulation',
        '1751_ccpa_cfpb 8217_consumer financial_enforcement': 'consumer protection enforcement',
        '178_bearing liabilities_net income_deposits borrowings_loans securities': 'bearing liabilities earnings',
        '2013_cares act_programs facilities_provisions cares_consolidated appropriations': 'cares act provisions',
        '2573_aenb_qualifying collateral_charge trust_lending trust': 'collateralized lending facility',
        '3_libor_sofr_reference rates_usd libor': 'libor reference rates',
        '557_funds rate_federal funds_federal reserve_actions federal': 'federal funds rate',
        '786_spoe_spoe strategy_parent company_support agreement': 'parent support strategy',
        '2462_secured funding_collateralized financings_gs bank_financings consolidated': 'collateralized financing assets',
        '44_federal reserve_capital liquidity_regulatory capital_basel iii': 'capital liquidity regulation',
        '846_backed securities_fasb financial_rmbs residential_capital financial': 'mortgage-backed securities',
        '86_fdic_reserve fdic_submit resolution_orderly resolution': 'fdic resolution planning',
        '878_monetary policy_monetary policies_instruments monetary_fiscal policies': 'monetary policy actions'
    }
    labels_sorted = [topic_mappings[t] for t in labels_sorted_]
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
