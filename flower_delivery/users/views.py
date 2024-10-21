# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm
from django.contrib import messages
from orders.models import Order
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'users/order_detail.html', {'order': order})

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user, status='pending')
    order.status = 'canceled'
    order.save()
    messages.success(request, f'Заказ №{order.id} был успешно отменен.')
    return HttpResponseRedirect(reverse('profile'))


@login_required
def profile(request):
    # Получаем все заказы пользователя, отсортированные по дате создания
    orders = request.user.orders.all().order_by('-created_at')

    # Разделяем заказы по статусам
    pending_orders = orders.filter(status='pending')
    accepted_orders = orders.filter(status='accepted')
    in_progress_orders = orders.filter(status='in_progress')
    in_delivery_orders = orders.filter(status='in_delivery')
    completed_orders = orders.filter(status='completed')
    canceled_orders = orders.filter(status='canceled')

    context = {
        'pending_orders': pending_orders,
        'accepted_orders': accepted_orders,
        'in_progress_orders': in_progress_orders,
        'in_delivery_orders': in_delivery_orders,
        'completed_orders': completed_orders,
        'canceled_orders': canceled_orders,
    }

    return render(request, 'users/profile.html', context)


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт создан для {username}!')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})
