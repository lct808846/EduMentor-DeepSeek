# 这个文件使views成为一个Python包
# 您可以在这里导入和暴露特定的视图函数 

# 从主视图文件导入所有视图函数
from correction_system.views.analytics import learning_analytics

# 从主视图模块导入所有函数
try:
    from correction_system.main_views import *
except ImportError:
    # 如果不存在main_views.py，尝试从views.py导入
    try:
        from correction_system.views import (
            user_login, user_register, user_logout,
            dashboard, home,
            learning_history, problem_history, homework_history,
            view_problem, view_homework,
            knowledge_cards, view_knowledge_card, create_knowledge_card,
            edit_knowledge_card, delete_knowledge_card,
            learning_resources, view_resource, recommend_resources,
            save_resource, unsave_resource, rate_resource,
            profile, edit_profile,
            solve_problem, correct_homework,
            reload_static
        )
    except ImportError:
        # 如果导入失败，尝试直接导入整个views模块
        from .. import views as main_views
        # 导出所有函数
        globals().update(vars(main_views)) 