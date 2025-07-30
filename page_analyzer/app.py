import logging
import os

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from .repository import DatabaseError, UrlAlreadyExists, UrlRepository

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не указана в .env")

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')

url_repo = UrlRepository(DATABASE_URL)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/urls/<int:id>')
def url_detail(id):
    try:
        url = url_repo.get_url_by_id(id)
        checks = url_repo.get_checks_by_url_id(id)
        return render_template('url_detail.html', url=url, checks=checks)
    except DatabaseError as e:
        app.logger.error(f"Ошибка получения данных: {e}")
        flash('Ошибка загрузки данных', 'danger')
        return redirect(url_for('index'))


@app.route('/urls', methods=['GET', 'POST'])
def urls():
    if request.method == 'POST':
        url = request.form['url'].strip()
        try:
            url_id = url_repo.add_url(url)
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('url_detail', id=url_id))
        except ValueError as e:
            flash(str(e), 'danger')
            urls = url_repo.get_all_urls()
            return render_template('index.html', urls=urls), 422
        except UrlAlreadyExists:
            existing_url = url_repo.get_url_by_name(url)
            flash('Страница уже существует', 'warning')
            return redirect(url_for('url_detail', id=existing_url['id']))
        except DatabaseError as e:
            app.logger.error(f"Ошибка добавления в БД: {e}")
            flash('Ошибка добавления URL', 'danger')
            urls = url_repo.get_all_urls()
            return render_template('urls.html', urls=urls), 500
    
    # get
    try:
        urls = url_repo.get_all_urls()
        return render_template('urls.html', urls=urls)
    except DatabaseError as e:
        app.logger.error(f"Ошибка получения списка URL: {e}")
        flash('Ошибка загрузки данных', 'danger')
        return render_template('index.html'), 500


@app.route('/urls/<int:id>/checks', methods=['POST'])
def create_check(id):
    try:
        success = url_repo.create_check(id)
        if success:
            flash('Страница успешно проверена', 'success')
        else:
            flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('url_detail', id=id))
    except DatabaseError as e:
        app.logger.error(f"Ошибка проверки: {e}")
        flash('Ошибка создания проверки', 'danger')
        return redirect(url_for('url_detail', id=id))