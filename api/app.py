# api.py
import logging
from typing import Dict
import requests
import numpy as np
import uvicorn
from fastapi import FastAPI
import pandas as pd
import json
import sqlite3
from langchain.document_loaders import WebBaseLoader
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from assets.buckets_location import SENTIMENT_LABELS_URL, TOPICS_AND_DOCS_SENTIMENT_URL, TOPICS_OVERTIME_URL
from bertopic import BERTopic
import os

app = FastAPI(debug=True)

sections = [f'Section{s}' for s in ['1', '1A', '7']]
if os.environ.get('TOPIC_MODELS_PATH') is not None:
    model_path = '/app/topic_models'
else:
    model_path = '../topic_models'

topic_models = {s: BERTopic.load(os.path.join(model_path, f'topic_models_{s}'),
                                 embedding_model='all-MiniLM-L6-v2') for s in sections}
topics_names_dict = {s: dict(zip(tm.get_topic_info()['Topic'], tm.get_topic_info()['Name'])) for s, tm in
                     topic_models.items()}
# Create a global logger
logger = logging.getLogger('topics-api')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

if os.environ.get('TOPIC_MODELS_PATH') is not None:
    assets_path = '/app/api/assets'
else:
    assets_path = 'assets'


@app.on_event("startup")
async def load_jsons():
    global sections_topics_time
    sections_topics_time = json.load(open(os.path.join(assets_path, "topics_overtime.json")))
    return sections_topics_time

# Load the topics_and_docs_sentiment json at the start of the application from the GCP bucket
#text = requests.get(url=TOPICS_AND_DOCS_SENTIMENT_URL).json()
text = json.load(open(os.path.join(assets_path, "topics_and_docs_sentiment.json")))
topics_and_docs_sentiment = {k: pd.read_json(v, orient='records') for k, v in text.items()}

if os.environ.get('TOPIC_MODELS_PATH') is None:
    logger.info('We are in local')
    db_path = 'db/topics-url-db.db'
else:
    logger.info('We are in docker')
    db_path = 'db/data_docker.db'

# Establish the connection and create the SQLite table if not existing
connection = sqlite3.connect(db_path)

cursor = connection.cursor()
cursor.execute("""
          CREATE TABLE IF NOT EXISTS data_topics
          (url text, topics_section1 text, topics_section2 text, topics_section3 text)
          """)
mapping_db = {'Section1': 'topics_section1', 'Section1A': 'topics_section2', 'Section7': 'topics_section3'}


@app.get("/")
async def root():
    return {"message": "Please use the /docs endpoint to view the API documentation"}


@app.get("/get_topics_time")
async def get_topics_time(freq: str = None, top_n: int = None) -> Dict[str, str]:
    """Return dictionary of jsonnified dataframes with evolution of the topic frequency over time.

    Parameters
    ----------
    freq : str, optional
        Resample frequency for aggregation. Needs to be compatible with Pandas resample.

    top_n : int, optional
        Only return top n topics

    Returns
    -------
    dict of {str : str}
        Dictionary of topic dataframes in json format

    """
    logger.info('Returning a dictionary of dataframes. Each dataframe is a section')
    response = await load_jsons()
    if not freq and not top_n:
        logger.info('No frequency or top_n specified, all topics will be returned.')
        return response
    else:
        response_json = {}
        sections_topics_time_dfs = {k: pd.read_json(v) for k, v in response.items()}
    if freq:
        logger.info(f'Using {freq} to aggregate across time. This may take some time.')
        response_json['frequency'] = freq
        for s, v in sections_topics_time_dfs.items():
            response[s] = v.set_index('Timestamp').groupby(['Topic', 'Words', 'Name'])['Frequency'].resample(
                rule=freq).sum().reset_index(level=(0, 1, 2))
    if top_n:
        logger.info(f'Top {top_n} topics will be returned. Topic -1 contains the outliers.')
        response_json['top_n'] = str(top_n)
        # If there is no frequency parameter, we simply filter for the top topics
        if not freq:
            for s, v in sections_topics_time_dfs.items():
                response[s] = v.loc[v['Topic'].isin(list(range(-1, top_n)))]
        # We can reuse response from above
        else:
            for s, v in response.items():
                response[s] = response[s].loc[response[s]['Topic'].isin(list(range(-1, top_n)))]
    for s in sections:
        response_json[s] = response[s].to_json(orient='records')
    return response_json


@app.get("/get_topics_sentiment")
async def get_topics_sentiment(freq: str = None) -> Dict[str, str]:
    """Return dictionary of topic sentiment dataframes.

    Parameters
    ----------
    freq : str, optional
        Resample frequency. Needs to be compatible with Pandas resample.

    Returns
    -------
    dict of {str : str}
        Dictionary of JSON topic sentiment data

    """
    logger.info('Returning a dictionary of dataframes. Each dataframe corresponds to the sentiment found for a '
                'respective section')
    if freq is None:
        logger.info(
            'No frequency specified, all documents will be returned for post-processing. This may block or interrupt '
            'your browser')
        response_json = {s: v.to_json(orient='records') for s, v in topics_and_docs_sentiment.items()}
        response_json['frequency'] = 'No frequency specified'
    else:
        logger.info(f'Using {freq} to aggregate sentiment across time.')
        agg_sentiment = {}
        for s in topics_and_docs_sentiment:
            topics_and_docs_sentiment[s]['Timestamp'] = pd.to_datetime(topics_and_docs_sentiment[s]['Timestamp'],
                                                                       infer_datetime_format=True)
            agg_sentiment[s] = topics_and_docs_sentiment[s].set_index('Timestamp').groupby(['Topic', 'Name'])[
                'sentiment_sigma_fsa'].resample(rule=freq).agg([np.mean, np.median]).reset_index(level=(0, 1,))
        response_json = {s: v.reset_index().to_json(orient='records', date_format='iso') for s, v in agg_sentiment.items()}
        response_json['frequency'] = freq
    return response_json


@app.get("/get_topics_url")
async def get_topics_url(url: str = 'https://www.federalreserve.gov/newsevents/pressreleases/bcreg20230829b.htm',
                         keep_all: bool = False) -> \
        Dict[str, list]:
    """Return the topics found in the text content of a given url

    Parameters
    ----------
    url : str, optional
        URL to scrape.

    Returns
    -------
    dict of {str : str}
        Dictionary of JSON topic url data

    """
    # Check if the url is present in the database
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM data WHERE url=?', [url])
    if cursor.fetchone() is None:
        logger.info('URL not present in the database. Scraping, extracting topics, and inserting into the database')
    else:
        logger.info('URL exists in the database. Returning the topics')
        cursor.execute('SELECT topics_section1, topics_section2, topics_section3 FROM data WHERE url=?', [url])

        topics_doc = {s: cursor.fetchone()[i] for i, s in enumerate(sections)}
        return topics_doc
    loader = WebBaseLoader(url)
    splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=0,
                                                     model_name='sentence-transformers/all-MiniLM-L6-v2')
    page = loader.load()
    docs = splitter.split_documents(page)
    docs_str = [doc.page_content for doc in docs]
    topics_doc = {}
    for s, tm in topic_models.items():
        topics, _ = tm.transform(docs_str)
        # Use this the user can keep uniques or get all the topics for density analysis.
        if keep_all:
            topics_doc[s] = list(np.vectorize(topics_names_dict[s].get)(topics))
        else:
            topics_doc[s] = list(set(np.vectorize(topics_names_dict[s].get)(topics)))
    # Make strings of the lists
    data_to_insert = {}
    for s, k in mapping_db.items():
        data_to_insert[k] = ','.join(topics_doc[s])
    data_to_insert['url'] = url
    cursor.execute('INSERT INTO data_topics VALUES (:url, :topics_section1, :topics_section2, :topics_section3)',
                   data_to_insert)
    connection.commit()
    return topics_doc


if __name__ == '__main__':
    uvicorn.run("app:app", port=8080)
