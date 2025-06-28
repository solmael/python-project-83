import logging
import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from .repository import DatabaseError, UrlAlreadyExists, UrlRepository

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не указана в .env")

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')

url_repo = UrlRepository(DATABASE_URL)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url'].strip()
        try:
            url_id = url_repo.add_url(url)
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('url_detail', id=url_id))
        except ValueError:
            flash('Некорректный URL', 'error')
            return redirect(url_for('index'))
        except UrlAlreadyExists:
            existing_url = url_repo.get_url_by_name(url)
            if existing_url:
                flash('URL уже существует', 'error')
                return redirect(url_for('url_detail', id=existing_url['id']))
            else:
                flash('URL не найден в БД', 'error')
                return redirect(url_for('index'))
        except DatabaseError as e:
            app.logger.error(f"Ошибка добавления в БД: {e}")
            flash('Ошибка добавления URL', 'error')
            return redirect(url_for('index'))

    return render_template('index.html')


@app.route('/urls/<int:id>')
def url_detail(id):
    try:
        url = url_repo.get_url_by_id(id)
        checks = url_repo.get_checks_by_url_id(id)
        return render_template('url_detail.html', url=url, checks=checks)
    except DatabaseError as e:
        app.logger.error(f"Ошибка получения данных: {e}")
        flash('Ошибка загрузки данных', 'error')
        return redirect(url_for('index'))


@app.route('/urls')
def urls():
    try:
        urls = url_repo.get_all_urls()
        return render_template('urls.html', urls=urls)
    except DatabaseError as e:
        app.logger.error(f"Ошибка получения списка URL: {e}")
        flash('Ошибка загрузки данных', 'error')
        return redirect(url_for('index'))


@app.route('/urls/<int:id>/checks', methods=['POST'])
def create_check(id):
    try:
        success = url_repo.create_check(id)
        if success:
            flash('Страница успешно проверена', 'success')
        else:
            flash('URL не найден', 'error')
        return redirect(url_for('url_detail', id=id))
    except DatabaseError:
        app.logger.error("Ошибка проверки URL")
        flash('Произошла ошибка при проверке', 'error')
        return redirect(url_for('url_detail', id=id))