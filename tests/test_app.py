import unittest
from app import app, db
from models import User

class TestApp(unittest.TestCase):
    def setUp(self):
        """Настроим тестовое окружение"""
        self.app = app.test_client()
        self.app.testing = True
        # Очистим базу данных перед каждым тестом
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Очистим базу данных после каждого теста"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_register_user(self):
        """Тестирование регистрации пользователя"""
        response = self.app.post('/register', data=dict(
            username='testuser',
            password='password123',
        ), follow_redirects=True)

        # Декодируем ответ перед сравнением
        response_data = response.data.decode('utf-8')

        # Проверяем, что в ответе есть сообщение о регистрации
        self.assertIn('Пользователь успешно зарегистрирован!', response_data)


if __name__ == '__main__':
    unittest.main()
