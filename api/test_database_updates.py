from fastapi.testclient import TestClient
import sqlite3

from api.app import app
from urllib import parse

client = TestClient(app)


def test_update_topics():
    url = "https://www.federalreserve.gov"
    response = client.post("/get_topics_url", json={"url": parse.quote(url)})

    # Check database was updated
    conn = sqlite3.connect('app/db/topics-url-db.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM data WHERE url="https://www.federalreserve.gov"')
    result = cursor.fetchone()
    assert result is not None
    assert result[0] == url

    conn.close()
