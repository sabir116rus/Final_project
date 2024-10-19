# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm
from django.contrib import messages

# Представление для профиля пользователя
@login_required
def profile(request):
    return render(request, 'users/profile.html')

# Представление для регистрации пользователей
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт создан для {username}!')
            return redirect('login')
    # Перенаправляем на страницу входа после успешной регистрации
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})