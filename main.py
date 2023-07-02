from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired, Length, URL, NumberRange
import requests
from dotenv.main import load_dotenv
import os

load_dotenv(dotenv_path='keys.env')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_IMG_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies-collection.db"
Bootstrap(app)
db = SQLAlchemy(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True)
    year = db.Column(db.Integer)
    description = db.Column(db.String(250))
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(250))
    img_url = db.Column(db.String(250))

    def __repr__(self):
        return f"<Movie {self.title}>"


class editMovieForm(FlaskForm):
    new_rating = FloatField(label="Your Rating out of 10 e.g. 7.5",
                            validators=[DataRequired(), NumberRange(min=0, max=10)])
    new_review = StringField(label="Your Review", validators=[DataRequired(), Length(min=4)])
    submit = SubmitField(label="DONE")


class addMovieForm(FlaskForm):
    movie_title = StringField(label="Movie Title", validators=[DataRequired()])
    add_btn = SubmitField(label="Add Movie")


with app.app_context():
    # db.drop_all()    #to be used incase of change to db model
    db.create_all()

# with app.app_context():
#     new_movie = Movie(
#         title="Phone Booth",
#         year=2002,
#         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#         rating=7.3,
#         ranking=10,
#         review="My favourite character was the caller.",
#         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#     )
#     db.session.add(new_movie)
#     db.session.commit()


@app.route('/edit/id=<movie_id>', methods=['GET', 'POST'])
def edit(movie_id):
    editform = editMovieForm()
    if request.method == 'GET':
        with app.app_context():
            selecMovie = db.session.query(Movie).filter_by(id=movie_id).first()
            return render_template('edit.html', movie=selecMovie, form=editform)
    else:
        if editform.validate_on_submit():
            with app.app_context():
                selecMovie = db.session.query(Movie).filter_by(id=movie_id).first()
                selecMovie.rating = editform.new_rating.data
                selecMovie.review = editform.new_review.data
                db.session.commit()
                return redirect(url_for('home'))


@app.route('/delete/id=<movie_id>')
def delete(movie_id):
    with app.app_context():
        selecMovie = db.session.query(Movie).filter_by(id=movie_id).first()
        db.session.delete(selecMovie)
        db.session.commit()
        return redirect(url_for('home'))


@app.route('/add', methods=['GET', 'POST'])
def add():
    add_form = addMovieForm()
    if request.method == 'GET':
        return render_template("add.html", form=add_form)
    else:
        resp = requests.get("https://api.themoviedb.org/3/search/movie",
                            params={'api_key': TMDB_API_KEY, 'query': add_form.movie_title.data})
        search_data = resp.json()['results']
        return render_template('select.html', movie_data=search_data)


@app.route('/add/<tmdb_movie_id>', methods=['GET', 'POST'])
def add_from_tmdb(tmdb_movie_id):
    resp = requests.get(f"https://api.themoviedb.org/3/movie/{tmdb_movie_id}", params={'api_key': TMDB_API_KEY})
    movie_data = resp.json()
    editform = editMovieForm()
    if request.method == 'GET':
        with app.app_context():
            new_movie = Movie(title=movie_data['original_title'],
                              year=movie_data['release_date'].split("-")[0],
                              description=movie_data['overview'],
                              img_url=TMDB_IMG_URL + movie_data['poster_path']
                              )
            db.session.add(new_movie)
            db.session.commit()
            selecMovie = db.session.query(Movie).filter_by(title=movie_data['original_title']).first()
            return render_template('edit.html', movie=selecMovie, form=editform)
    else:
        with app.app_context():
            selecMovie = db.session.query(Movie).filter_by(title=movie_data['original_title']).first()
            selecMovie.rating = editform.new_rating.data
            selecMovie.review = editform.new_review.data
            db.session.commit()
            return redirect(url_for('home'))



def getmovielist():
    with app.app_context():
        allmovies = db.session.query(Movie).all()
        return allmovies


@app.route("/")
def home():
    with app.app_context():
        all_movies = db.session.query(Movie).order_by(Movie.rating).all()
        for i in range(len(all_movies)):
            all_movies[i].ranking = len(all_movies) - i
            db.session.commit()
        return render_template("index.html", movies=all_movies)


if __name__ == '__main__':
    app.run(debug=True)
