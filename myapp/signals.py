import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Task

# Простой логгер без Unicode проблем
logger = logging.getLogger('myapp')


@receiver(pre_save, sender=Task)
def capture_task_status_change(sender, instance, **kwargs):
    """Capture status change before saving"""
    if instance.pk:
        try:
            old_instance = Task.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Task.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Task)
def send_status_change_notification(sender, instance, created, **kwargs):
    """Send notification when task status changes"""

    # Skip for new tasks
    if created:
        print(f"[INFO] Task '{instance.title}' created, skipping notification")
        return

    # Check owner and email
    if not instance.owner or not instance.owner.email:
        print(f"[WARNING] Task '{instance.title}' has no owner or email")
        return

    # Get status change
    old_status = getattr(instance, '_old_status', None)
    new_status = instance.status

    # Check if status changed
    if old_status == new_status:
        return

    # Determine notification type
    if new_status == 'done':
        notification_type = 'task_completed'
        emoji = '✅'
    elif old_status == 'done' and new_status != 'done':
        notification_type = 'status_reverted'
        emoji = '🔄'
    else:
        notification_type = 'status_change'
        emoji = '📝'

    try:
        # Send email notification
        subject = f'{emoji} Task Status Change: {instance.title}'

        # Simple text message for console
        message = f"""
=== EMAIL NOTIFICATION ===
To: {instance.owner.email} ({instance.owner.username})
Subject: {subject}

Hello {instance.owner.first_name or instance.owner.username}!

Your task status has been updated:

Task: {instance.title}
Description: {instance.description[:100]}{'...' if len(instance.description) > 100 else ''}

Status Change: {old_status or 'new'} -> {new_status}
Deadline: {instance.deadline.strftime('%Y-%m-%d %H:%M')}
Updated: {instance.updated_at.strftime('%Y-%m-%d %H:%M')}

Type: {notification_type}

---
This is an automated notification from your task management system.
========================
"""

        # Send email (will print to console)
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@todoapi.local'),
            recipient_list=[instance.owner.email],
            fail_silently=False,
        )

        print(f"[SUCCESS] Email notification sent for task: {instance.title}")

    except Exception as e:
        print(f"[ERROR] Failed to send notification: {e}")