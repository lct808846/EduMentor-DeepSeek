from django.apps import AppConfig


class CorrectionSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'correction_system'

    def ready(self):
        """
        应用启动时的初始化配置
        确保自定义模板标签和过滤器被加载
        """
        import correction_system.signals
        
        # 只有在非迁移环境下才尝试访问数据库
        # 避免在数据库未就绪时执行查询
        from django.db import connection
        from django.conf import settings
        
        # 检查是否在运行迁移命令
        import sys
        if 'makemigrations' in sys.argv or 'migrate' in sys.argv:
            return
        
        # 检查auth_user表是否存在
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='auth_user';")
                table_exists = cursor.fetchone()
                
            if not table_exists:
                # 表不存在，跳过后续操作
                return
                
            # 只有当表存在时才执行用户查询
            from django.contrib.auth.models import User
            from correction_system.models import UserProfile
            
            # 查找没有用户资料的用户
            users_without_profile = User.objects.filter(profile__isnull=True)
            for user in users_without_profile:
                UserProfile.objects.create(user=user)
        except Exception as e:
            # 捕获所有可能的数据库异常，确保应用能够启动
            if settings.DEBUG:
                print(f"数据库初始化检查出错: {e}")
