import mysql.connector
from datetime import datetime
from xml_parser import parse_itunes_library

def insert_songs_to_db(songs, db_config):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    for song in songs:
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
    
    conn.commit()
    cursor.close()
    conn.close()

# Usage example:
db_config = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'music_library'
}

songs = parse_itunes_library('path_to_library.xml')
insert_songs_to_db(songs, db_config)