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
        except ImportError:
            # 如果导入失败，记录日志（在生产环境中应该使用日志而不是print）
            print("警告: 未能导入correction_system.signals模块")
