import requests
from fastapi.testclient import TestClient
import sqlite3

from api.app import app
import pandas as pd

client = TestClient(app)

# Make sure the service is up before running the tests.

def test_connection():
    """Tests if the service is up."""
    response = client.get("/")
    assert response.status_code == 200


def test_get_topics_time():
    """Tests the get_topics_time endpoint."""
    response = client.get("/get_topics_time")
    assert response.status_code == 200


def test_get_topics_time_frequency():
    """Tests the use of the frequency parameter in the get_topics_time endpoint.
    We test if the satus is 200 and also if the frequency is the one we expect.
    """
    freq = '1Y'
    response = client.get(f"/get_topics_time?freq={freq}")
    assert response.status_code == 200
    text = response.json()
    assert text['frequency'] == freq


def test_get_topics_time_count():
    """Tests the use of top_n parameter in the get_topics_time endpoint"""
    top_N = 20
    response = client.get(f"/get_topics_time?top_n={top_N}")
    assert response.status_code == 200
    text = response.json()
    assert text['top_n'] == str(top_N)
    # See if in fact we get 20 unique topics.
    df_test = pd.read_json(text['Section1'], orient='records')
    # We include the topic with the outliers.
    assert df_test['Topic'].nunique() == top_N + 1


def test_get_topics_sentiment():
    """Tests the get_topics_sentiment endpoint."""
    response = client.get("/get_topics_sentiment")
    assert response.status_code == 200
    freq = '3M'
    response = client.get(f"/get_topics_sentiment?freq={freq}")
    assert response.status_code == 200
    text = response.json()
    assert text['frequency'] == freq


def test_update_database(url: str = "https://www.bloomberg.com"):
    """Tests if a given url is added to the database."""
    host = 'http://127.0.0.1:8080'
    keep_all=False
    requests.get(f"{host}/get_topics_url", params={'url': url, 'keep_all': f'{keep_all}'})

    # Check database was updated
    conn = sqlite3.connect('db/topics-url-db.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM data WHERE url="https://www.bloomberg.com"')
    result = cursor.fetchone()
    assert result is not None
    assert result[0] == url
    conn.close()
