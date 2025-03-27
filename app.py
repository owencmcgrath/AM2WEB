from flask import Flask, render_template, request, flash, redirect, url_for, session
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
import os
from werkzeug.utils import secure_filename
from xml_parser import parse_itunes_library
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import pylast

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
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def insert_songs_to_db(user_id, songs):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    inserted_count = 0

    for song in songs:
        try:
            values = (
                user_id, song.get("Track ID"), song.get("Name"), song.get("Artist"),
                song.get("Album Artist"), song.get("Composer"), song.get("Album"),
                song.get("Genre"), song.get("Kind"), song.get("Size"),
                song.get("Total Time"), song.get("Disc Number"), song.get("Disc Count"),
                song.get("Track Number"), song.get("Track Count"), song.get("Year"),
                song.get("Date Modified"), song.get("Date Added"), song.get("Play Count"),
                song.get("Play Date"), song.get("Play Date UTC"), song.get("Skip Count"),
                song.get("Skip Date"), song.get("Release Date"), song.get("Favorited", False),
                song.get("Loved", False), song.get("Artwork Count"), song.get("Sort Album"),
                song.get("Sort Artist"), song.get("Sort Name"), song.get("Persistent ID"),
                song.get("Track Type"), song.get("Protected", False),
                song.get("Apple Music", False), song.get("Location"),
                song.get("File Folder Count"), song.get("Library Folder Count"),
            )

            cursor.execute(
                """
                INSERT INTO songs (
                    userid, track_id, name, artist, album_artist, composer, album, genre,
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

def get_album_artwork(artist, album):
    network = pylast.LastFMNetwork(api_key=os.getenv("LASTFM_API_KEY"))
    try:
        album_obj = network.get_album(artist, album)
        return album_obj.get_cover_image(size=3)  # size 3 is large image
    except:
        return None

@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    return render_template("templates/landing.html")

@app.route("/library", methods=["GET", "POST"])
@login_required
def library():
    user_id = session["user_id"]

    # Handle file upload
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
                inserted_count = insert_songs_to_db(user_id, songs)
                flash(f"Successfully imported {inserted_count} songs!")
                os.remove(filepath)
            except Exception as e:
                flash(f"Error processing file: {str(e)}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return redirect(request.url)

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    WITH MonthlyPlays AS (
        SELECT
            CASE MONTH(play_date_utc)
                WHEN 1 THEN 'Jan.'
                WHEN 2 THEN 'Feb.'
                WHEN 3 THEN 'Mar.'
                WHEN 4 THEN 'Apr.'
                WHEN 5 THEN 'May'
                WHEN 6 THEN 'Jun.'
                WHEN 7 THEN 'Jul.'
                WHEN 8 THEN 'Aug.'
                WHEN 9 THEN 'Sep.'
                WHEN 10 THEN 'Oct.'
                WHEN 11 THEN 'Nov.'
                WHEN 12 THEN 'Dec.'
            END as month,
            YEAR(play_date_utc) as year,
            artist,
            album,
            total_time
        FROM songs
        WHERE userid = %(user_id)s
            AND play_date_utc IS NOT NULL
            AND YEAR(play_date_utc) = YEAR(CURDATE())
    ),
    ArtistPlays AS (
        SELECT
            month,
            year,
            artist,
            COUNT(*) as play_count,
            ROW_NUMBER() OVER (PARTITION BY month, year ORDER BY COUNT(*) DESC) as rn
        FROM MonthlyPlays
        GROUP BY month, year, artist
    ),
    AlbumPlays AS (
        SELECT
            month,
            year,
            album,
            COUNT(*) as play_count,
            ROW_NUMBER() OVER (PARTITION BY month, year ORDER BY COUNT(*) DESC) as rn
        FROM MonthlyPlays
        GROUP BY month, year, album
    )
    SELECT
        mp.month,
        mp.year,
        ap.artist as top_artist,
        alp.album as top_album,
        ROUND(SUM(mp.total_time)/1000/60, 0) as minutes_played
    FROM MonthlyPlays mp
    LEFT JOIN ArtistPlays ap ON mp.month = ap.month
        AND mp.year = ap.year
        AND ap.rn = 1
    LEFT JOIN AlbumPlays alp ON mp.month = alp.month
        AND mp.year = alp.year
        AND alp.rn = 1
    GROUP BY mp.month, mp.year, ap.artist, alp.album
    ORDER BY mp.month DESC
    """, {'user_id': user_id})

    monthly_stats = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("library.html", monthly_stats=monthly_stats)

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
            session["user_id"] = user["userid"]
            flash("Login successful!")
            return redirect(url_for("library"))
        else:
            flash("Invalid email or password")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
