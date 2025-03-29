"""
Django信号处理模块
用于处理模型的信号（如创建、更新、删除等事件）
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Problem, Homework, KnowledgeCard, UserProfile

# 这里可以添加信号处理逻辑
# 例如，当创建新问题时，自动生成知识卡片等

# @receiver(post_save, sender=Problem)
# def problem_created_handler(sender, instance, created, **kwargs):
#     """处理题目创建后的操作"""
#     if created:
#         # 在这里添加题目创建后的处理逻辑
#         pass

# @receiver(post_save, sender=Homework)
# def homework_created_handler(sender, instance, created, **kwargs):
#     """处理作业创建后的操作"""
#     if created:
#         # 在这里添加作业创建后的处理逻辑
#         pass

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """当用户被创建时，自动创建对应的资料"""
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """当用户被保存时，自动保存对应的资料"""
    try:
        instance.profile.save()
    except User.profile.RelatedObjectDoesNotExist:
        UserProfile.objects.create(user=instance) 