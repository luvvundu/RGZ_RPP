import unittest
from app import app, db
from models import User

class TestApp(unittest.TestCase):
    
    def setUp(self):
        """Настроим тестовое окружение"""
        # Используем in-memory базу данных для тестов
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # SQLite in-memory база данных
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Отключаем отслеживание изменений для экономии памяти

        self.app = app.test_client()  # Используем FlaskClient для тестов
        
        # Активируем контекст приложения
        self.app_context = app.app_context()
        self.app_context.push()

        # Создаём таблицы в базе данных для каждого теста
        db.create_all()

    def tearDown(self):
        """Очистим базу данных после каждого теста"""
        # Убираем контекст приложения
        self.app_context.pop()
        
        # Удаляем все данные из базы
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
