from .models import Notification

def notifications(request):
    """
    Adds the latest 5 notifications to the context of every template.
    """
    notifications = Notification.objects.order_by('-created_at')[:5]
    return {'notifications': notifications}