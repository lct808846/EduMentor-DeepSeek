from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Problem(models.Model):
    """题目模型"""
    PROBLEM_TYPE_CHOICES = [
        ('TEXT', '文字题目'),
        ('IMAGE', '图片题目'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='problems', verbose_name='用户')
    problem_type = models.CharField(max_length=5, choices=PROBLEM_TYPE_CHOICES, default='TEXT', verbose_name='题目类型')
    text_content = models.TextField(blank=True, null=True, verbose_name='文字内容')
    image = models.ImageField(upload_to='problems/', blank=True, null=True, verbose_name='题目图片')
    solution = models.TextField(blank=True, null=True, verbose_name='解答')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    is_favorite = models.BooleanField(default=False, verbose_name='收藏')
    view_count = models.IntegerField(default=0, verbose_name='查看次数')
    
    def __str__(self):
        return f"题目 {self.id} - {self.get_problem_type_display()}"
    
    class Meta:
        verbose_name = '题目'
        verbose_name_plural = '题目'
        ordering = ['-created_at']

class Homework(models.Model):
    """作业模型"""
    CORRECTION_STATUS_CHOICES = [
        ('PENDING', '待批改'),
        ('COMPLETED', '已批改'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='homeworks', verbose_name='用户')
    image = models.ImageField(upload_to='homeworks/', verbose_name='作业图片')
    correction_status = models.CharField(max_length=10, choices=CORRECTION_STATUS_CHOICES, default='PENDING', verbose_name='批改状态')
    correction_result = models.TextField(blank=True, null=True, verbose_name='批改结果')
    score = models.FloatField(blank=True, null=True, verbose_name='分数')
    feedback = models.TextField(blank=True, null=True, verbose_name='反馈')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    is_favorite = models.BooleanField(default=False, verbose_name='收藏')
    view_count = models.IntegerField(default=0, verbose_name='查看次数')
    
    def __str__(self):
        return f"作业 {self.id} - {self.get_correction_status_display()}"
    
    class Meta:
        verbose_name = '作业'
        verbose_name_plural = '作业'
        ordering = ['-created_at']

class KnowledgeCard(models.Model):
    """知识卡片模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='knowledge_cards', verbose_name='用户')
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='knowledge_cards', null=True, blank=True, verbose_name='相关问题')
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='knowledge_cards', null=True, blank=True, verbose_name='相关作业')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    last_reviewed = models.DateTimeField(null=True, blank=True, verbose_name='上次复习时间')
    review_count = models.IntegerField(default=0, verbose_name='复习次数')
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = '知识卡片'
        verbose_name_plural = '知识卡片'
        ordering = ['-created_at']

class LearningResource(models.Model):
    """学习资源模型"""
    RESOURCE_TYPES = (
        ('VIDEO', '视频'),
        ('ARTICLE', '文章'),
        ('BOOK', '图书'),
        ('EXERCISE', '练习题'),
        ('TOOL', '工具'),
    )
    
    title = models.CharField(max_length=200, verbose_name="标题")
    description = models.TextField(verbose_name="描述")
    content = models.TextField(verbose_name="内容", blank=True, null=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES, verbose_name="资源类型")
    image = models.ImageField(upload_to='resources/images/', blank=True, null=True, verbose_name="封面图片")
    file_url = models.URLField(blank=True, null=True, verbose_name="文件链接")
    video_url = models.URLField(blank=True, null=True, verbose_name="视频链接")
    external_url = models.URLField(blank=True, null=True, verbose_name="外部链接")
    tags = models.CharField(max_length=200, blank=True, null=True, verbose_name="标签")
    difficulty_level = models.IntegerField(default=1, choices=[(1, '初级'), (2, '中级'), (3, '高级')], verbose_name="难度级别")
    view_count = models.IntegerField(default=0, verbose_name="查看次数")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    saved_by = models.ManyToManyField(User, related_name='saved_resources', blank=True, verbose_name="收藏用户")
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "学习资源"
        verbose_name_plural = "学习资源"
        ordering = ['-created_at']

class ResourceRecommendation(models.Model):
    """资源推荐模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_recommendations', verbose_name='用户')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='resource_recommendations', null=True, blank=True, verbose_name='相关问题')
    resource = models.ForeignKey(LearningResource, on_delete=models.CASCADE, related_name='recommendations', verbose_name='学习资源')
    relevance_score = models.FloatField(default=0.0, verbose_name='相关性分数')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    def __str__(self):
        return f"{self.resource.title} 推荐给 {self.user.username}"
    
    class Meta:
        verbose_name = '资源推荐'
        verbose_name_plural = '资源推荐'
        ordering = ['-relevance_score']

class UserProfile(models.Model):
    """用户资料模型"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='用户')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')
    bio = models.TextField(blank=True, null=True, verbose_name='个人简介')
    school = models.CharField(max_length=100, blank=True, null=True, verbose_name='学校')
    grade = models.CharField(max_length=50, blank=True, null=True, verbose_name='年级')
    subjects_of_interest = models.CharField(max_length=200, blank=True, null=True, verbose_name='感兴趣的科目')
    
    def __str__(self):
        return f"{self.user.username}的个人资料"
    
    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'

class ResourceReview(models.Model):
    """资源评价模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_reviews', verbose_name='用户')
    resource = models.ForeignKey(LearningResource, on_delete=models.CASCADE, related_name='reviews', verbose_name='学习资源')
    rating = models.IntegerField(verbose_name='评分')
    comment = models.TextField(blank=True, null=True, verbose_name='评价内容')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '资源评价'
        verbose_name_plural = '资源评价'
        unique_together = ('user', 'resource')
    
    def __str__(self):
        return f"{self.user.username} 对 {self.resource.title} 的评价"

class ResourceRating(models.Model):
    """资源评价模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_ratings', verbose_name="用户")
    resource = models.ForeignKey(LearningResource, on_delete=models.CASCADE, related_name='ratings', verbose_name="资源")
    score = models.IntegerField(verbose_name="评分", choices=[(1, '1星'), (2, '2星'), (3, '3星'), (4, '4星'), (5, '5星')])
    comment = models.TextField(verbose_name="评论")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "资源评价"
        verbose_name_plural = "资源评价"
        unique_together = ['user', 'resource']  # 每个用户只能评价一次
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} 评价 {self.resource.title}: {self.score}星"

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
