from django.apps import AppConfig


class CorrectionSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'correction_system'

    def ready(self):
        """
        应用启动时的初始化配置
        确保自定义模板标签和过滤器被加载
        """
        try:
            # 导入信号处理器
            import correction_system.signals
            
            # 确保所有用户都有资料
            from django.contrib.auth.models import User
            from django.db.models import F
            from correction_system.models import UserProfile
            
            # 获取没有资料的用户列表
            users_without_profile = User.objects.exclude(
                id__in=UserProfile.objects.values_list('user_id', flat=True)
            )
            
            # 为这些用户创建资料
            for user in users_without_profile:
                UserProfile.objects.create(user=user)
        except ImportError:
            # 如果导入失败，记录日志（在生产环境中应该使用日志而不是print）
            print("警告: 未能导入correction_system.signals模块")
