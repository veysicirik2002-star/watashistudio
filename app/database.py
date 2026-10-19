import sqlite3
from flask import current_app

def get_db():
    db_path = current_app.config.get('DATABASE_URL', 'smartlead.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(app):
    db_path = app.config.get('DATABASE_URL', 'smartlead.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isim TEXT NOT NULL,
            telefon TEXT NOT NULL,
            mesaj TEXT,
            tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def lead_ekle(isim, telefon, mesaj=""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO leads (isim, telefon, mesaj) VALUES (?, ?, ?)',
        (isim, telefon, mesaj)
    )
    conn.commit()
    yeni_id = cursor.lastrowid
    conn.close()
    return yeni_id

def tum_leadler():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, isim, telefon, mesaj, tarih FROM leads ORDER BY id DESC')
    satirlar = cursor.fetchall()
    conn.close()
    return [dict(satir) for satir in satirlar]


def lead_sil(lead_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM leads WHERE id = ?', (lead_id,))
    conn.commit()
    silinen = cursor.rowcount
    conn.close()
    return silinen
