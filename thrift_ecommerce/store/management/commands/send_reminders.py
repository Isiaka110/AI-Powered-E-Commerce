from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from store.models import Wishlist
from datetime import timedelta

class Command(BaseCommand):
    help = 'Sends reminder emails for items in wishlist for more than 3 days'

    def handle(self, *args, **kwargs):
        # 1. Define the timeframe (e.g., 3 days ago)
        threshold_date = timezone.now() - timedelta(days=3)
        
        # 2. Find wishlist items older than 3 days that haven't had a reminder yet
        pending_reminders = Wishlist.objects.filter(
            added_at__lte=threshold_date,
            reminder_sent=False
        )

        if not pending_reminders.exists():
            self.stdout.write("No reminders to send today.")
            return

        for item in pending_reminders:
            try:
                # 3. Send the Email
                send_mail(
                    subject="Your Thrift Find is Waiting! 💜",
                    message=f"Hi {item.user.username},\n\nWe noticed '{item.product.name}' is still in your wishlist! It's in your size ({item.user.preferred_size}), so it might not last long. Come back and grab it before someone else does!",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[item.user.email],
                    fail_silently=False,
                )
                
                # 4. Mark as sent so they don't get spammed
                item.reminder_sent = True
                item.save()
                
                self.stdout.write(self.style.SUCCESS(f'Sent reminder to {item.user.email}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to send to {item.user.email}: {e}'))