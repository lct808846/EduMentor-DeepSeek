# 从main_views.py导入所有视图函数到views包的__init__.py中
from django.shortcuts import render, redirect, get_object_or_404
import os
import json
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Q, Avg, Count, Max, F
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Problem, Homework, KnowledgeCard, LearningResource, ResourceRecommendation, UserProfile, ResourceReview, ResourceRating
from .forms import (
    TextProblemForm, ImageProblemForm, HomeworkForm, 
    UserRegisterForm, UserLoginForm, ProfileForm,
    KnowledgeCardForm, LearningResourceForm,
    ResourceSearchForm, ResourceReviewForm,
    ProblemSolveForm, HomeworkCorrectForm
)
from .services import DeepSeekService, KnowledgeExtractor, ResourceRecommender
from django.utils import timezone
from django.views.decorators.http import require_POST

# 创建DeepSeek服务实例
deepseek_service = DeepSeekService()

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'correction_system/home.html')

@login_required
def dashboard(request):
    # 获取用户最近活动
    recent_problems = Problem.objects.filter(user=request.user).order_by('-created_at')[:5]
    recent_homeworks = Homework.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # 获取用户收藏的知识卡片
    favorite_cards = KnowledgeCard.objects.filter(user=request.user, review_count__gt=0).order_by('-last_reviewed')[:5]
    
    # 获取推荐学习资源 - 使用聚合函数计算平均评分
    recommended_resources = LearningResource.objects.annotate(
        avg_rating=Avg('ratings__score'),
        review_count=Count('ratings')
    ).order_by('-avg_rating', '-view_count')[:5]
    
    # 计算统计数据
    problem_count = Problem.objects.filter(user=request.user).count()
    homework_count = Homework.objects.filter(user=request.user).count()
    card_count = KnowledgeCard.objects.filter(user=request.user).count()
    
    # 计算其他有意义的统计
    recent_activity_count = Problem.objects.filter(
        user=request.user, 
        created_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).count() + Homework.objects.filter(
        user=request.user, 
        created_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).count()
    
    # 计算平均作业分数
    avg_score = Homework.objects.filter(user=request.user).aggregate(avg=Avg('score'))['avg'] or 0
    
    context = {
        'recent_problems': recent_problems,
        'recent_homeworks': recent_homeworks,
        'favorite_cards': favorite_cards,
        'recommended_resources': recommended_resources,
        
        # 添加统计数据
        'problem_count': problem_count,
        'homework_count': homework_count,
        'card_count': card_count,
        'recent_activity_count': recent_activity_count,
        'avg_score': round(avg_score, 1),
    }
    
    return render(request, 'correction_system/dashboard.html', context)

@login_required
def solve_problem(request):
    if request.method == 'POST':
        problem_type = request.POST.get('problem_type')
        
        if problem_type == 'TEXT':
            # 处理文本题目
            text_content = request.POST.get('text_content')
            
            # 调用DeepSeek API解答题目
            solution = deepseek_service.solve_text_problem(text_content)
            
            # 保存题目到数据库
            problem = Problem.objects.create(
                user=request.user,
                problem_type='TEXT',
                text_content=text_content,
                solution=solution
            )
            
            # 返回解答结果
            context = {
                'form': {'problem_type': 'TEXT', 'text_content': text_content},
                'solution': solution,
                'problem': problem
            }
            return render(request, 'correction_system/solve_problem.html', context)
            
        elif problem_type == 'IMAGE':
            # 处理图片题目
            if 'image' in request.FILES:
                image = request.FILES['image']
                text_content = request.POST.get('text_content', '')
                
                # 保存题目到数据库（先保存以获取图片路径）
                problem = Problem.objects.create(
                    user=request.user,
                    problem_type='IMAGE',
                    image=image,
                    text_content=text_content
                )
                
                # 获取保存后的图片路径
                image_path = problem.image.path
                
                # 调用DeepSeek API解答题目
                solution = deepseek_service.solve_image_problem(image_path)
                
                # 更新题目解答
                problem.solution = solution
                problem.save()
                
                # 返回解答结果
                context = {
                    'form': {'problem_type': 'IMAGE', 'image': problem.image, 'text_content': text_content},
                    'solution': solution,
                    'problem': problem
                }
                return render(request, 'correction_system/solve_problem.html', context)
    
    # GET请求或表单未提交成功
    context = {
        'form': ProblemSolveForm(),
    }
    return render(request, 'correction_system/solve_problem.html', context)

@login_required
def correct_homework(request):
    if request.method == 'POST':
        form = HomeworkCorrectForm(request.POST, request.FILES)
        if form.is_valid():
            homework = form.save(commit=False)
            homework.user = request.user
            homework.correction_status = 'PENDING'
            homework.save()
            
            # 获取保存后的图片路径
            image_path = os.path.join(settings.MEDIA_ROOT, homework.image.name)
            
            # 调用DeepSeek API批改作业
            correction = deepseek_service.correct_homework(image_path)
            
            # 更新作业批改结果
            homework.correction_status = 'COMPLETED'
            homework.correction_result = correction['correction_result']
            homework.score = correction['score']
            homework.feedback = correction['feedback']
            
            # 如果API返回了优点和缺点，也保存它们
            if 'strengths' in correction:
                homework.strengths = ';'.join(correction['strengths'])
            if 'weaknesses' in correction:
                homework.weaknesses = ';'.join(correction['weaknesses'])
                
            homework.save()
            
            messages.success(request, '作业批改成功！AI已完成评分和反馈。')
            return redirect('view_homework', homework_id=homework.id)
    else:
        form = HomeworkCorrectForm()
    
    context = {
        'form': form,
    }
    return render(request, 'correction_system/correct_homework.html', context)

# 用户认证相关视图
def user_login(request):
    """用户登录视图"""
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            # 使用form.get_user()获取已验证的用户
            user = form.get_user()
            login(request, user)
            messages.success(request, '登录成功！')
            return redirect('home')
    else:
        form = UserLoginForm()
    
    return render(request, 'correction_system/auth/login.html', {'form': form})

def user_register(request):
    """用户注册视图"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 自动登录
            login(request, user)
            messages.success(request, '注册成功！已自动登录。')
            return redirect('home')
    else:
        form = UserRegisterForm()
    
    return render(request, 'correction_system/auth/register.html', {'form': form})

def user_logout(request):
    """用户登出视图"""
    logout(request)
    messages.success(request, '已成功登出！')
    return redirect('home')

@login_required
def profile(request):
    """显示用户个人资料"""
    # 获取最近活动
    recent_problems = Problem.objects.filter(user=request.user).order_by('-created_at')[:3]
    recent_homeworks = Homework.objects.filter(user=request.user).order_by('-created_at')[:3]
    recent_cards = KnowledgeCard.objects.filter(user=request.user).order_by('-created_at')[:3]
    
    # 合并并排序
    recent_activities = []
    for problem in recent_problems:
        recent_activities.append({
            'type': 'problem',
            'time': problem.created_at,
            'description': problem.text_content[:100] if problem.problem_type == 'TEXT' else '图片题目'
        })
    
    for homework in recent_homeworks:
        recent_activities.append({
            'type': 'homework',
            'time': homework.created_at,
            'description': f'得分: {homework.score}/100'
        })
    
    for card in recent_cards:
        recent_activities.append({
            'type': 'knowledge_card',
            'time': card.created_at,
            'description': card.title
        })
    
    # 按时间排序
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    recent_activities = recent_activities[:5]
    
    # 作业统计
    homework_stats = {
        'avg_score': Homework.objects.filter(user=request.user).aggregate(avg=Avg('score'))['avg'] or 0,
        'avg_percentage': min(100, (Homework.objects.filter(user=request.user).aggregate(avg=Avg('score'))['avg'] or 0))
    }
    
    context = {
        'recent_activities': recent_activities,
        'recent_cards': recent_cards,
        'homework_stats': homework_stats
    }
    return render(request, 'correction_system/auth/profile.html', context)

@login_required
def edit_profile(request):
    """编辑用户个人资料"""
    # 获取或创建用户资料
    try:
        profile = request.user.profile
    except Exception as e:
        # 如果用户没有资料，创建一个新的
        from .models import UserProfile
        profile = UserProfile.objects.create(user=request.user)
        messages.info(request, "已为您创建新的个人资料")
    
    if request.method == 'POST':
        # 处理表单提交
        school = request.POST.get('school', '')
        grade = request.POST.get('grade', '')
        subjects = request.POST.get('subjects_of_interest', '')
        bio = request.POST.get('bio', '')
        avatar = request.FILES.get('avatar', None)
        
        profile.school = school
        profile.grade = grade
        profile.subjects_of_interest = subjects
        profile.bio = bio
        
        if avatar:
            profile.avatar = avatar
        
        profile.save()
        messages.success(request, '个人资料已更新')
        return redirect('profile')
    
    # 创建简单的表单结构
    form = {
        'school': {'value': profile.school if hasattr(profile, 'school') else ''},
        'grade': {'value': profile.grade if hasattr(profile, 'grade') else ''},
        'subjects_of_interest': {'value': profile.subjects_of_interest if hasattr(profile, 'subjects_of_interest') else ''},
        'bio': {'value': profile.bio if hasattr(profile, 'bio') else ''},
        'avatar': {'value': profile.avatar if hasattr(profile, 'avatar') else None}
    }
    
    context = {
        'form': form
    }
    return render(request, 'correction_system/auth/edit_profile.html', context)

# 学习历史记录相关视图
@login_required
def learning_history(request):
    """显示用户的学习历史总览页面"""
    # 获取用户的学习数据
    recent_problems = Problem.objects.filter(user=request.user).order_by('-created_at')[:5]
    recent_homeworks = Homework.objects.filter(user=request.user).order_by('-created_at')[:5]
    recent_cards = KnowledgeCard.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # 计算统计数据
    problem_count = Problem.objects.filter(user=request.user).count()
    homework_count = Homework.objects.filter(user=request.user).count()
    card_count = KnowledgeCard.objects.filter(user=request.user).count()
    
    # 计算更多详细统计
    # 题目统计
    text_problem_count = Problem.objects.filter(user=request.user, problem_type='TEXT').count()
    image_problem_count = Problem.objects.filter(user=request.user, problem_type='IMAGE').count()
    
    # 作业统计
    avg_homework_score = Homework.objects.filter(user=request.user).aggregate(Avg('score'))['score__avg'] or 0
    max_homework_score = Homework.objects.filter(user=request.user).aggregate(Max('score'))['score__max'] or 0
    
    # 活动统计
    last_week_problems = Problem.objects.filter(
        user=request.user, 
        created_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).count()
    last_week_homeworks = Homework.objects.filter(
        user=request.user, 
        created_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).count()
    
    # 总学习时长（假设每个问题和作业平均花费5分钟）
    total_study_time = (problem_count + homework_count) * 5
    
    context = {
        'recent_problems': recent_problems,
        'recent_homeworks': recent_homeworks,
        'recent_cards': recent_cards,
        'problem_count': problem_count,
        'homework_count': homework_count,
        'card_count': card_count,
        
        # 新增统计数据
        'text_problem_count': text_problem_count,
        'image_problem_count': image_problem_count,
        'avg_homework_score': round(avg_homework_score, 1),
        'max_homework_score': max_homework_score,
        'last_week_problems': last_week_problems,
        'last_week_homeworks': last_week_homeworks,
        'total_study_time': total_study_time,
        'has_activity': problem_count > 0 or homework_count > 0 or card_count > 0,
    }
    return render(request, 'correction_system/history/learning_history.html', context)

@login_required
def problem_history(request):
    """显示用户的题目历史列表"""
    problem_type = request.GET.get('type', None)
    
    problems = Problem.objects.filter(user=request.user)
    if problem_type:
        problems = problems.filter(problem_type=problem_type)
    
    problems = problems.order_by('-created_at')
    
    # 分页
    paginator = Paginator(problems, 10)  # 每页10条
    page_number = request.GET.get('page', 1)
    problems = paginator.get_page(page_number)
    
    context = {
        'problems': problems,
        'selected_type': problem_type
    }
    return render(request, 'correction_system/history/problem_history.html', context)

@login_required
def homework_history(request):
    """显示用户的作业批改历史列表"""
    score_filter = request.GET.get('score', None)
    
    homeworks = Homework.objects.filter(user=request.user)
    if score_filter:
        if score_filter == 'excellent':
            homeworks = homeworks.filter(score__gte=90)
        elif score_filter == 'good':
            homeworks = homeworks.filter(score__gte=80, score__lt=90)
        elif score_filter == 'average':
            homeworks = homeworks.filter(score__gte=70, score__lt=80)
        elif score_filter == 'pass':
            homeworks = homeworks.filter(score__gte=60, score__lt=70)
        elif score_filter == 'fail':
            homeworks = homeworks.filter(score__lt=60)
    
    homeworks = homeworks.order_by('-created_at')
    
    # 计算统计数据
    total_count = homeworks.count()
    avg_score = homeworks.aggregate(avg=Avg('score'))['avg'] or 0
    highest_score = homeworks.aggregate(max=Avg('score'))['max'] or 0
    
    # 分数分布
    excellent_count = homeworks.filter(score__gte=90).count()
    good_count = homeworks.filter(score__gte=80, score__lt=90).count()
    average_count = homeworks.filter(score__gte=70, score__lt=80).count()
    pass_count = homeworks.filter(score__gte=60, score__lt=70).count()
    fail_count = homeworks.filter(score__lt=60).count()
    
    # 分页
    paginator = Paginator(homeworks, 10)  # 每页10条
    page_number = request.GET.get('page', 1)
    homeworks = paginator.get_page(page_number)
    
    context = {
        'homeworks': homeworks,
        'selected_score': score_filter,
        'total_count': total_count,
        'avg_score': avg_score,
        'highest_score': highest_score,
        'excellent_count': excellent_count,
        'good_count': good_count,
        'average_count': average_count,
        'pass_count': pass_count,
        'fail_count': fail_count,
    }
    return render(request, 'correction_system/history/homework_history.html', context)

@login_required
def view_problem(request, problem_id):
    """
    显示题目详情页面
    """
    try:
        problem = Problem.objects.get(id=problem_id, user=request.user)
    except Problem.DoesNotExist:
        messages.error(request, "题目不存在或您无权查看")
        return redirect('problem_history')
    
    # 检查是否有关联的知识卡片
    related_cards = KnowledgeCard.objects.filter(problem=problem)
    
    # 准备上下文数据
    context = {
        'problem': problem,
        'related_cards': related_cards,
    }
    
    # 渲染详情页面
    return render(request, 'correction_system/problems/view_problem.html', context)

@login_required
def view_homework(request, homework_id):
    """
    显示作业批改详情页面
    """
    try:
        homework = Homework.objects.get(id=homework_id, user=request.user)
    except Homework.DoesNotExist:
        messages.error(request, "作业不存在或您无权查看")
        return redirect('homework_history')
    
    # 准备需要传递给模板的上下文数据
    context = {
        'homework': homework,
        'debug': settings.DEBUG,
    }
    
    return render(request, 'correction_system/homeworks/view_homework.html', context)

# 知识卡片相关视图
@login_required
def knowledge_cards(request):
    """显示用户的知识卡片列表"""
    tag_filter = request.GET.get('tag', None)
    search_query = request.GET.get('q', None)
    
    cards = KnowledgeCard.objects.filter(user=request.user)
    
    if tag_filter:
        # 移除对tags的筛选
        pass
    
    if search_query:
        cards = cards.filter(title__icontains=search_query) | cards.filter(content__icontains=search_query)
    
    cards = cards.order_by('-created_at')
    
    # 获取所有标签
    all_tags = []  # 因为模型没有tags字段，所以不需要收集标签
    
    # 分页
    paginator = Paginator(cards, 12)  # 每页12条
    page_number = request.GET.get('page', 1)
    cards = paginator.get_page(page_number)
    
    context = {
        'cards': cards,
        'all_tags': all_tags,
        'selected_tag': tag_filter,
        'search_query': search_query
    }
    return render(request, 'correction_system/knowledge/knowledge_cards.html', context)

@login_required
def view_knowledge_card(request, card_id):
    """查看单个知识卡片详情"""
    card = get_object_or_404(KnowledgeCard, id=card_id, user=request.user)
    
    # 获取相关资源（不使用tags）
    related_resources = LearningResource.objects.all().order_by('?')[:3]
    
    context = {
        'card': card,
        'related_resources': related_resources
    }
    return render(request, 'correction_system/knowledge/view_card.html', context)

@login_required
def create_knowledge_card(request):
    """创建新的知识卡片"""
    # 从URL获取相关题目ID（如果有）
    problem_id = request.GET.get('problem_id', None)
    problem = None
    generated_card = None
    
    if problem_id:
        problem = get_object_or_404(Problem, id=problem_id, user=request.user)
    
    if request.method == 'POST':
        # 检查是否是生成卡片的请求
        if 'problem_id' in request.POST and not request.POST.get('title'):
            # 这是生成知识卡片的请求，而不是保存卡片
            problem_id = request.POST.get('problem_id')
            problem = get_object_or_404(Problem, id=problem_id, user=request.user)
            
            # 从题目自动生成知识卡片内容
            title, content = generate_knowledge_card_content(problem)
            
            # 创建生成的卡片对象(不保存到数据库)
            generated_card = {
                'title': title,
                'content': content
            }
            
            # 渲染模板，但不保存卡片
            context = {
                'problem': problem,
                'generated_card': generated_card
            }
            return render(request, 'correction_system/knowledge/create_card.html', context)
        
        # 正常保存卡片的请求
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        if not title or not content:
            messages.error(request, '标题和内容不能为空')
            return redirect('create_knowledge_card')
        
        card = KnowledgeCard(
            user=request.user,
            title=title,
            content=content
        )
        
        if problem_id:
            card.problem = problem
        
        card.save()
        messages.success(request, '知识卡片创建成功！')
        return redirect('view_knowledge_card', card_id=card.id)
    
    context = {
        'problem': problem,
        'generated_card': generated_card
    }
    return render(request, 'correction_system/knowledge/create_card.html', context)

def generate_knowledge_card_content(problem):
    """根据题目生成知识卡片内容"""
    # 根据题目类型生成适当的标题
    if problem.problem_type == 'TEXT':
        # 从题目文本中提取前20个字符作为标题基础
        title_base = problem.text_content[:20].strip()
        # 如果标题太短，添加通用后缀
        if len(title_base) < 10:
            title = f"{title_base} - 知识点总结"
        else:
            title = title_base
    else:
        # 图片题目使用通用标题
        title = f"图片题目#{problem.id} - 知识点总结"
    
    # 生成内容
    content = "## 题目描述\n\n"
    
    if problem.problem_type == 'TEXT':
        content += f"{problem.text_content}\n\n"
    else:
        content += "这是一道图片题目，请参考原题图片。\n\n"
    
    content += "## 解题思路\n\n"
    
    # 提取解答中的要点
    if problem.solution:
        # 简单处理解答内容
        solution_lines = problem.solution.split('\n')
        filtered_lines = []
        
        for line in solution_lines:
            line = line.strip()
            if line and not line.startswith('```') and not line.startswith('/*'):
                filtered_lines.append(line)
        
        # 添加解答内容
        content += '\n'.join(filtered_lines) + "\n\n"
    else:
        content += "暂无解题思路。\n\n"
    
    content += "## 相关知识点\n\n"
    content += "- 在这里可以添加与此题相关的知识点\n"
    content += "- 可以包括公式、定理、解题技巧等\n"
    content += "- 记录难点和易错点\n\n"
    
    content += "## 学习笔记\n\n"
    content += "在这里可以添加自己的理解和学习心得...\n"
    
    return title, content

@login_required
def edit_knowledge_card(request, card_id):
    """编辑知识卡片"""
    card = get_object_or_404(KnowledgeCard, id=card_id, user=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        keep_problem_link = request.POST.get('keep_problem_link') == 'on'
        
        if not title or not content:
            messages.error(request, '标题和内容不能为空')
            return redirect('edit_knowledge_card', card_id=card.id)
        
        card.title = title
        card.content = content
        
        if card.problem and not keep_problem_link:
            card.problem = None
        
        card.save()
        messages.success(request, '知识卡片更新成功！')
        return redirect('view_knowledge_card', card_id=card.id)
    
    context = {
        'card': card
    }
    return render(request, 'correction_system/knowledge/edit_card.html', context)

@login_required
def delete_knowledge_card(request, card_id):
    """删除知识卡片"""
    card = get_object_or_404(KnowledgeCard, id=card_id, user=request.user)
    
    if request.method == 'POST':
        card.delete()
        messages.success(request, '知识卡片已删除')
        return redirect('knowledge_cards')
    
    return redirect('view_knowledge_card', card_id=card.id)

# 学习资源相关视图
@login_required
def learning_resources(request):
    """学习资源列表视图"""
    # 获取筛选参数
    keyword = request.GET.get('keyword', '')
    resource_type = request.GET.get('type', '')
    sort = request.GET.get('sort', 'relevance')
    subjects = request.GET.getlist('subject')
    
    # 基础查询
    resources = LearningResource.objects.all()
    
    # 关键词筛选
    if keyword:
        resources = resources.filter(
            Q(title__icontains=keyword) | 
            Q(description__icontains=keyword) | 
            Q(content__icontains=keyword) |
            Q(tags__icontains=keyword)
        )
    
    # 资源类型筛选
    if resource_type:
        resources = resources.filter(resource_type=resource_type)
    
    # 学科筛选
    if subjects:
        q_objects = Q()
        for subject in subjects:
            q_objects |= Q(tags__icontains=subject)
        resources = resources.filter(q_objects)
    
    # 排序
    if sort == 'latest':
        resources = resources.order_by('-created_at')
    elif sort == 'rating':
        resources = resources.annotate(avg_rating=Avg('ratings__score')).order_by('-avg_rating')
    elif sort == 'popular':
        resources = resources.order_by('-view_count')
    else:  # relevance (default)
        if keyword:
            # 使用Case-When根据关键词匹配程度排序
            from django.db.models import Case, When, IntegerField
            resources = resources.annotate(
                relevance=Case(
                    When(title__icontains=keyword, then=10),
                    When(description__icontains=keyword, then=5),
                    When(tags__icontains=keyword, then=3),
                    When(content__icontains=keyword, then=1),
                    default=0,
                    output_field=IntegerField()
                )
            ).order_by('-relevance', '-created_at')
        else:
            resources = resources.order_by('-created_at')
    
    # 统计相关信息
    resources = resources.annotate(
        avg_rating=Avg('ratings__score'),
        review_count=Count('ratings', distinct=True)
    )
    
    # 分页前获取评分和评论数据
    resource_list = list(resources)
    
    # 在每个资源对象上保存评分和评论数量
    for resource in resource_list:
        resource.avg_rating_value = getattr(resource, 'avg_rating', 0) or 0
        resource.review_count_value = getattr(resource, 'review_count', 0) or 0
    
    # 分页
    paginator = Paginator(resource_list, 12)  # 每页显示12个资源
    page = request.GET.get('page')
    
    try:
        paginated_resources = paginator.page(page)
    except PageNotAnInteger:
        paginated_resources = paginator.page(1)
    except EmptyPage:
        paginated_resources = paginator.page(paginator.num_pages)
    
    # 获取用户收藏的资源
    if request.user.is_authenticated:
        saved_resources_query = request.user.saved_resources.all().annotate(
            avg_rating=Avg('ratings__score'),
            review_count=Count('ratings', distinct=True)
        )[:3]  # 只显示前3个收藏
        
        # 为收藏的资源也添加评分属性
        saved_resources = list(saved_resources_query)
        for resource in saved_resources:
            resource.avg_rating_value = getattr(resource, 'avg_rating', 0) or 0
            resource.review_count_value = getattr(resource, 'review_count', 0) or 0
    else:
        saved_resources = []
    
    context = {
        'resources': paginated_resources,
        'saved_resources': saved_resources,
        'selected_types': [resource_type] if resource_type else [],
        'is_paginated': paginated_resources.has_other_pages(),
        'page_obj': paginated_resources,
    }
    
    return render(request, 'correction_system/resources/learning_resources.html', context)

@login_required
def view_resource(request, resource_id):
    """查看单个学习资源"""
    try:
        resource = LearningResource.objects.get(id=resource_id)
    except LearningResource.DoesNotExist:
        messages.error(request, "资源不存在或已被删除")
        return redirect('learning_resources')
    
    # 增加浏览量
    LearningResource.objects.filter(id=resource_id).update(view_count=F('view_count') + 1)
    
    # 获取相关资源（同类型或相同标签）
    similar_resources = LearningResource.objects.filter(
        Q(resource_type=resource.resource_type) | 
        Q(tags__icontains=resource.tags.split(',')[0] if resource.tags else '')
    ).exclude(id=resource_id)[:5]
    
    # 获取个性化推荐
    recommended_resources = get_recommended_resources(request.user)[:5]
    
    context = {
        'resource': resource,
        'similar_resources': similar_resources,
        'recommended_resources': recommended_resources,
    }
    
    return render(request, 'correction_system/resources/view_resource.html', context)

@login_required
def create_resource(request):
    """创建新的学习资源"""
    # 检查权限 - 只有管理员或教师可以创建资源
    if not request.user.is_staff and not getattr(request.user, 'is_teacher', False):
        messages.error(request, "您没有创建学习资源的权限")
        return redirect('learning_resources')
    
    if request.method == 'POST':
        form = LearningResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            # 设置其他字段
            resource.save()
            messages.success(request, f"学习资源《{resource.title}》创建成功")
            return redirect('view_resource', resource_id=resource.id)
    else:
        form = LearningResourceForm()
    
    return render(request, 'correction_system/resources/resource_form.html', {
        'form': form,
        'title': '创建学习资源',
        'submit_text': '创建资源'
    })

@login_required
def edit_resource(request, resource_id):
    """编辑学习资源"""
    try:
        resource = LearningResource.objects.get(id=resource_id)
    except LearningResource.DoesNotExist:
        messages.error(request, "资源不存在或已被删除")
        return redirect('learning_resources')
    
    # 检查权限 - 只有管理员或教师可以编辑资源
    if not request.user.is_staff and not getattr(request.user, 'is_teacher', False):
        messages.error(request, "您没有编辑学习资源的权限")
        return redirect('view_resource', resource_id=resource_id)
    
    if request.method == 'POST':
        form = LearningResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, f"学习资源《{resource.title}》已更新")
            return redirect('view_resource', resource_id=resource_id)
    else:
        form = LearningResourceForm(instance=resource)
    
    return render(request, 'correction_system/resources/resource_form.html', {
        'form': form,
        'resource': resource,
        'title': f'编辑资源: {resource.title}',
        'submit_text': '保存修改'
    })

@login_required
@require_POST
def delete_resource(request, resource_id):
    """删除学习资源"""
    try:
        resource = LearningResource.objects.get(id=resource_id)
    except LearningResource.DoesNotExist:
        messages.error(request, "资源不存在或已被删除")
        return redirect('learning_resources')
    
    # 检查权限 - 只有管理员可以删除资源
    if not request.user.is_staff:
        messages.error(request, "您没有删除学习资源的权限")
        return redirect('view_resource', resource_id=resource_id)
    
    resource_title = resource.title
    resource.delete()
    messages.success(request, f"学习资源《{resource_title}》已删除")
    return redirect('learning_resources')

@login_required
@require_POST
def save_resource(request, resource_id):
    """收藏学习资源"""
    try:
        resource = LearningResource.objects.get(id=resource_id)
        resource.saved_by.add(request.user)
        messages.success(request, f"已收藏《{resource.title}》")
    except LearningResource.DoesNotExist:
        messages.error(request, "资源不存在或已被删除")
    
    # 重定向回之前的页面
    next_url = request.META.get('HTTP_REFERER', 'learning_resources')
    return redirect(next_url)

@login_required
@require_POST
def unsave_resource(request, resource_id):
    """取消收藏学习资源"""
    try:
        resource = LearningResource.objects.get(id=resource_id)
        resource.saved_by.remove(request.user)
        messages.success(request, f"已取消收藏《{resource.title}》")
    except LearningResource.DoesNotExist:
        messages.error(request, "资源不存在或已被删除")
    
    # 重定向回之前的页面
    next_url = request.META.get('HTTP_REFERER', 'learning_resources')
    return redirect(next_url)

@login_required
@require_POST
def rate_resource(request, resource_id):
    """评价学习资源"""
    try:
        resource = LearningResource.objects.get(id=resource_id)
        
        # 获取评分和评论
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if not rating or not rating.isdigit() or int(rating) < 1 or int(rating) > 5:
            messages.error(request, "请提供有效的评分（1-5）")
            return redirect('view_resource', resource_id=resource_id)
        
        # 检查用户是否已经评价过
        existing_rating = ResourceRating.objects.filter(
            user=request.user,
            resource=resource
        ).first()
        
        if existing_rating:
            # 更新现有评价
            existing_rating.score = rating
            existing_rating.comment = comment
            existing_rating.save()
            messages.success(request, "您的评价已更新")
        else:
            # 创建新评价
            ResourceRating.objects.create(
                user=request.user,
                resource=resource,
                score=rating,
                comment=comment
            )
            messages.success(request, "感谢您的评价")
        
    except LearningResource.DoesNotExist:
        messages.error(request, "资源不存在或已被删除")
    
    return redirect('view_resource', resource_id=resource_id)

@login_required
def recommend_resources(request):
    """推荐学习资源"""
    # 获取推荐资源
    recommended = get_recommended_resources(request.user)
    
    context = {
        'resources': recommended,
    }
    
    return render(request, 'correction_system/resources/recommended_resources.html', context)

# 辅助函数
def get_recommended_resources(user):
    """获取推荐资源的辅助函数"""
    from django.db.models import Avg, Count
    
    # 获取用户偏好
    user_interests = ''
    user_preferences = ''
    
    try:
        if hasattr(user, 'profile'):
            user_interests = getattr(user.profile, 'subjects_of_interest', '')
            user_preferences = getattr(user.profile, 'learning_preferences', '')
    except:
        # 如果获取失败，使用默认值
        pass
    
    # 基础查询
    resources = LearningResource.objects.annotate(
        avg_rating=Avg('ratings__score'),
        review_count=Count('ratings')
    )
    
    # 根据用户兴趣筛选
    if user_interests:
        interest_filter = Q()
        for interest in user_interests.split(','):
            interest = interest.strip()
            if interest:
                interest_filter |= Q(tags__icontains=interest)
        
        if interest_filter:
            interest_resources = resources.filter(interest_filter).order_by('-avg_rating', '-view_count')[:10]
            if interest_resources.exists():
                return interest_resources
    
    # 如果没有基于兴趣的资源，返回热门资源
    return resources.order_by('-avg_rating', '-view_count')[:10]

def reload_static(request):
    """
    用于清除Django模板缓存的视图
    仅在DEBUG模式下可用
    """
    if not settings.DEBUG:
        return HttpResponseForbidden("仅在调试模式下可用")
    
    from django.template.loader import get_template
    from django.template import engines
    
    # 清除Django模板缓存
    for engine in engines.all():
        if hasattr(engine, 'template_loaders'):
            for loader in engine.template_loaders:
                if hasattr(loader, 'reset'):
                    loader.reset()
                elif hasattr(loader, 'loaders'):
                    for subloader in loader.loaders:
                        if hasattr(subloader, 'reset'):
                            subloader.reset()
    
    # 确保导入settings
    from django.conf import settings
    
    # 强制从文件系统重新加载模板
    template_name = request.GET.get('template', 'correction_system/problems/view_problem.html')
    try:
        template = get_template(template_name)
        messages.success(request, f"成功重新加载模板: {template_name}")
    except Exception as e:
        messages.error(request, f"加载模板失败: {str(e)}")
    
    # 重定向回之前的页面
    redirect_to = request.GET.get('next', 'dashboard')
    return redirect(redirect_to) 