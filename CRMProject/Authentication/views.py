from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import LoginUser
import json
from rest_framework import status
import logging
import uuid
import json
from django.http import HttpResponse
from django.views import View
from django.core.mail import send_mail
# from django.utils.timezone import now
from datetime import timedelta, timezone
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from .models import LoginUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import GenericAPIView

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name="dispatch")
class LoginView(View):

    def post(self, request):
        print("LOGIN API HIT")

        try:
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return HttpResponse(
                    json.dumps({
                        "status": "fail",
                        "message": "Email and password required"
                    }),
                    content_type="application/json",
                    status=status.HTTP_400_BAD_REQUEST
                )
                

            user = LoginUser.objects.select_related("role").get(
                email=email,
                is_active=True
            )
            print("USER FOUND:", user)

            if not user.check_password(password):
                return HttpResponse(
                    json.dumps({
                        "status": "fail",
                        "message": "Invalid credentials",
                    }),
                    content_type="application/json",
                    status=status.HTTP_401_UNAUTHORIZED
                )

            refresh = RefreshToken.for_user(user)

            return HttpResponse(
                json.dumps({
                    "status": "success",
                    "message": "Login successful",
                    "role": user.role.name,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "expires_in": int(refresh.access_token.lifetime.total_seconds()),
                }),
                content_type="application/json",
                status=status.HTTP_200_OK
            )


        except LoginUser.DoesNotExist:
            logger.warning("Login failed: Not Found",)

            return HttpResponse(
                    json.dumps({
                        "status": "fail",
                        "message": "User not found"
                    }),
                    content_type="application/json",
                    status=status.HTTP_404_NOT_FOUND
                )

        except json.JSONDecodeError:
           
            return HttpResponse( json.dumps({
                        "status": "fail",
                        "message": "Invalid JSON format"
                    }),
                    content_type="application/json",
                    status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return HttpResponse( json.dumps({
                        "status": "Error",
                        "message":f"Server error: {str(e)}"
                    }),
                    content_type="application/json",
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        return HttpResponse("POST method required", status=405)



@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(View):

    def post(self, request):
        return HttpResponse(
            json.dumps({
                "status": "success",
                "message": "Logout successful"
            }),
            content_type="application/json",
            status=status.HTTP_200_OK
        )

    def get(self, request):
        return HttpResponse("POST method required", status=405)

@method_decorator(csrf_exempt, name="dispatch")
class ForgotPasswordView(View):

    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email")

            user = LoginUser.objects.get(email=email, is_active=True)

            token = str(uuid.uuid4())
            user.reset_token = token
            user.reset_token_expiry = timezone.now() + timedelta(minutes=15)
            user.save()

            reset_link = f"http://localhost:5173/reset-password/{token}"

            send_mail(
                "Reset Your Password",
                f"Click the link to reset your password:\n{reset_link}",
                None,
                [email],
                fail_silently=False,
            )

            return HttpResponse(
                json.dumps({
                    "status": "success",
                    "message": "Reset link sent to email"
                }),
                content_type="application/json",
                status=200
            )

        except LoginUser.DoesNotExist:
            return HttpResponse(
                json.dumps({
                    "status": "fail",
                    "message": "Email not registered"
                }),
                content_type="application/json",
                status=404
            )

@method_decorator(csrf_exempt, name="dispatch")
class ResetPasswordView(View):

    def post(self, request, token):
        try:
            data = json.loads(request.body)
            new_password = data.get("password")

            user = LoginUser.objects.get(
                reset_token=token,
                reset_token_expiry__gte=timezone.now()
            )
            if user.reset_token_expiry and user.reset_token_expiry < timezone.now():
                return HttpResponse(
                    json.dumps({"message": "Reset link expired"}),
                    content_type="application/json",
                    status=400
                )
            user.set_password(new_password)
            user.reset_token = None
            user.reset_token_expiry = None
            user.save()

            return HttpResponse(
                json.dumps({
                    "status": "success",
                    "message": "Password reset successful"
                }),
                content_type="application/json",
                status=200
            )

        except LoginUser.DoesNotExist:
            return HttpResponse(
                json.dumps({
                    "status": "fail",
                    "message": "Invalid or expired token"
                }),
                content_type="application/json",
                status=400
            )


class UserView(GenericAPIView):
    def get(self, request):
        # status_filter = request.GET.get("status")

        users = LoginUser.objects.filter(is_active=True)


        if not users:
            return HttpResponse(
                json.dumps({
                    "status": "success",
                    "message": "No User found",
                    "count": 0,
                    "data": []
                }),
                content_type="application/json",
                status=status.HTTP_200_OK
            )

        data = [
            {
              "email":user.email  
            }
            for user in users
        ]

        return HttpResponse(
                json.dumps({
            "status": "success",
            "message": "Users retrieved successfully",
            "data": data
        }))
 

    