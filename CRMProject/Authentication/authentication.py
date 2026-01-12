# crmapp/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions
from .models import LoginUser

class LoginUserJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Returns the user associated with the given validated token.
        Overrides default behavior to use LoginUser model.
        """
        try:
            user_id = validated_token["user_id"]
        except KeyError:
            raise exceptions.AuthenticationFailed(
                "Token contained no user ID", code="invalid_token"
            )

        try:
            user = LoginUser.objects.get(id=user_id, is_active=True)
        except LoginUser.DoesNotExist:
            raise exceptions.AuthenticationFailed(
                "User not found", code="user_not_found"
            )

        return user
