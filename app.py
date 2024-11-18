from flask import Flask, render_template
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

@app.route('/')
def index():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT name, artist, album, genre, play_count
        FROM songs
        ORDER BY play_count DESC
        LIMIT 50
    """)
    songs = cursor.fetchall()
    
    cursor.execute("""
        SELECT artist, COUNT(*) as song_count
        FROM songs
        GROUP BY artist
        ORDER BY song_count DESC
        LIMIT 10
    """)
    top_artists = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('home.html', songs=songs, top_artists=top_artists)

if __name__ == '__main__':
    app.run(debug=True)