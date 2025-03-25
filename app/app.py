from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Inizializzazione del database
def init_db():
    conn = sqlite3.connect('gestione.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS lista_spesa 
                 (id INTEGER PRIMARY KEY, item TEXT, data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS spese 
                 (id INTEGER PRIMARY KEY, descrizione TEXT, importo REAL, data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS appuntamenti 
                 (id INTEGER PRIMARY KEY, descrizione TEXT, data TEXT)''')
    conn.commit()
    conn.close()

# Homepage
@app.route('/')
def home():
    return render_template('home.html')

# Gestione Lista Spesa
@app.route('/lista_spesa', methods=['GET', 'POST'])
def lista_spesa():
    conn = sqlite3.connect('gestione.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        if 'aggiungi' in request.form:
            item = request.form['item']
            data = datetime.now().strftime("%Y-%m-%d %H:%M")
            c.execute("INSERT INTO lista_spesa (item, data) VALUES (?, ?)", (item, data))
        elif 'cancella' in request.form:
            item_id = request.form['item_id']
            c.execute("DELETE FROM lista_spesa WHERE id = ?", (item_id,))
        conn.commit()
    
    c.execute("SELECT * FROM lista_spesa")
    items = c.fetchall()
    conn.close()
    return render_template('lista_spesa.html', items=items)

# Gestione Spese
@app.route('/spese', methods=['GET', 'POST'])
def spese():
    conn = sqlite3.connect('gestione.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        if 'aggiungi' in request.form:
            descrizione = request.form['descrizione']
            importo = float(request.form['importo'])
            data = datetime.now().strftime("%Y-%m-%d %H:%M")
            c.execute("INSERT INTO spese (descrizione, importo, data) VALUES (?, ?, ?)", 
                     (descrizione, importo, data))
        elif 'cancella' in request.form:
            spesa_id = request.form['spesa_id']
            c.execute("DELETE FROM spese WHERE id = ?", (spesa_id,))
        conn.commit()
    
    c.execute("SELECT * FROM spese")
    spese_list = c.fetchall()
    conn.close()
    return render_template('spese.html', spese=spese_list)

# Gestione Appuntamenti
@app.route('/appuntamenti', methods=['GET', 'POST'])
def appuntamenti():
    conn = sqlite3.connect('gestione.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        if 'aggiungi' in request.form:
            descrizione = request.form['descrizione']
            data = request.form['data']
            c.execute("INSERT INTO appuntamenti (descrizione, data) VALUES (?, ?)", 
                     (descrizione, data))
        elif 'cancella' in request.form:
            app_id = request.form['app_id']
            c.execute("DELETE FROM appuntamenti WHERE id = ?", (app_id,))
        conn.commit()
    
    c.execute("SELECT * FROM appuntamenti")
    app_list = c.fetchall()
    conn.close()
    return render_template('appuntamenti.html', appuntamenti=app_list)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')  # Accessibile da rete locale