"""Custom JWT Authentication Class for Django REST Framework."""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions\
    import InvalidToken, AuthenticationFailed
from rest_framework.authentication import CSRFCheck
from django.conf import settings
from rest_framework import exceptions


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom authentication class that gets the JWT token from cookies.

    Instead of the Authorization header.
    """

    def authenticate(self, request):
        """
        Authenticate the user using a JWT token stored in cookies.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
        tuple: A tuple of (user, validated_token) if authentication succeeds.
            None: If no token is found in cookies.

        """
        print("==== Authentication Process Started ====")
        access_token = request.COOKIES.get('access_token')

        print(f"Cookies received: {list(request.COOKIES.keys())}")

        if not access_token:
            print('No access token found in cookies')
            return None

        print(f"Access token found, length: {len(access_token)}")

        try:
            print("Attempting to validate token...")
            validated_token = self.get_validated_token(access_token)
            print("Token validated successfully")

            print("Getting user from token...")
            user = self.get_user(validated_token)

            # Skip CSRF check for login endpoint
            if (
                request.method in ['POST', 'PUT', 'PATCH', 'DELETE']
                and request.path != '/api/auth/login/'
            ):
                print("Checking CSRF for non-safe method...")
                self.enforce_csrf(request)
                print("CSRF check passed")

            return (user, validated_token)
        except InvalidToken as e:
            print(f'Invalid token error: {str(e)}')
            raise AuthenticationFailed(f'Invalid token: {str(e)}')
        except Exception as e:
            print(f'Authentication error: {str(e)}')
            raise AuthenticationFailed(str(e))

    def enforce_csrf(self, request):
        """
        Enforce CSRF validation for non-safe HTTP methods.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Raises:
            PermissionDenied: If the CSRF check fails.
        """
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            print("CSRF headers:", {
                k: v for k, v in request.headers.items()
                if 'csrf' in k.lower()
            })
            check = CSRFCheck(lambda req: None)
            reason = check.process_view(request, None, (), {})
            if reason:
                print(f'CSRF check failed: {reason}')
                raise exceptions.PermissionDenied(f'CSRF Failed: {reason}')
