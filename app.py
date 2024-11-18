from flask import Flask, render_template, request, flash, redirect, url_for
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
import os
from werkzeug.utils import secure_filename
from xml_parser import parse_itunes_library

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xml'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def insert_songs_to_db(songs):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    inserted_count = 0
    
    for song in songs:
        try:
            values = (
                song.get('Track ID'),
                song.get('Name'),
                song.get('Artist'),
                song.get('Album Artist'),
                song.get('Composer'),
                song.get('Album'),
                song.get('Genre'),
                song.get('Kind'),
                song.get('Size'),
                song.get('Total Time'),
                song.get('Disc Number'),
                song.get('Disc Count'),
                song.get('Track Number'),
                song.get('Track Count'),
                song.get('Year'),
                song.get('Date Modified'),
                song.get('Date Added'),
                song.get('Play Count'),
                song.get('Play Date'),
                song.get('Play Date UTC'),
                song.get('Skip Count'),
                song.get('Skip Date'),
                song.get('Release Date'),
                song.get('Favorited', False),
                song.get('Loved', False),
                song.get('Artwork Count'),
                song.get('Sort Album'),
                song.get('Sort Artist'),
                song.get('Sort Name'),
                song.get('Persistent ID'),
                song.get('Track Type'),
                song.get('Protected', False),
                song.get('Apple Music', False),
                song.get('Location'),
                song.get('File Folder Count'),
                song.get('Library Folder Count')
            )
            
            cursor.execute("""
                INSERT INTO songs (
                    track_id, name, artist, album_artist, composer, album, genre,
                    kind, size, total_time, disc_number, disc_count, track_number,
                    track_count, year, date_modified, date_added, play_count,
                    play_date, play_date_utc, skip_count, skip_date, release_date,
                    favorited, loved, artwork_count, sort_album, sort_artist,
                    sort_name, persistent_id, track_type, protected, apple_music,
                    location, file_folder_count, library_folder_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            inserted_count += 1
        except mysql.connector.Error as e:
            print(f"Error inserting song {song.get('Name')}: {e}")
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    return inserted_count

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                songs = parse_itunes_library(filepath)
                inserted_count = insert_songs_to_db(songs)
                flash(f'Successfully imported {inserted_count} songs!')
                os.remove(filepath)
            except Exception as e:
                flash(f'Error processing file: {str(e)}')
                if os.path.exists(filepath):
                    os.remove(filepath)
                return redirect(request.url)
            
            return redirect(url_for('library'))
    
    return render_template('upload.html')

@app.route('/library')
def library():
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
    
    return render_template('library.html', songs=songs, top_artists=top_artists)

if __name__ == '__main__':
    app.run(debug=True)