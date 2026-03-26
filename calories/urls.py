from django.urls import path

from . import views

urlpatterns = [
    # Dashboard view
    path("", views.dashboard, name="dashboard"),

    # ex: /calories/meal
    path("meal/", views.index, name="index"),
    # ex: /calories/meal/5/
    path("meal/<int:meal_id>/", views.detail, name="detail"),

    path("meal/create/", views.create_meal, name="create_meal"),

    path("update-goal/", views.update_calorie_goal, name="update_goal"),
]