import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from forms import RegistrationForm, LoginForm, TicketForm

# Загружаем переменные окружения из .env файла
load_dotenv()

# Инициализация Flask приложения и конфигурация базы данных
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Получаем секретный ключ из переменной окружения
user_db = "postgres"
host_ip = "127.0.0.1"
host_port = "5432"
database_name = "rpp_lv"
password = os.getenv('DB_PASSWORD')  # Получаем пароль из переменной окружения

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user_db}:{password}@{host_ip}:{host_port}/{database_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Реализация маршрута главной страницы
@app.route('/')
def home():
    return render_template('index.html')

# Реализация маршрута регистрации пользователя с использованием формы
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data, password=form.password.data)  # Хеширование пароля можно добавить позже
        db.session.add(new_user)
        db.session.commit()
        flash('Пользователь успешно зарегистрирован!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Реализация маршрута логина пользователя с проверкой пароля
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:  # Хеширование пароля можно добавить позже
            login_user(user)
            return redirect(url_for('get_tickets'))
        flash('Неверные имя пользователя или пароль', 'danger')
    return render_template('login.html', form=form)

# Реализация маршрута получения заявок и создания новых
@app.route('/tickets', methods=['GET', 'POST'])
@login_required
def get_tickets():
    form = TicketForm()
    if request.method == 'POST' and form.validate_on_submit():
        new_ticket = Ticket(title=form.title.data, description=form.description.data, user_id=current_user.id)
        db.session.add(new_ticket)
        db.session.commit()
        flash('Заявка успешно создана!', 'success')
        return redirect(url_for('get_tickets'))

    if current_user.role == 'admin':
        tickets = Ticket.query.all()
    else:
        tickets = Ticket.query.filter_by(user_id=current_user.id).all()

    return render_template('tickets.html', tickets=tickets, form=form)

# Реализация маршрута для отображения заявки по id с проверкой доступа
@app.route('/tickets/<int:ticket_id>', methods=['GET'])
@login_required
def get_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if ticket:
        if current_user.role == 'admin' or ticket.user_id == current_user.id:
            return render_template('ticket_detail.html', ticket=ticket)
        flash('Нет доступа', 'danger')
        return redirect(url_for('get_tickets'))
    flash('Заявка не найдена', 'danger')
    return redirect(url_for('get_tickets'))

# Реализация маршрута для обновления заявки с проверкой прав пользователя
@app.route('/tickets/<int:ticket_id>', methods=['POST'])
@login_required
def update_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        flash('Заявка не найдена', 'danger')
        return redirect(url_for('get_tickets'))
    if current_user.role != 'admin' and ticket.user_id != current_user.id:
        flash('Нет доступа', 'danger')
        return redirect(url_for('get_tickets'))

    ticket.title = request.form.get('title', ticket.title)
    ticket.description = request.form.get('description', ticket.description)
    ticket.status = request.form.get('status', ticket.status)
    db.session.commit()
    flash('Заявка успешно обновлена!', 'success')
    return redirect(url_for('get_ticket', ticket_id=ticket_id))

# Реализация маршрута для удаления заявки с проверкой прав доступа
@app.route('/tickets/<int:ticket_id>', methods=['DELETE'])
@login_required
def delete_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        flash('Заявка не найдена', 'danger')
        return redirect(url_for('get_tickets'))

    # Проверяем, есть ли у пользователя права на удаление
    if current_user.role != 'admin' and ticket.user_id != current_user.id:
        flash('Нет доступа', 'danger')
        return redirect(url_for('get_tickets'))

    # Удаляем заявку из базы данных
    db.session.delete(ticket)
    db.session.commit()
    flash('Заявка успешно удалена', 'success')
    return redirect(url_for('get_tickets'))

# Реализация маршрута для отображения всех пользователей (доступно только админам)
@app.route('/users', methods=['GET'])
@login_required
def get_users():
    if current_user.role != 'admin':
        flash('Нет доступа', 'danger')
        return redirect(url_for('get_tickets'))

    users = User.query.all()
    return render_template('users.html', users=users)

# Реализация маршрута для изменения роли пользователя (доступно только админам)
@app.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user_role(user_id):
    if current_user.role != 'admin':
        flash('Нет доступа', 'danger')
        return redirect(url_for('get_tickets'))

    user = User.query.get(user_id)
    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('get_users'))

    data = request.json
    user.role = data.get('role', user.role)
    db.session.commit()
    flash('Роль пользователя успешно обновлена', 'success')
    return redirect(url_for('get_users'))

# Реализация маршрута для выхода пользователя из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Создание таблиц базы данных при старте приложения
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # создание таблиц в базе данных
    app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true')  # Используем переменную окружения для режима отладки
