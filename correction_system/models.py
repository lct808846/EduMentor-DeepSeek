from django.db import models
from django.utils import timezone

class Problem(models.Model):
    """题目模型"""
    PROBLEM_TYPE_CHOICES = [
        ('TEXT', '文字题目'),
        ('IMAGE', '图片题目'),
    ]
    
    problem_type = models.CharField(max_length=5, choices=PROBLEM_TYPE_CHOICES, default='TEXT', verbose_name='题目类型')
    text_content = models.TextField(blank=True, null=True, verbose_name='文字内容')
    image = models.ImageField(upload_to='problems/', blank=True, null=True, verbose_name='题目图片')
    solution = models.TextField(blank=True, null=True, verbose_name='解答')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    def __str__(self):
        return f"题目 {self.id} - {self.get_problem_type_display()}"
    
    class Meta:
        verbose_name = '题目'
        verbose_name_plural = '题目'

class Homework(models.Model):
    """作业模型"""
    CORRECTION_STATUS_CHOICES = [
        ('PENDING', '待批改'),
        ('COMPLETED', '已批改'),
    ]
    
    image = models.ImageField(upload_to='homeworks/', verbose_name='作业图片')
    correction_status = models.CharField(max_length=10, choices=CORRECTION_STATUS_CHOICES, default='PENDING', verbose_name='批改状态')
    correction_result = models.TextField(blank=True, null=True, verbose_name='批改结果')
    score = models.FloatField(blank=True, null=True, verbose_name='分数')
    feedback = models.TextField(blank=True, null=True, verbose_name='反馈')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    def __str__(self):
        return f"作业 {self.id} - {self.get_correction_status_display()}"
    
    class Meta:
        verbose_name = '作业'
        verbose_name_plural = '作业'
