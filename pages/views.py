from django.shortcuts import render
from django.views.generic import TemplateView


class AboutView(TemplateView):
    """Страница 'О проекте'."""

    template_name = 'pages/about.html'


class RulesView(TemplateView):
    """Страница 'Правила'."""

    template_name = 'pages/rules.html'


def page_not_found(request, exception):
    """Обработчик ошибки 404."""
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    """Обработчик ошибки 500."""
    return render(request, 'pages/500.html', status=500)


def permission_denied_view(request, exception):
    """Обработчик ошибки 403."""
    return render(request, 'pages/403csrf.html', status=403)
