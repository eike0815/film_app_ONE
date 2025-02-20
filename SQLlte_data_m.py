from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from data_manager_Interface import DataManagerInterface

db = SQLAlchemy()


user_movie = db.Table('user_movie' ,
                      db.Column('user_id', db.Integer, db.ForeignKey('user.id'),primary_key=True),
                      db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True)
                      )

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    movies =  db.relationship('Movie', secondary= user_movie, backref='users')

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    director = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, nullable=True)
class SQLiteDataManager(DataManagerInterface):
    def __init__(self, app: Flask):
        self.db = db
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)


    def get_all_users(self):
        return User.query.all()

    def get_user_movies(self, user_id):
        return Movie.query.filter_by(user_id=user_id).all()

    def add_user(self, name):
        new_user = User(name=name)
        self.db.session.add(new_user)
        self.db.session.commit()
        return new_user

    def add_movie(self, name, director, year, user_id):
        new_movie = Movie(name=name, director=director, year=year, user_id=user_id)
        self.db.session.add(new_movie)
        self.db.session.commit()
        return new_movie


    def update_movie(self, movie_id, new_title):
        movie = Movie.query.get(movie_id)
        if movie:
            movie.title = new_title
            self.db.session.commit()
            return movie
        return None

    def delete_movie(self, movie_id):
        movie = Movie.query.get(movie_id)
        if movie:
            self.db.session.delete(movie)
            self.db.session.commit()
            return True
        return False

    def init_db(self):
        with self.db.engine.connect() as connection:
            self.db.create_all()