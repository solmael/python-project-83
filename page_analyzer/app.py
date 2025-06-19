from flask import Flask, render_template, request
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        # >.<
        return f"Вы ввели: {url}"
    return render_template('index.html')


@app.route('/add-url')
def add_url():
    return render_template('add_url.html')