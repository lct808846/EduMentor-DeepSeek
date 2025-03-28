from django.urls import path
from . import views
from django.conf import settings

urlpatterns = [
    # 用户认证相关URL
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    
    # 首页和仪表盘
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.home, name='home'),
    
    # 学习历史相关URL
    path('history/', views.learning_history, name='learning_history'),
    path('history/problems/', views.problem_history, name='problem_history'),
    path('history/homeworks/', views.homework_history, name='homework_history'),
    path('history/problem/<int:problem_id>/', views.view_problem, name='view_problem'),
    path('history/homework/<int:homework_id>/', views.view_homework, name='view_homework'),
    
    # 知识卡片相关URL
    path('cards/', views.knowledge_cards, name='knowledge_cards'),
    path('cards/view/<int:card_id>/', views.view_knowledge_card, name='view_knowledge_card'),
    path('cards/create/', views.create_knowledge_card, name='create_knowledge_card'),
    path('cards/edit/<int:card_id>/', views.edit_knowledge_card, name='edit_knowledge_card'),
    path('cards/delete/<int:card_id>/', views.delete_knowledge_card, name='delete_knowledge_card'),
    
    # 学习资源相关URL
    path('resources/', views.learning_resources, name='learning_resources'),
    path('resources/view/<int:resource_id>/', views.view_resource, name='view_resource'),
    path('resources/recommend/', views.recommend_resources, name='recommend_resources'),
    path('resources/save/<int:resource_id>/', views.save_resource, name='save_resource'),
    path('resources/unsave/<int:resource_id>/', views.unsave_resource, name='unsave_resource'),
    path('resources/rate/<int:resource_id>/', views.rate_resource, name='rate_resource'),
    
    # 用户资料相关URL
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # 题目和作业处理
    path('solve/', views.solve_problem, name='solve_problem'),
    path('correct/', views.correct_homework, name='correct_homework'),
]

# 添加调试路径
if settings.DEBUG:
    urlpatterns += [
        path('reload-static/', views.reload_static, name='reload_static'),
    ]

urlpatterns = tuple(urlpatterns) 