from django.db import models
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class Meal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, blank=True)
    calories = models.IntegerField()
    proteins = models.IntegerField()
    carbohydrates = models.IntegerField()
    fats = models.IntegerField()
    weight = models.IntegerField(blank=True)
    log_date = models.DateTimeField("logging time", default = datetime.now())

    def __str__(self):
            return self.name
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    def get_goal_for_date(self, target_date):
        """Get the calorie goal that was active on a specific date"""
        try:
            # Get the most recent goal that was set on or before target_date
            goal = CalorieGoal.objects.filter(
                user=self.user,
                effective_date__lte=target_date
            ).order_by('-effective_date').first()
            
            if goal:
                return goal.goal
        except:
            pass
        
        # Fallback to default 2000 if no goal found
        return 2000

    def __str__(self):
        return f"{self.user.username}'s profile"
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

class CalorieGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    goal = models.IntegerField()
    effective_date = models.DateField()
    
    class Meta:
        ordering = ['-effective_date']
        unique_together = ['user', 'effective_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.goal} cal from {self.effective_date}"