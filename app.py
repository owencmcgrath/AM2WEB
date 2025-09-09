from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    session,
)

import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
import os
from werkzeug.utils import secure_filename
from xml_parser import parse_itunes_library
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"xml"}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def insert_songs_to_db(user_id, songs):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    inserted_count = 0

    for song in songs:
        try:
            values = (
                user_id,
                song.get("Track ID"),
                song.get("Name"),
                song.get("Artist"),
                song.get("Album Artist"),
                song.get("Composer"),
                song.get("Album"),
                song.get("Genre"),
                song.get("Kind"),
                song.get("Size"),
                song.get("Total Time"),
                song.get("Disc Number"),
                song.get("Disc Count"),
                song.get("Track Number"),
                song.get("Track Count"),
                song.get("Year"),
                song.get("Date Modified"),
                song.get("Date Added"),
                song.get("Play Count"),
                song.get("Play Date"),
                song.get("Play Date UTC"),
                song.get("Skip Count"),
                song.get("Skip Date"),
                song.get("Release Date"),
                song.get("Favorited", False),
                song.get("Loved", False),
                song.get("Artwork Count"),
                song.get("Sort Album"),
                song.get("Sort Artist"),
                song.get("Sort Name"),
                song.get("Persistent ID"),
                song.get("Track Type"),
                song.get("Protected", False),
                song.get("Apple Music", False),
                song.get("Location"),
                song.get("File Folder Count"),
                song.get("Library Folder Count"),
            )

            cursor.execute(
                """
                INSERT INTO songs (
                    userID,
                    track_id, name, artist, album_artist, composer, album, genre,
                    kind, size, total_time, disc_number, disc_count, track_number,
                    track_count, year, date_modified, date_added, play_count,
                    play_date, play_date_utc, skip_count, skip_date, release_date,
                    favorited, loved, artwork_count, sort_album, sort_artist,
                    sort_name, persistent_id, track_type, protected, apple_music,
                    location, file_folder_count, library_folder_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
                values,
            )
            inserted_count += 1
        except mysql.connector.Error as e:
            print(f"Error inserting song {song.get('Name')}: {e}")
            continue

    conn.commit()
    cursor.close()
    conn.close()
    return inserted_count


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not email or not password or not confirm_password:
            flash("Please fill out all fields")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("signup"))

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already exists")
            cursor.close()
            conn.close()
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO user (email, password) VALUES (%s, %s)",
            (email, hashed_password),
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash("Signup successful! Please log in.")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["userID"]
            flash("Login successful!")
            return redirect(url_for("upload"))
        else:
            flash("Invalid email or password")

    return render_template("login.html");

@app.route("/", methods=["GET", "POST"])
@login_required
def upload():
    user_id = session["user_id"]
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            try:
                songs = parse_itunes_library(filepath)
                inserted_count = insert_songs_to_db(
                    user_id, songs
                )  # Fixed order here
                flash(f"Successfully imported {inserted_count} songs!")
                os.remove(filepath)
            except Exception as e:
                flash(f"Error processing file: {str(e)}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return redirect(request.url)

            return redirect(url_for("library"))

    return render_template("upload.html")


@app.route("/library")
@login_required
def library():
    user_id = session["user_id"]
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
            SELECT 
                COUNT(*) as total_songs,
                COUNT(DISTINCT artist) as unique_artists,
                COUNT(DISTINCT album) as unique_albums,
                COUNT(DISTINCT genre) as unique_genres,
                SUM(play_count) as total_plays,
                SUM(total_time) as total_time_ms,
                ROUND(AVG(play_count), 2) as avg_plays_per_song,
                ROUND(AVG(total_time)/1000/60, 2) as avg_song_length_minutes,
                COUNT(CASE WHEN play_count = 0 THEN 1 END) as unplayed_songs,
                COUNT(CASE WHEN favorited = TRUE THEN 1 END) as favorite_count
            FROM songs
            WHERE userID = %(user_id)s
        """,
        {"user_id": user_id},
    )
    stats = cursor.fetchone()

    if stats["total_songs"] > 0:
        stats["favorite_percentage"] = round(
            (stats["favorite_count"] / stats["total_songs"]) * 100, 2
        )
        stats["unplayed_percentage"] = round(
            (stats["unplayed_songs"] / stats["total_songs"]) * 100, 2
        )
    stats["total_hours"] = (
        round(stats["total_time_ms"] / (1000 * 60 * 60), 1)
        if stats["total_time_ms"]
        else 0
    )

    cursor.execute(
        """
            SELECT 
                YEAR(play_date_utc) as year,
                MONTH(play_date_utc) as month,
                COUNT(*) as play_count
            FROM songs 
            WHERE play_date_utc IS NOT NULL
                AND userID = %(user_id)s
            GROUP BY YEAR(play_date_utc), MONTH(play_date_utc)
            ORDER BY play_count DESC
            LIMIT 5
        """,
        {"user_id": user_id},
    )
    active_months = cursor.fetchall()

    cursor.execute(
        """
            SELECT COUNT(*) as new_songs
            FROM songs
            WHERE date_added > DATE_SUB(NOW(), INTERVAL 30 DAY)
            AND userID = %s
        """,
        (user_id,),
    )
    recent_additions = cursor.fetchone()

    cursor.execute(
        """
        SELECT name, artist, ROUND(total_time/1000/60, 2) as duration_minutes
        FROM songs
        WHERE total_time > 0 AND userID = %s
        ORDER BY total_time DESC
        LIMIT 5
    """,
        (user_id,),
    )
    longest_songs = cursor.fetchall()

    cursor.execute(
        """
        SELECT name, artist, ROUND(total_time/1000/60, 2) as duration_minutes
        FROM songs
        WHERE total_time > 0 AND userID = %s
        ORDER BY total_time ASC
        LIMIT 5
    """,
        (user_id,),
    )
    shortest_songs = cursor.fetchall()

    cursor.execute(
        """
        SELECT FLOOR(year/10)*10 as decade,
        COUNT(*) as song_count
        FROM songs
        WHERE year IS NOT NULL AND userID = %s
        GROUP BY decade
        ORDER BY decade
    """,
        (user_id,),
    )
    decades = cursor.fetchall()

    cursor.execute(
        """
        SELECT name, artist,
        skip_count,
        play_count,
        ROUND(skip_count/play_count * 100, 2) as skip_ratio
        FROM songs
        WHERE play_count > 0 AND skip_count > 0 AND userID = %s
        ORDER BY skip_ratio DESC
        LIMIT 10
    """,
        (user_id,),
    )
    most_skipped = cursor.fetchall()

    cursor.execute(
        """
        SELECT artist,
        COUNT(*) as song_count,
        COUNT(DISTINCT album) as album_count,
        MIN(year) as earliest_song,
        MAX(year) as latest_song,
        ROUND(AVG(total_time)/1000/60, 2) as avg_song_length_minutes,
        SUM(play_count) as total_plays
        FROM songs
        WHERE userID = %s
        GROUP BY artist 
        HAVING COUNT(*) > 5 AND SUM(play_count) > 0
        ORDER BY SUM(play_count) DESC
        LIMIT 10
    """,
        (user_id,),
    )
    artist_analysis = cursor.fetchall()

    cursor.execute(
        """
        SELECT name, artist,
            play_count,
            DATEDIFF(NOW(), date_added) as days_in_library,
            ROUND(play_count/DATEDIFF(NOW(), date_added), 2) as plays_per_day
        FROM songs
        WHERE date_added IS NOT NULL AND userID = %s
        HAVING days_in_library > 30
        ORDER BY plays_per_day DESC
        LIMIT 10
    """,
        (user_id,),
    )
    most_replayed = cursor.fetchall()

    cursor.execute(
        """
        SELECT 
        CASE 
            WHEN HOUR(play_date_utc) BETWEEN 5 AND 11 THEN 'Morning'
            WHEN HOUR(play_date_utc) BETWEEN 12 AND 16 THEN 'Afternoon'
            WHEN HOUR(play_date_utc) BETWEEN 17 AND 20 THEN 'Evening'
            ELSE 'Night'
        END as time_of_day,
        COUNT(*) as play_count
        FROM songs
        WHERE play_date_utc IS NOT NULL AND userID = %s
        GROUP BY time_of_day
        ORDER BY play_count DESC
    """,
        (user_id,),
    )
    listening_times = cursor.fetchall()

    cursor.execute(
        """
        SELECT 
        DAYNAME(play_date_utc) as day_name,
        COUNT(*) as play_count
        FROM songs
        WHERE play_date_utc IS NOT NULL AND userID = %s
        GROUP BY DAYNAME(play_date_utc)
        ORDER BY MIN(DAYOFWEEK(play_date_utc))
    """,
        (user_id,),
    )
    listening_days = cursor.fetchall()

    cursor.execute(
        """
        SELECT 
        album,
        artist,
        COUNT(*) as songs_in_library,
        track_count as total_album_songs,
        ROUND((COUNT(*) / MAX(track_count)) * 100, 2) as completion_percentage
        FROM songs
        WHERE album IS NOT NULL AND userID = %s
        GROUP BY album, artist, track_count
        HAVING COUNT(*) > 5
        ORDER BY completion_percentage DESC
        LIMIT 10
    """,
        (user_id,),
    )
    complete_albums = cursor.fetchall()

    cursor.execute(
        """
        SELECT 
        album,
        artist,
        COUNT(*) as track_count,
        SUM(play_count) as total_plays,
        ROUND(AVG(play_count), 2) as avg_plays_per_track
        FROM songs
        WHERE userID = %s
        GROUP BY album, artist
        HAVING COUNT(*) > 3
        ORDER BY total_plays DESC
        LIMIT 10
    """,
        (user_id,),
    )
    most_played_albums = cursor.fetchall()

    cursor.execute(
        """
        SELECT 
            genre,
            FLOOR(year/10)*10 as decade,
            COUNT(*) as song_count
        FROM songs
        WHERE genre IS NOT NULL AND year IS NOT NULL AND userID = %s
        GROUP BY genre, decade
        ORDER BY decade, song_count DESC
    """,
        (user_id,),
    )
    genre_evolution = cursor.fetchall()

    cursor.execute(
        """
        SELECT 
            genre,
            COUNT(*) as song_count,
            ROUND(SUM(total_time)/1000/60/60, 2) as total_hours,
            ROUND(AVG(total_time)/1000/60, 2) as avg_minutes_per_song
        FROM songs
        WHERE genre IS NOT NULL AND userID = %s
        GROUP BY genre
        ORDER BY total_hours DESC
        LIMIT 10
    """,
        (user_id,),
    )
    genre_time = cursor.fetchall()

    cursor.execute(
        """
        SELECT 
        artist,
        MIN(date_added) as first_added,
        MAX(date_added) as last_added,
        COUNT(*) as total_songs,
        SUM(play_count) as total_plays
        FROM songs
        WHERE userID = %s AND play_count > 0
        GROUP BY artist
        HAVING COUNT(*) > 5
        ORDER BY first_added
        LIMIT 10
    """,
        (user_id,),
    )
    artist_growth = cursor.fetchall()

    cursor.execute(
        """
        SELECT 
            artist,
            COUNT(*) as songs,
            ROUND(AVG(play_count), 2) as avg_plays,
            ROUND(STDDEV(play_count), 2) as play_count_stddev
        FROM songs
        WHERE userID = %s AND play_count > 0
        GROUP BY artist
        HAVING COUNT(*) > 5 AND play_count_stddev > 0
        ORDER BY play_count_stddev
        LIMIT 10
    """,
        (user_id,),
    )
    consistent_artists = cursor.fetchall()

    cursor.execute(
        """
        SELECT 
            name,
            artist,
            play_count,
            skip_count,
            ROUND(play_count/DATEDIFF(NOW(), date_added), 2) as plays_per_day
        FROM songs
        WHERE date_added < DATE_SUB(NOW(), INTERVAL 90 DAY)
            AND play_count > 10
            AND skip_count < 3
            AND userID = %s
        ORDER BY plays_per_day DESC
        LIMIT 10
    """,
        (user_id,),
    )
    growers = cursor.fetchall()

    cursor.execute(
        """
        SELECT 
            name,
            artist,
            play_count,
            skip_count,
            ROUND((play_count - skip_count) / play_count * 100, 2) as completion_rate
        FROM songs
        WHERE play_count > 10
            AND skip_count = 0
            AND userID = %s
        ORDER BY play_count DESC
        LIMIT 10
    """,
        (user_id,),
    )
    never_skip = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "library.html",
        active_months=active_months,
        recent_additions=recent_additions,
        longest_songs=longest_songs,
        shortest_songs=shortest_songs,
        decades=decades,
        most_skipped=most_skipped,
        artist_analysis=artist_analysis,
        most_replayed=most_replayed,
        stats=stats,
        listening_times=listening_times,
        listening_days=listening_days,
        complete_albums=complete_albums,
        most_played_albums=most_played_albums,
        genre_evolution=genre_evolution,
        genre_time=genre_time,
        artist_growth=artist_growth,
        consistent_artists=consistent_artists,
        growers=growers,
        never_skip=never_skip,
    )

@app.route("/drop", methods=['POST'])
def drop_table_personal_table():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute("TRUNCATE TABLE songs")
        conn.commit()
        
        return redirect(url_for("upload"))
    except Exception as e:
        return "An error occurred while resetting data", 500
    finally:
        cursor.close()
        conn.close()

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)