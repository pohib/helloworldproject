from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm, UserEditForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from .models import Profile, TelegramUser
import hashlib
import hmac
from datetime import datetime
from django.conf import settings
import logging
import requests
from django.core.files.base import ContentFile
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@login_required
def profile(request):
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)
    return render(request, 'users/profile/profile.html')

@login_required
def profile_edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            
            if 'avatar-clear' in request.POST:
                request.user.profile.avatar.delete(save=False)
            profile_form.save()
            
            return redirect('users:profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'users/profile/profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


def telegram_login(request):
    if not request.GET.get('hash'):
        logger.error("Вход через Telegram: в запросе отсутствует хэш")
        return redirect('account_login')
    
    auth_data = request.GET.dict()
    logger.info(f"Данные для авторизации в Telegram: {auth_data}")

    if not validate_telegram_data(auth_data):
        logger.error("Вход через Telegram: Ошибка валидации")
        return redirect('account_login')

    telegram_id = auth_data['id']
    auth_date_timestamp = int(auth_data.get('auth_date'))
    auth_date_dt = datetime.fromtimestamp(auth_date_timestamp)

    try:
        telegram_user = TelegramUser.objects.filter(telegram_id=telegram_id).first()

        if telegram_user:
            user = telegram_user.user
            logger.info(f"Существующий пользователь вошёл через Telegram: {user.username}")
        else:
            username = generate_unique_username(auth_data)

            user = User.objects.create_user(
                username=username,
                first_name=auth_data.get('first_name', ''),
                last_name=auth_data.get('last_name', '')
            )

            telegram_user = TelegramUser.objects.create(
                user=user,
                telegram_id=telegram_id,
                username=auth_data.get('username'),
                first_name=auth_data.get('first_name'),
                last_name=auth_data.get('last_name'),
                photo_url=auth_data.get('photo_url'),
                auth_date=auth_date_dt
            )
            
            if auth_data.get('photo_url'):
                try:
                    response = requests.get(auth_data['photo_url'])
                    if response.status_code == 200:
                        file_name = urlparse(auth_data['photo_url']).path.split('/')[-1]
                        user.profile.avatar.save(file_name, ContentFile(response.content), save=True)
                except Exception as e:
                    logger.error(f"Ошибка при загрузке аватара Telegram: {e}")
                    
            logger.info(f"Новый пользователь создан: {username} (ID: {telegram_id})")

        user = authenticate(request, telegram_id=telegram_id)
        if user is not None:
            login(request, user)
            return redirect('users:profile')
        else:
            logger.error("Пользователь Telegram не найден для аутентификации")
            return redirect('account_login')

    except Exception as e:
        logger.error(f"Ошибка входа через Telegram: {str(e)}", exc_info=True)
        return redirect('account_login')


def validate_telegram_data(auth_data):
    try:
        required_fields = ['id', 'first_name', 'auth_date', 'hash']
        for field in required_fields:
            if field not in auth_data:
                logger.error(f"Отсутствует обязательное поле: {field}")
                return False

        bot_token = settings.TELEGRAM_BOT_TOKEN
        data_check_string = '\n'.join(
            f"{key}={auth_data[key]}" 
            for key in sorted(auth_data.keys()) 
            if key != 'hash'
        )

        secret_key = hashlib.sha256(bot_token.encode()).digest()
        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        return auth_data['hash'] == computed_hash

    except Exception as e:
        logger.error(f"Ошибка валидации: {str(e)}", exc_info=True)
        return False


def generate_unique_username(auth_data):
    base_username = auth_data.get('username', f"tg_{auth_data['id']}")
    username = base_username
    counter = 1

    while User.objects.filter(username=username).exists():
        username = f"{base_username}_{counter}"
        counter += 1

    return username
