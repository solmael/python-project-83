from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
import psycopg2
import logging
from .url_validator import validate_url

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не указана в .env")

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')


def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        app.logger.error(f"Ошибка подключения к БД: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        url = request.form['url'].strip()

        normalized_url, error = validate_url(url)

        if error:
            flash(error, 'error')
            return redirect(url_for('index'))

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO urls (name) VALUES (%s) RETURNING id", (normalized_url,))
            url_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()

            flash('URL успешно добавлен', 'success')
            return redirect(url_for('url_detail', id=url_id))

        except psycopg2.IntegrityError as e:
            conn.rollback()
            flash('URL уже существует', 'error')
            return redirect(url_for('index'))

        except Exception as e:
            app.logger.error(f"Ошибка добавления в БД: {e}")
            flash('Ошибка добавления URL', 'error')
            return redirect(url_for('index'))

    return render_template('index.html')


@app.route('/urls/<int:id>/checks', methods=['POST'])
def create_check(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
        url = cur.fetchone()
        if not url:
            return "URL не найден", 404
        
        cur.execute(
            "INSERT INTO url_checks (url_id) VALUES (%s) RETURNING id",
            (id,)
        )
        check_id = cur.fetchone()[0]
        conn.commit()
        
        flash('Проверка запущена', 'success')
        return redirect(url_for('url_detail', id=id))
    
    except Exception as e:
        app.logger.error(f"Ошибка создания проверки: {e}")
        conn.rollback()
        flash('Ошибка создания проверки', 'error')
        return redirect(url_for('url_detail', id=id))
    finally:
        cur.close()
        conn.close()

@app.route('/add-url')
def add_url():
    return render_template('add_url.html')

@app.route('/urls')
def urls():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM urls ORDER BY created_at DESC")
        urls = cur.fetchall()
        
        return render_template('urls.html', urls=urls)
    
    except Exception as e:
        app.logger.error(f"Ошибка получения списка URL: {e}")
        flash('Ошибка загрузки данных', 'error')
        return redirect(url_for('index'))
    
    finally:
        cur.close()
        conn.close()

@app.route('/urls/<int:id>')
def url_detail(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
        url = cur.fetchone()
        
        cur.execute("SELECT * FROM url_checks WHERE url_id = %s ORDER BY created_at DESC", (id,))
        checks = cur.fetchall()
        
        if not url:
            return "URL не найден", 404
        
        return render_template('url_detail.html', url=url, checks=checks)
    
    except Exception as e:
        app.logger.error(f"Ошибка получения данных: {e}")
        flash('Ошибка загрузки данных', 'error')
        return redirect(url_for('index'))
    finally:
        cur.close()
        conn.close()