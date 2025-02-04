from flask import Flask, render_template, request
import requests
import pandas as pd
import ast
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(_name_)

OMDB_API_KEY = '9787b8fa'
OMDB_API_URL = 'http://www.omdbapi.com/'

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/recommend', methods=['POST'])
def recommend():
    movies = pd.read_csv('tmdb_5000_movies.csv')
    credits = pd.read_csv('tmdb_5000_credits.csv')

    movies = movies.merge(credits, on='title')

    movies = movies[['movie_id', 'title', 'overview','genres', 'keywords', 'cast', 'crew']]

    def convert(text):
        L = []
        for i in ast.literal_eval(text):
            L.append(i['name'])
        return L

    movies.dropna(inplace=True)

    movies['genres'] = movies['genres'].apply(convert)
    movies.head()

    movies['keywords'] = movies['keywords'].apply(convert)
    movies.head()

    ast.literal_eval(
        '[{"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"}, {"id": 14, "name": "Fantasy"}, {"id": 878, "name": "Science Fiction"}]')

    movies['cast'] = movies['cast'].apply(convert)

    movies['cast'] = movies['cast'].apply(lambda x: x[0:3])

    def collapse(L):
        L1 = []
        for i in L:
            L1.append(i.replace(" ", ""))
        return L1

    movies['cast'] = movies['cast'].apply(collapse)
    movies['crew'] = movies['crew'].apply(collapse)
    movies['genres'] = movies['genres'].apply(collapse)
    movies['keywords'] = movies['keywords'].apply(collapse)

    movies['overview'] = movies['overview'].apply(lambda x: x.split())

    movies['tags'] = movies['overview'] + movies['genres'] + \
        movies['keywords'] + movies['cast'] + movies['crew']

    new = movies.drop(columns=['genres', 'keywords', 'cast', 'crew'])

    new['tags'] = new['tags'].apply(lambda x: " ".join(x))

    cv = CountVectorizer(max_features=5000, stop_words='english')

    vector = cv.fit_transform(new['tags']).toarray()

    similarity = cosine_similarity(vector)

    new[new['title'] == 'The Lego Movie'].index[0]

    def recommend(movie):
        index = new[new['title'] == movie].index[0]
        distances = sorted(
            list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
        finalMovies=[]
        TitleWordList=[]
        finalMoviesTitle=[]
        finalMoviesPosterLink=[]
        for i in distances[1:6]:
            finalMovies.append(new.iloc[i[0]].title)
            TitleWordList.append(new.iloc[i[0]].overview)
        # print(finalMovies)
        for item in TitleWordList:
            sentence=' '.join(item)
            finalMoviesTitle.append(sentence)
        # print(finalMoviesTitle)
        for x in finalMovies:
            params = {'apikey': OMDB_API_KEY, 't': x}
            response = requests.get(OMDB_API_URL, params=params)
            data = response.json()
            print(data["Poster"])
            finalMoviesPosterLink.append(data["Poster"])
        return render_template('index.html',movies=finalMovies,finalMoviesTitle=finalMoviesTitle,links=finalMoviesPosterLink)
    try:
        return recommend(request.form['movie'])
    except:
        return render_template('index.html',warning="No recommendation available for this movie!😓")


if _name_ == '_main_':
    app.run(debug=True)