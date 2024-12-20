import unittest
from app import app, db
from models import User, Ticket
from flask import json

class FlaskAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app
        cls.client = cls.app.test_client()
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'  # Используем тестовую БД
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(cls.app)
        with cls.app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.drop_all()

    def setUp(self):
        # добавляем тестового пользователя
        with self.app.app_context():
            user = User(username="testuser", password="password", role="user")
            db.session.add(user)
            db.session.commit()
            self.test_user = user

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_register(self):
        response = self.client.post('/register', data={
            'username': 'newuser',
            'password': 'newpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Пользователь успешно зарегистрирован!', response.data)

    def test_login(self):
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Заявки на техподдержку', response.data)

    def test_create_ticket(self):
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password',
        })
        response = self.client.post('/tickets', data={
            'title': 'Test Ticket',
            'description': 'This is a test ticket.',
        })
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            ticket = Ticket.query.first()
            self.assertEqual(ticket.title, 'Test Ticket')

    def test_view_tickets(self):
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password',
        })
        response = self.client.get('/tickets')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Ticket', response.data)

    def test_delete_ticket(self):
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password',
        })
        ticket = Ticket(title='Delete me', description='This is a ticket to delete', user_id=self.test_user.id)
        db.session.add(ticket)
        db.session.commit()

        ticket_id = ticket.id
        response = self.client.delete(f'/tickets/{ticket_id}')
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            deleted_ticket = Ticket.query.get(ticket_id)
            self.assertIsNone(deleted_ticket)

    def test_admin_view_users(self):
        self.test_user.role = 'admin'
        db.session.commit()
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password',
        })
        response = self.client.get('/users')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'testuser', response.data)
