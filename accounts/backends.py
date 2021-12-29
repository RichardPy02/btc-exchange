from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from .models import Trader


# backend model to customize authentication

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        Trader = get_user_model()
        try:
            user = Trader.objects.get(email=username)
        except Trader.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
        return None

    def get_user(self, user_id):
        try:
            return Trader.objects.get(pk=user_id)
        except Trader.DoesNotExist:
            return None
