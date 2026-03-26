from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from datetime import date, datetime
from .models import Meal, UserProfile, CalorieGoal
from django.views.decorators.http import require_http_methods

from.models import Meal

# Create your views here.

@login_required
def dashboard(request):
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get selected date from query parameter (default to today)
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    else:
        selected_date = timezone.now().date()
    
    # Get meals for selected date
    selected_date_meals = Meal.objects.filter(
        user=request.user,
        log_date__date=selected_date
    )
    
    # Calculate totals for selected date
    totals = selected_date_meals.aggregate(
        total_calories=Sum('calories'),
        total_proteins=Sum('proteins'),
        total_carbohydrates=Sum('carbohydrates'),
        total_fats=Sum('fats')
    )
    
    total_calories = totals['total_calories'] or 0
    total_proteins = totals['total_proteins'] or 0
    total_carbohydrates = totals['total_carbohydrates'] or 0
    total_fats = totals['total_fats'] or 0
    
    # Get the goal that was active on the selected date
    calorie_goal = profile.get_goal_for_date(selected_date)
    
    # Calculate remaining calories
    remaining = calorie_goal - total_calories
    
    # Get all meals for the main list
    all_meals = Meal.objects.filter(user=request.user).order_by('-log_date')
    
    # Get distinct dates for day selection
    dates = Meal.objects.filter(user=request.user).values_list('log_date__date', flat=True).distinct().order_by('-log_date__date')
    
    # Get current goal (for display in the modal)
    current_goal = profile.get_goal_for_date(timezone.now().date())
    
    context = {
        'meals': all_meals,
        'selected_date': selected_date,
        'selected_date_meals': selected_date_meals,
        'total_calories': total_calories,
        'total_proteins': total_proteins,
        'total_carbohydrates': total_carbohydrates,
        'total_fats': total_fats,
        'calorie_goal': calorie_goal,
        'current_goal': current_goal,
        'remaining': remaining,
        'dates': dates,
        'today': timezone.now().date(),
    }
    return render(request, 'dashboard.html', context)

@login_required
def create_meal(request):
    if request.method == 'POST':
        # Get the selected date from the form or use today
        selected_date = request.POST.get('log_date')
        if selected_date:
            log_date = datetime.strptime(selected_date, '%Y-%m-%d')
        else:
            log_date = timezone.now()
        
        # Handle weight
        weight_value = request.POST.get('weight')
        if weight_value == '' or weight_value is None:
            weight_value = 0
        else:
            weight_value = int(weight_value)
        
        # Create new meal for the logged-in user
        meal = Meal(
            name=request.POST.get('name'),
            calories=int(request.POST.get('calories')),
            proteins=int(request.POST.get('proteins')),
            carbohydrates=int(request.POST.get('carbohydrates')),
            fats=int(request.POST.get('fats')),
            weight=weight_value,
            user=request.user,
            log_date=log_date
        )
        meal.save()
        
        # Redirect back to the dashboard with the same date
        return redirect(f'/calories/?date={log_date.date()}')
    
    return redirect('dashboard')

def index(request):
    latest_meal_list = Meal.objects.order_by("-log_date")[:5]
    context = {"latest_meal_list": latest_meal_list}
    return render(request, "meal/index.html", context)

@login_required
def detail(request, meal_id):
    # Get the meal, ensuring it belongs to the logged-in user
    meal = get_object_or_404(Meal, id=meal_id, user=request.user)
    
    if request.method == 'POST':
        # Check which button was clicked
        if 'update' in request.POST:
            # Update the meal
            meal.name = request.POST.get('name')
            meal.calories = int(request.POST.get('calories'))
            meal.proteins = int(request.POST.get('proteins'))
            meal.carbohydrates = int(request.POST.get('carbohydrates'))
            meal.fats = int(request.POST.get('fats'))
            
            # Handle weight
            weight_value = request.POST.get('weight')
            if weight_value == '' or weight_value is None:
                weight_value = 0
            else:
                weight_value = int(weight_value)
            meal.weight = weight_value
            
            meal.save()
            return redirect('dashboard')
            
        elif 'delete' in request.POST:
            # Delete the meal
            meal.delete()
            return redirect('dashboard')
    
    # GET request - show the form with current meal data
    context = {
        'meal': meal,
    }
    return render(request, 'detail.html', context)

@login_required
@require_http_methods(["POST"])
def update_calorie_goal(request):
    new_goal = request.POST.get('calorie_goal')
    if new_goal:
        try:
            new_goal = int(new_goal)
            if new_goal > 0:
                today = timezone.now().date()
                
                # Update existing goal for today, or create if it doesn't exist
                CalorieGoal.objects.update_or_create(
                    user=request.user,
                    effective_date=today,
                    defaults={'goal': new_goal}
                )
        except ValueError:
            pass
    
    # Get the next URL from the form, or default to dashboard
    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    else:
        return redirect('dashboard')