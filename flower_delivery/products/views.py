# products/views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Review
from .forms import ReviewForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg

def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/product_list.html', {'products': products})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.filter(is_active=True)
    user_review = None
    if request.user.is_authenticated:
        user_review = product.reviews.filter(user=request.user).first()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Вы должны войти, чтобы оставить отзыв.')
            return redirect('login')
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            # review.is_active = False  # Раскомментируйте, если хотите модерацию отзывов
            review.save()
            messages.success(request, 'Ваш отзыв был добавлен!')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ReviewForm()
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    return render(request, 'products/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'form': form,
        'user_review': user_review,
        'average_rating': average_rating,
        'review_count': reviews.count()
    })
