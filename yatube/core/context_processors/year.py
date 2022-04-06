from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом."""
    dt = timezone.now().year
    return {
        'year': dt
    }
