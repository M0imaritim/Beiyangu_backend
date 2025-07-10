from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
import json

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model"""

    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'bio': 'Test bio',
            'location': 'Test Location'
        }

    def test_create_user(self):
        """Test creating a user"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.username, self.user_data['username'])
        self.assertEqual(user.bio, self.user_data['bio'])
        self.assertEqual(user.location, self.user_data['location'])
        self.assertTrue(user.check_password(self.user_data['password']))

    def test_user_str_method(self):
        """Test user string representation"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), self.user_data['email'])

    def test_username_field_is_email(self):
        """Test that USERNAME_FIELD is email"""
        self.assertEqual(User.USERNAME_FIELD, 'email')

    def test_required_fields(self):
        """Test REQUIRED_FIELDS contains username"""
        self.assertEqual(User.REQUIRED_FIELDS, ['username'])


class UserRegistrationTest(APITestCase):
    """Test cases for user registration"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.valid_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'TestPassword123!',
            'bio': 'Test bio',
            'location': 'Test Location'
        }

    def test_user_registration_success(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, self.valid_data)
        print(response.status_code, response.json())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(
            response.data['message'],
            'User registered successfully')
        self.assertIn('user', response.data['data'])
        self.assertIn('tokens', response.data['data'])
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

        # Check user was created
        user = User.objects.get(email=self.valid_data['email'])
        self.assertEqual(user.username, self.valid_data['username'])
        self.assertEqual(user.bio, self.valid_data['bio'])
        self.assertEqual(user.location, self.valid_data['location'])

    def test_user_registration_password_mismatch(self):
        """Test registration with password mismatch"""
        data = self.valid_data.copy()
        data['password_confirm'] = 'differentpassword'

        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('password', response.data['errors'])

    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create first user
        User.objects.create_user(
            email=self.valid_data['email'],
            username='firstuser',
            password='password123'
        )

        response = self.client.post(self.register_url, self.valid_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('email', response.data['errors'])

    def test_user_registration_invalid_email(self):
        """Test registration with invalid email"""
        data = self.valid_data.copy()
        data['email'] = 'invalid-email'

        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('email', response.data['errors'])

    def test_user_registration_weak_password(self):
        """Test registration with weak password"""
        data = self.valid_data.copy()
        data['password'] = '123'
        data['password_confirm'] = '123'

        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('password', response.data['errors'])

    def test_user_registration_missing_required_fields(self):
        """Test registration with missing required fields"""
        data = {'email': 'test@example.com'}

        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('username', response.data['errors'])
        self.assertIn('password', response.data['errors'])


class UserLoginTest(APITestCase):
    """Test cases for user login"""

    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('login')
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'TestPassword123!'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_login_success(self):
        """Test successful user login"""
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }

        response = self.client.post(self.login_url, login_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Login successful')
        self.assertIn('user', response.data['data'])
        self.assertIn('tokens', response.data['data'])
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            'email': self.user_data['email'],
            'password': 'wrongpassword'
        }

        response = self.client.post(self.login_url, login_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Login failed')

    def test_user_login_nonexistent_user(self):
        """Test login with nonexistent user"""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'password123'
        }

        response = self.client.post(self.login_url, login_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_user_login_missing_fields(self):
        """Test login with missing fields"""
        login_data = {'email': self.user_data['email']}

        response = self.client.post(self.login_url, login_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_user_login_empty_fields(self):
        """Test login with empty fields"""
        login_data = {'email': '', 'password': ''}

        response = self.client.post(self.login_url, login_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class UserLogoutTest(APITestCase):
    """Test cases for user logout"""

    def setUp(self):
        self.client = APIClient()
        self.logout_url = reverse('logout')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!'
        )
        self.refresh_token = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh_token.access_token)

    def test_user_logout_success(self):
        """Test successful user logout"""
        self.client.cookies['refresh_token'] = str(self.refresh_token)
        self.client.cookies['access_token'] = self.access_token
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Logout successful')

        # Check cookies are deleted
        self.assertNotIn('access_token', response.cookies)
        self.assertNotIn('refresh_token', response.cookies)

    def test_user_logout_without_token(self):
        """Test logout without refresh token"""
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    @patch('rest_framework_simplejwt.tokens.RefreshToken.blacklist')
    def test_user_logout_token_blacklist_error(self, mock_blacklist):
        """Test logout with token blacklist error"""
        mock_blacklist.side_effect = Exception("Token blacklist error")

        self.client.cookies['refresh_token'] = str(self.refresh_token)

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'Logout failed')


class UserProfileTest(APITestCase):
    """Test cases for user profile"""

    def setUp(self):
        self.client = APIClient()
        self.profile_url = reverse('user_profile')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!',
            bio='Test bio',
            location='Test Location'
        )
        self.refresh_token = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh_token.access_token)

    def test_get_user_profile_authenticated(self):
        """Test getting user profile when authenticated"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], self.user.email)
        self.assertEqual(response.data['data']['username'], self.user.username)
        self.assertEqual(response.data['data']['bio'], self.user.bio)
        self.assertEqual(response.data['data']['location'], self.user.location)

    def test_get_user_profile_unauthenticated(self):
        """Test getting user profile when not authenticated"""
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenRefreshTest(APITestCase):
    """Test cases for token refresh"""

    def setUp(self):
        self.client = APIClient()
        self.refresh_url = reverse('token_refresh')
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPassword123!'
        )
        self.refresh_token = RefreshToken.for_user(self.user)

    def test_token_refresh_success(self):
        """Test successful token refresh"""
        self.client.cookies['refresh_token'] = str(self.refresh_token)

        response = self.client.post(self.refresh_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('access_token', response.cookies)

    def test_token_refresh_invalid_token(self):
        """Test token refresh with invalid token"""
        self.client.cookies['refresh_token'] = 'invalid_token'

        response = self.client.post(self.refresh_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_no_token(self):
        """Test token refresh without token"""
        response = self.client.post(self.refresh_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserSerializerTest(TestCase):
    """Test cases for user serializers"""

    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!',
            'bio': 'Test bio',
            'location': 'Test Location'
        }

    def test_user_registration_serializer_valid(self):
        """Test UserRegistrationSerializer with valid data"""
        from apps.users.serializers import UserRegistrationSerializer

        serializer = UserRegistrationSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())

    def test_user_registration_serializer_password_mismatch(self):
        """Test UserRegistrationSerializer with password mismatch"""
        from apps.users.serializers import UserRegistrationSerializer

        data = self.user_data.copy()
        data['password_confirm'] = 'differentpassword'

        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_user_serializer(self):
        """Test UserSerializer"""
        from apps.users.serializers import UserSerializer

        user = User.objects.create_user(**self.user_data)
        serializer = UserSerializer(user)

        self.assertEqual(serializer.data['email'], user.email)
        self.assertEqual(serializer.data['username'], user.username)
        self.assertEqual(serializer.data['bio'], user.bio)
        self.assertEqual(serializer.data['location'], user.location)
        self.assertIn('id', serializer.data)
        self.assertIn('created_at', serializer.data)
        print(serializer.errors)

    def test_login_serializer_valid(self):
        """Test LoginSerializer with valid data"""
        from apps.users.serializers import LoginSerializer

        # Create user first
        User.objects.create_user(**self.user_data)

        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }

        serializer = LoginSerializer(data=login_data)
        self.assertTrue(serializer.is_valid())
        self.assertIn('user', serializer.validated_data)

    def test_login_serializer_invalid_credentials(self):
        """Test LoginSerializer with invalid credentials"""
        from apps.users.serializers import LoginSerializer

        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }

        serializer = LoginSerializer(data=login_data)
        self.assertFalse(serializer.is_valid())


class IntegrationTest(APITestCase):
    """Integration tests for the complete user flow"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.profile_url = reverse('user_profile')
        self.refresh_url = reverse('token_refresh')

        self.user_data = {
            'email': 'integration@example.com',
            'username': 'integrationuser',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!',
            'bio': 'Integration test bio',
            'location': 'Integration Location'
        }

    def test_complete_user_flow(self):
        """Test complete user registration, login, profile access, and logout flow"""
        # 1. Register user
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Extract tokens from registration response
        access_token = response.data['data']['tokens']['access']
        refresh_token = response.data['data']['tokens']['refresh']

        # 2. Access profile with token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['data']['email'],
            self.user_data['email'])

        # 3. Logout
        self.client.cookies['refresh_token'] = refresh_token
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. Login again
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 5. Access profile again
        new_access_token = response.data['data']['tokens']['access']
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_refresh_flow(self):
        """Test token refresh flow"""
        # Register user
        response = self.client.post(self.register_url, self.user_data)
        refresh_token = response.data['data']['tokens']['refresh']

        # Use refresh token to get new access token
        self.client.cookies['refresh_token'] = refresh_token
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

        # Use new access token to access profile
        new_access_token = response.data['access']
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
