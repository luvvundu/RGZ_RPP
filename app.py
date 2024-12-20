from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import db, User, Ticket
from forms import RegistrationForm, LoginForm, TicketForm
# инициализация Flask приложения и конфигурация базы данных
app = Flask(__name__)
app.secret_key = "123"
user_db = "postgres"
host_ip = "127.0.0.1"
host_port = "5432"
database_name = "rpp_lv"
password = "korea231"
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user_db}:{password}@{host_ip}:{host_port}/{database_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# реализация маршрута главной страницы
@app.route('/')
def home():
    return render_template('index.html')

# реализация маршрута регистрации пользователя с использованием формы
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data, password=form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Пользователь успешно зарегистрирован!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# реализация маршрута логина пользователя с проверкой пароля
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('get_tickets'))
        flash('Неверные имя пользователя или пароль', 'danger')
    return render_template('login.html', form=form)

# реализация маршрута получения заявок и создания новых
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

# реализация маршрута для отображения заявки по id с проверкой доступа
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

# реализация маршрута для обновления заявки с проверкой прав пользователя
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

# реализация маршрута для удаления заявки с проверкой прав доступа
@app.route('/tickets/<int:ticket_id>', methods=['DELETE'])
@login_required
def delete_ticket(ticket_id):
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        flash('Заявка не найдена', 'danger')
        return redirect(url_for('get_tickets'))

    # проверяем, есть ли у пользователя права на удаление
    if current_user.role != 'admin' and ticket.user_id != current_user.id:
        flash('Нет доступа', 'danger')
        return redirect(url_for('get_tickets'))

    # удаляем заявку из базы данных
    db.session.delete(ticket)
    db.session.commit()
    flash('Заявка успешно удалена', 'success')
    return redirect(url_for('get_tickets'))

# реализация маршрута для отображения всех пользователей (доступно только админам)
@app.route('/users', methods=['GET'])
@login_required
def get_users():
    if current_user.role != 'admin':
        flash('Нет доступа', 'danger')
        return redirect(url_for('get_tickets'))

    users = User.query.all()
    return render_template('users.html', users=users)

# реализация маршрута для изменения роли пользователя (доступно только админам)
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

# реализация маршрута для выхода пользователя из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# создание таблиц базы данных при старте приложения
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # создание таблиц в базе данных
    app.run(debug=True)