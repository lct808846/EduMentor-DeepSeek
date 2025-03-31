from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

@require_POST
@csrf_protect
def mark_messages_read(request):
    """
    标记所有消息为已读
    清理Django消息框架中的所有消息
    """
    # 清理存储在消息框架中的所有消息
    storage = messages.get_messages(request)
    # 遍历所有消息以确保它们被标记为已读
    for message in storage:
        pass  # 仅仅遍历就会将消息标记为已读
    
    # 确保存储被清理
    storage.used = True
    
    return JsonResponse({"status": "success"})

# 导入Django消息框架
from django.contrib import messages

def add_message_once(request, level, message, extra_tags=''):
    """
    添加消息前检查是否已经存在相同消息
    防止相同消息重复显示
    
    参数:
        request: HttpRequest对象
        level: 消息级别 (如 messages.INFO, messages.SUCCESS 等)
        message: 消息内容
        extra_tags: 额外的CSS类名
    """
    # 获取当前会话中的所有消息
    storage = messages.get_messages(request)
    # 转换为列表以便可以重用
    message_list = list(storage)
    
    # 检查是否已存在相同消息
    for existing_message in message_list:
        if str(existing_message) == message:
            # 将消息放回存储
            for m in message_list:
                storage.add(m)
            return False
    
    # 将消息放回存储
    for m in message_list:
        storage.add(m)
        
    # 添加新消息
    messages.add_message(request, level, message, extra_tags=extra_tags)
    return True 