# api.py
import logging
from typing import Dict

import numpy as np
import uvicorn
from fastapi import FastAPI
import pandas as pd
import json
import sqlite3

from langchain.document_loaders import WebBaseLoader
from langchain.text_splitter import SentenceTransformersTokenTextSplitter

from bertopic import BERTopic
sections = [f'Section{s}' for s in ['1', '1A', '7'] ]
topic_models = {s: BERTopic.load(f'../topic_models/topic_models_{s}', embedding_model='all-MiniLM-L6-v2') for s in sections}
topics_names_dict = {s: dict(zip(tm.get_topic_info()['Topic'], tm.get_topic_info()['Name'])) for s,tm in topic_models.items()}

# Create a global logger
logger = logging.getLogger('logger')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Load the topics_and_docs_sentiment json
with open("../api/assets/topics_and_docs_sentiment.json", "r") as f:
    topics_and_docs_sentiment = json.load(f)
    topics_and_docs_sentiment = {k: pd.read_json(v) for k, v in topics_and_docs_sentiment.items()}
app = FastAPI()

connection = sqlite3.connect('app/db/topics-url-db.db')
cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
      id INTEGER PRIMARY KEY,
      message TEXT NOT NULL
    )
''')

cursor.execute('''
          CREATE TABLE IF NOT EXISTS data
          (url text, topics_section1 text, topics_section2 text, topics_section3 text)
          ''')
mapping_db = {'Section1':'topics_section1', 'Section1A':'topics_section2', 'Section7':'topics_section3'}
@app.get("/")
async def root():
    return {"message": "Please use the /docs endpoint to view the API documentation"}

@app.get("/route1")
async def route1():
    message = {"message": "This is route 1"}

    cursor.execute('''
        INSERT INTO messages (message) VALUES (?)
    ''', (message['message'],))

    connection.commit()
    
    return message


@app.get("/route3")
async def route3():
    return {"message": "This is a banana"}


@app.get("/get_topics_time")
async def get_topics_time(freq: str = None, top_n: int = None) -> Dict[str, str]:
    """Return dictionary of topic dataframes over time.

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
    with open("../api/assets/topics_overtime.json", "r") as f:
        sections_topics_time = json.load(f)
    response = {s: v for s,v in sections_topics_time.items()}
    if not freq and not top_n:
        logger.info('No frequency or top_n specified, all topics will be returned.')
        return response
    else:
        if freq:
            logger.info(f'Using {freq} to aggregate across time. This may take some time.')
            logger.info('Topics will be returned as a dictionary of dataframes')
            for s, v in sections_topics_time():
                response[s] = v.set_index('Timestamp').groupby(['Topic', 'Words', 'Name'])['Frequency'].resample(
                    rule=freq).sum().reset_index(level=(0, 1, 2, 3))
        if top_n:
            for s, v in response.items():
                response[s] = v.loc[v['Topic'].isin(list(range(-1, top_n)))]
            logger.info(f'Top {top_n} topics will be returned. Topic -1 contains the outliers.')
        else:
            logger.info('No top_n specified, all topics will be returned.')

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
    logger.info('Returning a dictionary of dataframes. Each dataframe is a section')
    if not freq:
        logger.info('No frequency specified, all documents will be returned for post-processing. This may block interrupt your browser')
        return {s: v.to_json(orient='records') for s,v in topics_and_docs_sentiment.items()}
    else:
        logger.info(f'Using {freq} to aggregate sentiment across time.')
        agg_sentiment = {}
        for s in topics_and_docs_sentiment:
            topics_and_docs_sentiment[s]['Timestamp'] = pd.to_datetime(topics_and_docs_sentiment[s]['Timestamp'], infer_datetime_format=True)
            agg_sentiment[s] = topics_and_docs_sentiment[s].set_index('Timestamp').groupby(['Topic', 'Name'])[
                'sentiment_sigma_fsa'].resample(rule=freq).agg([np.mean, np.median]).reset_index(level=(0, 1, 2,))
        return {s: v.to_json(orient='records') for s,v in agg_sentiment.items()}


@app.get("/get_topics_url")
async def get_topics_url(url: str = 'https://www.federalreserve.gov/newsevents/pressreleases/bcreg20230829b.htm') -> Dict[str, list]:
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
    #cursor.execute('INSERT INTO data VALUES (:url)', url)
    loader = WebBaseLoader(url)
    splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=0, model_name='sentence-transformers/all-MiniLM-L6-v2')
    page = loader.load()
    docs = splitter.split_documents(page)
    docs_str = [doc.page_content for doc in docs]
    topics_doc = {}
    for s, tm in topic_models.items():
        topics, _ = tm.transform(docs_str)
        # Use set to keep uniques
        topics_doc[s] = list(set(np.vectorize(topics_names_dict[s].get)(topics)))
    # Make strings of the lists
    data_to_insert = {}
    for s,k in mapping_db.items():
        print(s,k)
        data_to_insert[k] = ''.join(topics_doc[s])
    print(data_to_insert)
    data_to_insert['url'] = url
    cursor.execute('INSERT INTO data VALUES (:url, :topics_section1, :topics_section2, :topics_section3)', data_to_insert)
    connection.commit()

    return topics_doc

if __name__ == '__main__':
    uvicorn.run(app, port=8000)
