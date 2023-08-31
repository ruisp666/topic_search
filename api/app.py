# api.py
import logging
from typing import Dict

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
async def get_topics_time(freq=None, top_n=None):
    logger.info('Returning a dictionary of dataframes. Each dataframe is a section')
    with open("../data/topics_overtime.json", "r") as f:
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


if __name__ == '__main__':
    uvicorn.run(app, port=8000)
