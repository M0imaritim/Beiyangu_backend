from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import login
from django.conf import settings
from .models import User
from .serializers import UserRegistrationSerializer, UserSerializer, LoginSerializer


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        tokens = get_tokens_for_user(user)

        response = Response({
            'success': True,
            'message': 'User registered successfully',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': tokens
            }
        }, status=status.HTTP_201_CREATED)

        # Set cookies
        response.set_cookie(
            'access_token',
            tokens['access'],
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(
            ),
            httponly=True,
            samesite='None',  # Set to 'None' for cross-site cookies
            secure=False
        )
        response.set_cookie(
            'refresh_token',
            tokens['refresh'],
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(
            ),
            httponly=True,
            samesite='None',  # Set to 'None' for cross-site cookies
            secure=False
        )

        return response

    return Response({
        'success': False,
        'message': 'Registration failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """User login endpoint"""
    serializer = LoginSerializer(
        data=request.data, context={
            'request': request})
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        tokens = get_tokens_for_user(user)

        response = Response({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': tokens
            }
        }, status=status.HTTP_200_OK)

        # Set cookies
        response.set_cookie(
            'access_token',
            tokens['access'],
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(
            ),
            httponly=True,
            samesite='None',  # Set to 'None' for cross-site cookies
            secure=True  # Set to True in production if using HTTPS
        )
        response.set_cookie(
            'refresh_token',
            tokens['refresh'],
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(
            ),
            httponly=True,
            samesite='None',  # Set to 'None' for cross-site cookies
            secure=True
        )

        return response

    return Response({
        'success': False,
        'message': 'Login failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout_view(request):
    """User logout endpoint"""
    try:
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()

        response = Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)

        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')

        return response
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Logout failed',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def user_profile_view(request):
    """Get current user profile"""
    return Response({
        'success': True,
        'data': UserSerializer(request.user).data
    })


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            request.data['refresh'] = refresh_token

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            access_token = response.data['access']
            response.set_cookie(
                'access_token',
                access_token,
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                samesite='Lax',
                secure=False)

        return response
