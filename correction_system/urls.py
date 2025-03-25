from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('solve/', views.solve_problem, name='solve_problem'),
    path('correct/', views.correct_homework, name='correct_homework'),
    path('api/solve/', views.api_solve_problem, name='api_solve_problem'),
    path('api/correct/', views.api_correct_homework, name='api_correct_homework'),
] 