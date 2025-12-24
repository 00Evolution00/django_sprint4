from django.db.models import Count
from django.core.paginator import Paginator

def annotate_comment_count(queryset):
    """Добавляет comment_count и сортирует по дате публикации."""
    return queryset.annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')

def paginate(request, queryset, per_page=10):
    """Вычисляет страницу пагинатора."""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)