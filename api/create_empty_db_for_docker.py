import sqlite3
db_path = 'db/data_docker.db'
connect = sqlite3.connect(db_path)
cursor = connect.cursor()
cursor.execute('''
          CREATE TABLE IF NOT EXISTS data
          (url text, topics_section1 text, topics_section2 text, topics_section3 text)
          ''')
cursor.execute(''' select * from data''').fetchone()

