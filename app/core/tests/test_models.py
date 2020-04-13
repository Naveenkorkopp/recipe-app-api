from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):

    def test_create_user_with_email_succesful(self):
        """Test creating a new user with an email is successful"""
        email = "test_my_user@yopmail.com"
        password = "Testpass123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """New user email normalized"""
        email = "testnaveen@YOPMAIL.COM"
        user = get_user_model().objects.create_user(
            email=email,
            password='Test123'
        )
        self.assertEqual(user.email, email.lower())

    def test_new_user_valid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'test124')

    def test_create_new_superuser(self):
        """Test createing a new superuser"""
        user = get_user_model().objects.create_superuser(
            'testnaveen@yopmail.com',
            'test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
