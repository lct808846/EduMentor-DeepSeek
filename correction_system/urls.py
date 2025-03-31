from django.urls import path
from .views import *  # 这里确保导入所有视图
from django.conf import settings
from .views.analytics import learning_analytics
from correction_system.views.utils import mark_messages_read

urlpatterns = [
    # 认证相关URL
    path('login/', user_login, name='login'),
    path('register/', user_register, name='register'),
    path('logout/', user_logout, name='logout'),

    # 主要页面
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),

    # 学习历史
    path('history/', learning_history, name='learning_history'),
    path('history/problems/', problem_history, name='problem_history'),
    path('history/homework/', homework_history, name='homework_history'),
    path('problem/<int:problem_id>/', view_problem, name='view_problem'),
    path('homework/<int:homework_id>/', view_homework, name='view_homework'),

    # 知识卡片
    path('cards/', knowledge_cards, name='knowledge_cards'),
    path('cards/view/<int:card_id>/', view_knowledge_card, name='view_knowledge_card'),
    path('cards/create/', create_knowledge_card, name='create_knowledge_card'),
    path('cards/edit/<int:card_id>/', edit_knowledge_card, name='edit_knowledge_card'),
    path('cards/delete/<int:card_id>/', delete_knowledge_card, name='delete_knowledge_card'),

    # 学习资源相关URL
    path('resources/', learning_resources, name='learning_resources'),
    path('resources/<int:resource_id>/', view_resource, name='view_resource'),
    path('resources/<int:resource_id>/save/', save_resource, name='save_resource'),
    path('resources/<int:resource_id>/unsave/', unsave_resource, name='unsave_resource'),
    path('resources/<int:resource_id>/rate/', rate_resource, name='rate_resource'),
    path('resources/recommended/', recommend_resources, name='recommend_resources'),
    path('resources/create/', create_resource, name='create_resource'),
    path('resources/<int:resource_id>/edit/', edit_resource, name='edit_resource'),
    path('resources/<int:resource_id>/delete/', delete_resource, name='delete_resource'),

    # 用户个人资料
    path('profile/', profile, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),

    # 功能页面
    path('solve/', solve_problem, name='solve_problem'),
    path('correct/', correct_homework, name='correct_homework'),
    
    # 分析页面
    path('analytics/learning/', learning_analytics, name='learning_analytics'),

    # 工具类URL
    path('utils/mark-messages-read/', mark_messages_read, name='mark_messages_read'),
]

# 在DEBUG模式下添加静态文件重新加载路径
if settings.DEBUG:
    urlpatterns.append(path('reload-static/', reload_static, name='reload_static')) 