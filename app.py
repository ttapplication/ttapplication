from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'una_chiave_segreta_molto_sicura'
bcrypt = Bcrypt(app)

# Configurazione del database
DB_NAME = "shopping_list.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    plain_password TEXT NOT NULL,
                    first_name TEXT NOT NULL DEFAULT '',
                    last_name TEXT NOT NULL DEFAULT '')''')
    c.execute('''CREATE TABLE IF NOT EXISTS shopping_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    item TEXT NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    amount REAL NOT NULL,
                    spender TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    activity_date TEXT NOT NULL,
                    activity_time TEXT NOT NULL DEFAULT '00:00',
                    description TEXT NOT NULL,
                    location TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS activity_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL UNIQUE,
                    color TEXT NOT NULL DEFAULT '#000000')''')
    c.execute('''CREATE TABLE IF NOT EXISTS maintenance_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS expense_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bike_maintenance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    maintenance_date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS useful_numbers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    description TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id))''')
    default_expense_types = [("Cibo",), ("Trasporti",), ("Bollette",), ("Svago",), ("Altro",)]
    c.executemany("INSERT OR IGNORE INTO expense_types (description) VALUES (?)", default_expense_types)
    conn.commit()
    conn.close()

# Template HTML con CSS e JavaScript
template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Lista della Spesa</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; color: #333; }
        h1 { font-size: 24px; margin-bottom: 20px; }
        h2 { font-size: 20px; margin-bottom: 15px; }
        .container { max-width: 100%; padding: 20px; }
        .form-container { margin-bottom: 20px; }
        input[type="text"], input[type="password"], input[type="number"], input[type="date"], input[type="time"], input[type="color"] { 
            width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }
        input[type="number"] { width: 80px; }
        input[type="time"] { width: 120px; }
        input[type="color"] { height: 40px; padding: 0; }
        select { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }
        button { 
            width: 100%; padding: 12px; border: none; border-radius: 8px; color: white; font-size: 16px; cursor: pointer; 
            transition: transform 0.2s, background-color 0.2s; }
        button:hover { transform: scale(1.02); }
        .menu { display: flex; flex-direction: column; gap: 10px; }
        .menu-btn-1 { background: #28a745; }
        .menu-btn-1:hover { background: #218838; }
        .menu-btn-2 { background: #007bff; }
        .menu-btn-2:hover { background: #0069d9; }
        .menu-btn-3 { background: #ff9800; }
        .menu-btn-3:hover { background: #e68a00; }
        .menu-btn-4 { background: #6f42c1; }
        .menu-btn-4:hover { background: #5e35b1; }
        .menu-btn-5 { background: #17a2b8; }
        .menu-btn-5:hover { background: #138496; }
        .menu-btn-6 { background: #dc3545; }
        .menu-btn-6:hover { background: #c82333; }
        .menu-btn-7 { background: #ffc107; }
        .menu-btn-7:hover { background: #e0a800; }
        .remove-btn { background: #dc3545; width: auto; padding: 8px 16px; }
        .remove-btn:hover { background: #c82333; }
        .link-btn { background: #007bff; width: auto; padding: 10px 20px; }
        .link-btn:hover { background: #0069d9; }
        .back-btn { background: #6c757d; margin-top: 20px; }
        .back-btn:hover { background: #5a6268; }
        .settings-btn, .calendar-btn { background: none; border: none; font-size: 24px; cursor: pointer; margin-right: 10px; }
        .item, .expense-item, .activity-item, .maintenance-item, .number-item { 
            background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
            display: flex; justify-content: space-between; align-items: center; }
        .item-content { display: flex; justify-content: space-between; width: 100%; flex-wrap: wrap; }
        .item-description { flex-grow: 1; }
        .item-quantity { margin-left: 10px; color: #555; }
        .item-notes { margin-left: 10px; color: #777; font-style: italic; }
        .expense-item span, .activity-item span, .maintenance-item span, .number-item span { flex-grow: 1; }
        .color-box { display: inline-block; width: 20px; height: 20px; margin-left: 10px; vertical-align: middle; }
        .empty { color: #777; font-style: italic; text-align: center; }
        .error { color: #dc3545; margin-top: 10px; text-align: center; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .header-right { display: flex; align-items: center; }
        .content { display: none; margin-top: 20px; }
        .content.active { display: block; }
        .subcontent { display: none; }
        .subcontent.active { display: block; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #e9ecef; }
        canvas { max-width: 100%; margin-top: 20px; }
        .calendar { display: none; margin-top: 20px; }
        .calendar.active { display: block; }
        .calendar-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .calendar-days { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; }
        .calendar-day { background: white; padding: 10px; border-radius: 8px; text-align: center; cursor: pointer; }
        .calendar-day:hover { background: #e9ecef; }
        .activity-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin: 2px; }
        .logo { display: block; margin: 20px auto; max-width: 200px; }
        @media (min-width: 768px) {
            .container { max-width: 600px; margin: 0 auto; }
            .menu { max-width: 300px; }
        }
    </style>
    <script>
        function showSection(sectionId) {
            document.querySelectorAll('.content').forEach(content => content.classList.remove('active'));
            document.getElementById(sectionId).classList.add('active');
            document.querySelector('.menu').style.display = 'none';
            document.querySelector('.header').style.display = 'none';
            localStorage.setItem('activeSection', sectionId);
            if (sectionId === 'expense-report') {
                showSubSection(document.getElementById('expense-options').value);
            }
        }
        function showMenu() {
            document.querySelectorAll('.content').forEach(content => content.classList.remove('active'));
            document.querySelector('.menu').style.display = 'flex';
            document.querySelector('.header').style.display = 'flex';
            localStorage.removeItem('activeSection');
        }
        function showSettings() {
            document.querySelectorAll('.content').forEach(content => content.classList.remove('active'));
            document.querySelector('.menu').style.display = 'none';
            document.querySelector('.header').style.display = 'none';
            document.getElementById('settings').classList.add('active');
            localStorage.setItem('activeSection', 'settings');
        }
        function showSubSection(subSectionId) {
            document.querySelectorAll('.subcontent').forEach(content => content.classList.remove('active'));
            document.getElementById(subSectionId).classList.add('active');
            localStorage.setItem('activeSubSection', subSectionId);
        }
        window.onload = function() {
            const urlParams = new URLSearchParams(window.location.search);
            const section = urlParams.get('section') || localStorage.getItem('activeSection');
            if (section) {
                if (section === 'settings') {
                    showSettings();
                } else {
                    showSection(section);
                }
            } else {
                document.querySelector('.menu').style.display = 'flex';
                document.querySelector('.header').style.display = 'flex';
            }
        }
        function updateSubSection() {
            const selected = document.getElementById('expense-options').value;
            showSubSection(selected);
        }
        function toggleCalendar() {
            const calendar = document.getElementById('weekly-calendar');
            calendar.classList.toggle('active');
        }
        function changeWeek(offset) {
            const currentWeekStart = new Date(document.getElementById('week-start').value);
            currentWeekStart.setDate(currentWeekStart.getDate() + (offset * 7));
            document.getElementById('week-start').value = currentWeekStart.toISOString().split('T')[0];
            updateCalendar();
        }
        function updateCalendar() {
            const weekStart = new Date(document.getElementById('week-start').value);
            const days = document.querySelectorAll('.calendar-day');
            const activities = JSON.parse(document.getElementById('activities-data').textContent);
            const activityTypes = JSON.parse(document.getElementById('activity-types-data').textContent);
            const typeColorMap = {};
            activityTypes.forEach(type => typeColorMap[type[1]] = type[2]);

            days.forEach((day, index) => {
                const date = new Date(weekStart);
                date.setDate(weekStart.getDate() + index);
                const dateStr = date.toISOString().split('T')[0];
                day.dataset.date = dateStr;
                day.innerHTML = date.getDate();

                const dayActivities = activities.filter(act => act[2] === dateStr);
                if (dayActivities.length > 0) {
                    const dots = dayActivities.map(act => {
                        const color = typeColorMap[act[6]] || '#000000';
                        return `<span class="activity-dot" style="background-color: ${color};" title="${act[4]} - ${act[5]} (${act[6]})"></span>`;
                    }).join('');
                    day.innerHTML += '<br>' + dots;
                }
            });
        }
        function showDayActivities(date) {
            const activities = JSON.parse(document.getElementById('activities-data').textContent);
            const dayActivities = activities.filter(act => act[2] === date);
            const activityList = document.getElementById('day-activities-list');
            activityList.innerHTML = '';
            if (dayActivities.length > 0) {
                dayActivities.forEach(act => {
                    const li = document.createElement('li');
                    li.textContent = `${act[3]} - ${act[4]} - ${act[5]} (${act[2]} ${act[3]})`;
                    activityList.appendChild(li);
                });
            } else {
                activityList.innerHTML = '<p class="empty">Nessuna attività per questo giorno.</p>';
            }
            document.getElementById('day-activities').classList.add('active');
        }
        function closeDayActivities() {
            document.getElementById('day-activities').classList.remove('active');
        }
    </script>
</head>
<body>
    <div class="container">
        {% if not session.get('logged_in') %}
            {% if request.path == '/register' %}
                <h1>Iscriviti</h1>
                <form method="POST" action="/register">
                    <div class="form-container">
                        <input type="text" name="first_name" placeholder="Nome" required>
                        <input type="text" name="last_name" placeholder="Cognome" required>
                        <input type="text" name="username" placeholder="Nome utente" required>
                        <input type="password" name="password" placeholder="Password" required>
                        <button type="submit" style="background: #28a745;">Registrati</button>
                    </div>
                    {% if error %}
                        <p class="error">{{ error }}</p>
                    {% endif %}
                    <a href="{{ url_for('home') }}"><button type="button" class="link-btn">Torna al Login</button></a>
                    <img src="{{ url_for('static', filename='logo.png') }}" alt="Tati Adventure Logo" class="logo">
                </form>
            {% else %}
                <h1>Login</h1>
                <form method="POST" action="/login">
                    <div class="form-container">
                        <input type="text" name="username" placeholder="Nome utente" required>
                        <input type="password" name="password" placeholder="Password" required>
                        <button type="submit" style="background: #28a745;">Accedi</button>
                    </div>
                    {% if error %}
                        <p class="error">{{ error }}</p>
                    {% endif %}
                    <a href="{{ url_for('register') }}"><button type="button" class="link-btn">Iscriviti</button></a>
                    <img src="{{ url_for('static', filename='logo.png') }}" alt="Tati Adventure Logo" class="logo">
                </form>
            {% endif %}
        {% else %}
            <div class="header">
                <h1>Benvenuto, {{ session['first_name'] }} {{ session['last_name'] }}!</h1>
                <div class="header-right">
                    <button class="settings-btn" onclick="showSettings()">⚙️</button>
                    <a href="{{ url_for('logout') }}"><button style="background: #dc3545; width: auto;">Logout</button></a>
                </div>
            </div>
            
            <div class="menu">
                <button class="menu-btn-1" onclick="showSection('shopping-list')">Lista della Spesa</button>
                <button class="menu-btn-2" onclick="showSection('expense-report')">Rendicontazione Spese</button>
                <button class="menu-btn-3" onclick="showSection('task-planner')">Programmazione Attività</button>
                <button class="menu-btn-4" onclick="showSection('bike-maintenance')">Manutenzione Bicicletta</button>
                <button class="menu-btn-5" onclick="showSection('useful-numbers')">Numeri Utili</button>
                <button class="menu-btn-6" onclick="showSection('oscar-schedule')">Turnazione Oscar</button>
                <button class="menu-btn-7" onclick="showSection('notes')">Note</button>
                <img src="{{ url_for('static', filename='logo.png') }}" alt="Tati Adventure Logo" class="logo">
            </div>
            
            <div id="settings" class="content">
                <h2>Impostazioni</h2>
                <div class="menu">
                    <button class="menu-btn-2" onclick="showSection('activity-management')">Gestione Attività</button>
                    <button class="menu-btn-3" onclick="showSection('maintenance-types')">Tipi di Manutenzione</button>
                    <button class="menu-btn-1" onclick="showSection('expense-types')">Tipologia Spese</button>
                </div>
                <button class="back-btn" onclick="showMenu()">Torna al Menu</button>
            </div>
            
            <div id="activity-management" class="content">
                <h2>Gestione Attività</h2>
                <div class="form-container">
                    <form method="POST" action="/add_activity_type">
                        <input type="text" name="description" placeholder="Descrizione Attività" required>
                        <input type="color" name="color" value="#000000" title="Seleziona Colore">
                        <button type="submit" style="background: #007bff;">Aggiungi Tipo Attività</button>
                    </form>
                </div>
                {% if activity_types %}
                    {% for activity_type in activity_types %}
                        <div class="activity-item">
                            <span>{{ activity_type[1] }} <span class="color-box" style="background-color: {{ activity_type[2] }};"></span></span>
                            <a href="{{ url_for('remove_activity_type', type_id=activity_type[0]) }}"><button class="remove-btn">Rimuovi</button></a>
                        </div>
                    {% endfor %}
                {% else %}
                    <p class="empty">Nessun tipo di attività registrato.</p>
                {% endif %}
                <button class="back-btn" onclick="showMenu()">Torna al Menu</button>
            </div>
            
            <div id="maintenance-types" class="content">
                <h2>Tipi di Manutenzione</h2>
                <div class="form-container">
                    <form method="POST" action="/add_maintenance_type">
                        <input type="text" name="description" placeholder="Descrizione Tipo di Manutenzione" required>
                        <button type="submit" style="background: #ff9800;">Aggiungi Tipo di Manutenzione</button>
                    </form>
                </div>
                {% if maintenance_types %}
                    {% for maintenance_type in maintenance_types %}
                        <div class="activity-item">
                            <span>{{ maintenance_type[1] }}</span>
                            <a href="{{ url_for('remove_maintenance_type', type_id=maintenance_type[0]) }}"><button class="remove-btn">Rimuovi</button></a>
                        </div>
                    {% endfor %}
                {% else %}
                    <p class="empty">Nessun tipo di manutenzione registrato.</p>
                {% endif %}
                <button class="back-btn" onclick="showMenu()">Torna al Menu</button>
            </div>
            
            <div id="expense-types" class="content">
                <h2>Tipologia Spese</h2>
                <div class="form-container">
                    <form method="POST" action="/add_expense_type">
                        <input type="text" name="description" placeholder="Descrizione Tipo di Spesa" required>
                        <button type="submit" style="background: #28a745;">Aggiungi Tipo di Spesa</button>
                    </form>
                </div>
                {% if expense_types %}
                    {% for expense_type in expense_types %}
                        <div class="activity-item">
                            <span>{{ expense_type[1] }}</span>
                            <a href="{{ url_for('remove_expense_type', type_id=expense_type[0]) }}"><button class="remove-btn">Rimuovi</button></a>
                        </div>
                    {% endfor %}
                {% else %}
                    <p class="empty">Nessun tipo di spesa registrato.</p>
                {% endif %}
                <button class="back-btn" onclick="showMenu()">Torna al Menu</button>
            </div>
            
            <div id="shopping-list" class="content">
                <h2>Lista della Spesa</h2>
                <div class="form-container">
                    <form method="POST" action="/add">
                        <input type="text" name="item" placeholder="Aggiungi un articolo" required>
                        <input type="number" name="quantity" value="1" min="1" placeholder="Quantità">
                        <input type="text" name="notes" placeholder="Note (opzionale)">
                        <button type="submit" style="background: #28a745;">Aggiungi</button>
                    </form>
                </div>
                {% if items %}
                    {% for item in items %}
                        <div class="item">
                            <div class="item-content">
                                <span class="item-description">{{ item[1] }}</span>
                                <span class="item-quantity">({{ item[2] }})</span>
                                {% if item[3] %}
                                    <span class="item-notes">{{ item[3] }}</span>
                                {% endif %}
                            </div>
                            <a href="{{ url_for('remove_item', item_id=item[0]) }}"><button class="remove-btn">Rimuovi</button></a>
                        </div>
                    {% endfor %}
                {% else %}
                    <p class="empty">La lista è vuota! Aggiungi qualcosa da acquistare.</p>
                {% endif %}
                <button class="back-btn" onclick="showMenu()">Torna al Menu</button>
            </div>
            
            <div id="expense-report" class="content">
                <h2>Rendicontazione Spese</h2>
                <select id="expense-options" onchange="updateSubSection()">
                    <option value="add-expense">Aggiungi Spesa</option>
                    <option value="monthly-totals">Spese Totali Mensili</option>
                    <option value="yearly-by-description">Spese per Descrizione (Annue)</option>
                    <option value="expense-chart">Grafico Spese Mensili</option>
                </select>
                
                <div id="add-expense" class="subcontent">
                    <div class="form-container">
                        <form method="POST" action="/add_expense">
                            <input type="date" name="date" required>
                            <select name="description" required>
                                {% for expense_type in expense_types %}
                                    <option value="{{ expense_type[1] }}">{{ expense_type[1] }}</option>
                                {% endfor %}
                            </select>
                            <input type="number" name="amount" step="0.01" min="0" placeholder="Importo (€)" required>
                            <input type="text" name="spender" value="{{ session['first_name'] }} {{ session['last_name'] }}" placeholder="Chi ha speso" required>
                            <button type="submit" style="background: #007bff;">Aggiungi Spesa</button>
                        </form>
                    </div>
                    {% if expenses %}
                        {% for expense in expenses %}
                            <div class="expense-item">
                                <span>{{ expense[2] }} - {{ expense[3] }} - €{{ "%.2f"|format(expense[4]) }} ({{ expense[5] }})</span>
                                <a href="{{ url_for('remove_expense', expense_id=expense[0]) }}"><button class="remove-btn">Rimuovi</button></a>
                            </div>
                        {% endfor %}
                    {% else %}
                        <p class="empty">Nessuna spesa registrata.</p>
                    {% endif %}
                </div>
                
                <div id="monthly-totals" class="subcontent">
                    <h3>Spese Totali Mensili</h3>
                    {% if monthly_totals %}
                        <table>
                            <tr><th>Mese</th><th>Totale (€)</th></tr>
                            {% for month, total in monthly_totals.items() %}
                                <tr><td>{{ month }}</td><td>{{ "%.2f"|format(total) }}</td></tr>
                            {% endfor %}
                        </table>
                    {% else %}
                        <p class="empty">Nessun dato disponibile.</p>
                    {% endif %}
                </div>
                
                <div id="yearly-by-description" class="subcontent">
                    <h3>Spese Totali per Descrizione (Annue)</h3>
                    {% if yearly_by_description %}
                        <table>
                            <tr><th>Descrizione</th><th>Totale (€)</th></tr>
                            {% for desc, total in yearly_by_description.items() %}
                                <tr><td>{{ desc }}</td><td>{{ "%.2f"|format(total) }}</td></tr>
                            {% endfor %}
                        </table>
                    {% else %}
                        <p class="empty">Nessun dato disponibile.</p>
                    {% endif %}
                </div>
                
                <div id="expense-chart" class="subcontent">
                    <h3>Grafico Spese Mensili (Ultimo Anno)</h3>
                    {% if monthly_totals %}
                        <canvas id="expenseChart"></canvas>
                        <script>
                            const ctx = document.getElementById('expenseChart').getContext('2d');
                            const chartData = {
                                labels: [{% for month in monthly_totals.keys() %}'{{ month }}',{% endfor %}],
                                datasets: [{
                                    label: 'Spese Mensili (€)',
                                    data: [{% for total in monthly_totals.values() %}{{ total }},{% endfor %}],
                                    backgroundColor: 'rgba(0, 123, 255, 0.5)',
                                    borderColor: 'rgba(0, 123, 255, 1)',
                                    borderWidth: 1
                                }]
                            };
                            new Chart(ctx, {
                                type: 'bar',
                                data: chartData,
                                options: {
                                    scales: {
                                        y: { beginAtZero: true }
                                    }
                                }
                            });
                        </script>
                    {% else %}
                        <p class="empty">Nessun dato disponibile per il grafico.</p>
                    {% endif %}
                </div>
                <button class="back-btn" onclick="showMenu()">Torna al Menu</button>
            </div>
            
            <div id="task-planner" class="content">
                <h2>Programmazione Attività</h2>
                <div class="form-container">
                    <form method="POST" action="/add_activity">
                        <input type="date" name="activity_date" required>
                        <input type="time" name="activity_time" required>
                        <input type="text" name="description" placeholder="Descrizione Attività" required>
                        <input type="text" name="location" placeholder="Luogo Attività" required>
                        <select name="activity_type" required>
                            {% for activity_type in activity_types %}
                                <option value="{{ activity_type[1] }}">{{ activity_type[1] }}</option>
                            {% endfor %}
                        </select>
                        <button type="submit" style="background: #ff9800;">Aggiungi Attività</button>
                    </form>
                </div>
                <button class="calendar-btn" onclick="toggleCalendar()">📅</button>
                <div id="weekly-calendar" class="calendar">
                    <div class="calendar-header">
                        <button onclick="changeWeek(-1)">◄</button>
                        <input type="date" id="week-start" value="{{ today }}" onchange="updateCalendar()" style="width: auto;">
                        <button onclick="changeWeek(1)">►</button>
                    </div>
                    <div class="calendar-days">
                        <div class="calendar-day" onclick="showDayActivities(this.dataset.date)"></div>
                        <div class="calendar-day" onclick="showDayActivities(this.dataset.date)"></div>
                        <div class="calendar-day" onclick="showDayActivities(this.dataset.date)"></div>
                        <div class="calendar-day" onclick="showDayActivities(this.dataset.date)"></div>
                        <div class="calendar-day" onclick="showDayActivities(this.dataset.date)"></div>
                        <div class="calendar-day" onclick="showDayActivities(this.dataset.date)"></div>
                        <div class="calendar-day" onclick="showDayActivities(this.dataset.date)"></div>
                    </div>
                </div>
                <div id="day-activities" class="calendar" style="display: none;">
                    <h3>Attività del Giorno</h3>
                    <ul id="day-activities-list"></ul>
                    <button class="back-btn" onclick="closeDayActivities()">Chiudi</button>
                </div>
                <script id="activities-data" type="application/json">{{ activities | tojson }}</script>
                <script id="activity-types-data" type="application/json">{{ activity_types | tojson }}</script>
                <script>updateCalendar();</script>
                {% if activities %}
                    {% for activity in activities %}
                        <div class="activity-item">
                            <span>{{ activity[2] }} {{ activity[3] }} - {{ activity[4] }} - {{ activity[5] }} ({{ activity[6] }})</span>
                            <a href="{{ url_for('remove_activity', activity_id=activity[0]) }}"><button class="remove-btn">Rimuovi</button></a>
                        </div>
                    {% endfor %}
                {% else %}
                    <p class="empty">Nessuna attività programmata.</p>
                {% endif %}
                <button class="back-btn" onclick="showMenu()">Torna al Menu</button>
            </div>
            
            <div id="bike-maintenance" class="content">
                <h2>Manutenzione Bicicletta</h2>
                <div class="form-container">
                    <form method="POST" action="/add_maintenance">
                        <input type="date" name="maintenance_date" required>
                        <select name="description" required>
                            {% for maintenance_type in maintenance_types %}
                                <option value="{{ maintenance_type[1] }}">{{ maintenance_type[1] }}</option>
                            {% endfor %}
                        </select>
                        <button type="submit" style="background: #6f42c1;">Aggiungi Manutenzione</button>
                    </form>
                </div>
                {% if maintenances %}
                    {% for maintenance in maintenances %}
                        <div class="maintenance-item">
                            <span>{{ maintenance[2] }} - {{ maintenance[3] }}</span>
                            <a href="{{ url_for('remove_maintenance', maintenance_id=maintenance[0]) }}"><button class="remove-btn">Rimuovi</button></a>
                        </div>
                    {% endfor %}
                {% else %}
                    <p class="empty">Nessuna manutenzione registrata.</p>
                {% endif %}
                <button class="back-btn" onclick="showMenu()">Torna al Menu</button>
            </div>
            
            <div id="useful-numbers" class="content">
                <h2>Numeri Utili</h2>
                <div class="form-container">
                    <form method="POST" action="/add_number">
                        <input type="text" name="description" placeholder="Descrizione" required>
                        <input type="text" name="phone_number" placeholder="Numero di telefono" required>
                        <input type="text" name="notes" placeholder="Note">
                        <button type="submit" style="background: #17a2b8;">Aggiungi Numero</button>
                    </form>
                </div>
                {% if numbers %}
                    <table>
                        <tr><th>Descrizione</th><th>Numero</th><th>Note</th><th>Azione</th></tr>
                        {% for number in numbers %}
                            <tr>
                                <td>{{ number[2] }}</td>
                                <td>{{ number[3] }}</td>
                                <td>{{ number[4] or '' }}</td>
                                <td><a href="{{ url_for('remove_number', number_id=number[0]) }}"><button class="remove-btn">Rimuovi</button></a></td>
                            </tr>
                        {% endfor %}
                    </table>
                {% else %}
                    <p class="empty">Nessun numero utile registrato.</p>
                {% endif %}
                <button class="back-btn" onclick="showMenu()">Torna al Menu</button>
            </div>
            
            <div id="oscar-schedule" class="content">
                <h2>Turnazione Oscar</h2>
                <p>Funzionalità in sviluppo...</p>
                <button class="back-btn" onclick="showMenu()">Torna al Menu</button>
            </div>
            
            <div id="notes" class="content">
                <h2>Note</h2>
                <p>Funzionalità in sviluppo...</p>
                <button class="back-btn" onclick="showMenu()">Torna al Menu</button>
            </div>
        {% endif %}
    </div>
</body>
</html>
'''

# Inizializza o aggiorna il database all'avvio
init_db()

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template_string(template, error=None)
    user_id = session.get('user_id')
    today = datetime.now().strftime('%Y-%m-%d')
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT id, item, quantity, notes FROM shopping_list")
        items = c.fetchall()
        c.execute("SELECT id, user_id, date, description, amount, spender FROM expenses")
        expenses = c.fetchall()
        c.execute("SELECT id, user_id, activity_date, activity_time, description, location, activity_type FROM activities")
        activities = c.fetchall()
        c.execute("SELECT id, description, color FROM activity_types")
        activity_types = c.fetchall()
        c.execute("SELECT id, description FROM maintenance_types ORDER BY description ASC")
        maintenance_types = c.fetchall()
        c.execute("SELECT id, description FROM expense_types")
        expense_types = c.fetchall()
        c.execute("SELECT id, user_id, maintenance_date, description FROM bike_maintenance")
        maintenances = c.fetchall()
        c.execute("SELECT id, user_id, description, phone_number, notes FROM useful_numbers ORDER BY description ASC")
        numbers = c.fetchall()

    monthly_totals = defaultdict(float)
    yearly_by_description = defaultdict(float)
    current_year = datetime.now().year

    for expense in expenses:
        date = datetime.strptime(expense[2], '%Y-%m-%d')
        month_key = date.strftime('%Y-%m')
        yearly_key = date.year
        monthly_totals[month_key] += float(expense[4])
        if yearly_key == current_year:
            yearly_by_description[expense[3]] += float(expense[4])

    section = request.args.get('section')
    return render_template_string(template, items=items, expenses=expenses, activities=activities,
                                 activity_types=activity_types, maintenance_types=maintenance_types,
                                 expense_types=expense_types, monthly_totals=dict(monthly_totals),
                                 yearly_by_description=dict(yearly_by_description), today=today,
                                 maintenances=maintenances, numbers=numbers)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT id, password, first_name, last_name FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        if user and bcrypt.check_password_hash(user[1], password):
            session['logged_in'] = True
            session['user_id'] = user[0]
            session['username'] = username
            session['first_name'] = user[2]
            session['last_name'] = user[3]
            return redirect(url_for('home'))
    return render_template_string(template, error="Nome utente o password errati")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        plain_pw = password
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password, plain_password, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                         (username, hashed_pw, plain_pw, first_name, last_name))
                conn.commit()
                return redirect(url_for('home'))
            except sqlite3.IntegrityError:
                return render_template_string(template, error="Nome utente già in uso")
    return render_template_string(template, error=None)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('first_name', None)
    session.pop('last_name', None)
    return redirect(url_for('home'))

@app.route('/add', methods=['POST'])
def add_item():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    item = request.form['item'].strip()
    quantity = int(request.form.get('quantity', 1))
    notes = request.form.get('notes', '').strip() or None
    user_id = session.get('user_id')
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT item FROM shopping_list WHERE item = ?", (item,))
        if not c.fetchone():
            c.execute("INSERT INTO shopping_list (user_id, item, quantity, notes) VALUES (?, ?, ?, ?)", (user_id, item, quantity, notes))
            conn.commit()
    return redirect(url_for('home'))

@app.route('/remove_item/<int:item_id>')
def remove_item(item_id):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM shopping_list WHERE id = ?", (item_id,))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    date = request.form['date']
    description = request.form['description']
    amount = float(request.form['amount'])
    spender = request.form['spender'].strip()
    user_id = session.get('user_id')
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO expenses (user_id, date, description, amount, spender) VALUES (?, ?, ?, ?, ?)",
                 (user_id, date, description, amount, spender))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/remove_expense/<int:expense_id>')
def remove_expense(expense_id):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/add_activity', methods=['POST'])
def add_activity():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    activity_date = request.form['activity_date']
    activity_time = request.form['activity_time']
    description = request.form['description'].strip()
    location = request.form['location'].strip()
    activity_type = request.form['activity_type']
    user_id = session.get('user_id')
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO activities (user_id, activity_date, activity_time, description, location, activity_type) VALUES (?, ?, ?, ?, ?, ?)",
                 (user_id, activity_date, activity_time, description, location, activity_type))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/remove_activity/<int:activity_id>')
def remove_activity(activity_id):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/add_activity_type', methods=['POST'])
def add_activity_type():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    description = request.form['description'].strip()
    color = request.form['color']
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO activity_types (description, color) VALUES (?, ?)", (description, color))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
    return redirect(url_for('home'))

@app.route('/remove_activity_type/<int:type_id>')
def remove_activity_type(type_id):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM activity_types WHERE id = ?", (type_id,))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/add_maintenance_type', methods=['POST'])
def add_maintenance_type():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    description = request.form['description'].strip()
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO maintenance_types (description) VALUES (?)", (description,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
    return redirect(url_for('home'))

@app.route('/remove_maintenance_type/<int:type_id>')
def remove_maintenance_type(type_id):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM maintenance_types WHERE id = ?", (type_id,))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/add_expense_type', methods=['POST'])
def add_expense_type():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    description = request.form['description'].strip()
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO expense_types (description) VALUES (?)", (description,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
    return redirect(url_for('home'))

@app.route('/remove_expense_type/<int:type_id>')
def remove_expense_type(type_id):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM expense_types WHERE id = ?", (type_id,))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/add_maintenance', methods=['POST'])
def add_maintenance():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    maintenance_date = request.form['maintenance_date']
    description = request.form['description']
    user_id = session.get('user_id')
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO bike_maintenance (user_id, maintenance_date, description) VALUES (?, ?, ?)",
                 (user_id, maintenance_date, description))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/remove_maintenance/<int:maintenance_id>')
def remove_maintenance(maintenance_id):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM bike_maintenance WHERE id = ?", (maintenance_id,))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/add_number', methods=['POST'])
def add_number():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    description = request.form['description'].strip()
    phone_number = request.form['phone_number'].strip()
    notes = request.form['notes'].strip() or None
    user_id = session.get('user_id')
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO useful_numbers (user_id, description, phone_number, notes) VALUES (?, ?, ?, ?)",
                 (user_id, description, phone_number, notes))
        conn.commit()
    return redirect(url_for('home'))

@app.route('/remove_number/<int:number_id>')
def remove_number(number_id):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM useful_numbers WHERE id = ?", (number_id,))
        conn.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)