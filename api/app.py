# api.py
import logging
from typing import Dict

import numpy as np
import uvicorn
from fastapi import FastAPI
import pandas as pd
import json
import sqlite3

# Create a global logger
logger = logging.getLogger('logger')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Load the topics_and_docs_sentiment json
with open("assets/topics_and_docs_sentiment.json", "r") as f:
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
async def get_topics_time(freq: str = None, top_n: int = None) -> Dict[str, pd.DataFrame]:
    """Return dictionary of topic dataframes over time.

    Parameters
    ----------
    freq : str, optional
        Resample frequency for aggregation. Needs to be compatible with Pandas resample.
    top_n : int, optional
        Only return top n topics

    Returns
    -------
    dict of {str : pd.DataFrame}
        Dictionary of topic dataframes

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

if __name__ == '__main__':
    uvicorn.run(app, port=8000)
