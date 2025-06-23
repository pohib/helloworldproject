from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from users.models import TelegramUser

class TelegramBackend(BaseBackend):
    def authenticate(self, request, telegram_id=None):
        if telegram_id is None:
            return None
        try:
            telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
            return telegram_user.user
        except TelegramUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
