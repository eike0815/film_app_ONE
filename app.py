import os
import requests
from flask import Flask, jsonify, request, render_template, redirect, url_for
from SQLlte_data_m import SQLiteDataManager, db, User, Movie
from dotenv import load_dotenv

load_dotenv()

OMDB_API_KEY = os.getenv("OMDB_API_KEY")

def fetch_movie_details(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data.get("Response") == "True":
        return {
            "name": data.get("Title"),
            "director": data.get("Director"),
            "year": data.get("Year"),
            "rating": data.get("imdbRating"),
        }
    else:
        return None


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#db = SQLAlchemy()
db_manager = SQLiteDataManager(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/users")
def list_users():
    users = User.query.all()
    return render_template("users.html", users=users)


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            return redirect(url_for("error_page", message= "Name missing"))
        user = User(name=name)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("list_users"))
    return render_template("add_user.html")


# 📌 call all movies by user
@app.route("/users/<int:user_id>")
def get_movies(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("user_movies.html", user=user, movies= user.movies)


@app.route("/users/<int:user_id>/add_movie", methods=["GET", "POST"])
def add_movie(user_id):
    try:
        user = User.query.get_or_404(user_id)
        if request.method == "POST":
            data = request.form
            if "name" not in data or not data["name"].strip():
                return redirect(url_for("error_page", message="Movie title is required"))
            movie_name = data["name"].strip()
            existing_movie = next((m for m in user.movies if m.name.lower() == movie_name.lower()), None)
            if existing_movie:
                return redirect(url_for("error_page", message="Movie already exists in your list"))


            movie_data = fetch_movie_details(movie_name)
            if not movie_data:
                return redirect(url_for("error_page", message="Movie not found in OMDb"))


            movie = Movie(
                name=movie_data["name"],
                director=movie_data["director"],
                year=movie_data["year"] if movie_data["year"] else "Unknown",
                rating=movie_data["rating"] if movie_data["rating"] else "Unknown"
            )
            db.session.add(movie)
            user.movies.append(movie)
            db.session.commit()
            return redirect(url_for("get_movies", user_id=user.id))
        return render_template("add_movie.html", user=user)
    except Exception as e:
        db.session.rollback()
        return redirect(url_for("error_page", message="Failed to add movie"))



@app.route("/users/<int:user_id>/update_movie/<int:movie_id>", methods=["GET", "POST"])
def update_movie(user_id, movie_id):
    user = User.query.get_or_404(user_id)
    movie = Movie.query.get_or_404(movie_id)
    if request.method == "POST":
        new_name = request.form.get("name", "").strip()
        new_director = request.form.get("director", "").strip()
        new_year = request.form.get("year", "").strip()
        new_rating = request.form.get("rating", "").strip()
        if not new_name:
            return redirect(url_for("error_page", message="Movie title is required"))
        existing_movie = next((m for m in user.movies if m.name.lower() == new_name.lower() and m.id != movie.id), None)
        if existing_movie:
            return redirect(url_for("error_page", message="Another movie with this title already exists"))
        movie.name = new_name
        movie.director = new_director if new_director else movie.director
        movie.year = new_year if new_year.isdigit() else movie.year
        movie.rating = new_rating if float(new_rating) else movie.rating
        db.session.commit()
        return redirect(url_for("get_movies", user_id=user.id))
    return render_template("update_movie.html", user=user, movie=movie)


@app.route("/users/<int:user_id>/delete_movie/<int:movie_id>", methods=["POST"])
def delete_movie(user_id, movie_id):
    user = User.query.get_or_404(user_id)
    movie = Movie.query.get_or_404(movie_id)
    if movie not in user.movies:
        return redirect(url_for("error_page", message="Movie not found in user's list"))
    user.movies.remove(movie)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("get_movies", user_id=user.id))

@app.route("/error")
def error_page():
    message = request.args.get("message", "An unexpected error occurred.")
    return render_template("error.html", message=message)

if __name__ == "__main__":
    with app.app_context():
        db_manager.init_db()
    app.run(debug=True)