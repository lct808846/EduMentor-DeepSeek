from django.shortcuts import render, redirect, get_object_or_404
import os
import json
from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Q, Avg, Count, Max, F, Case, When, IntegerField
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
    recent_problems = Problem.objects.filter(user=request.user).order_by('-created_at')[:3]
    recent_homeworks = Homework.objects.filter(user=request.user).order_by('-created_at')[:3]
    recent_cards = KnowledgeCard.objects.filter(user=request.user).order_by('-created_at')[:3]
    
    # 计算统计数据
    stats = {
        'problem_count': Problem.objects.filter(user=request.user).count(),
        'homework_count': Homework.objects.filter(user=request.user).count(),
        'card_count': KnowledgeCard.objects.filter(user=request.user).count(),
    }
    
    # 获取推荐资源
    recommended_resources = LearningResource.objects.all().order_by('-avg_rating')[:5]
    
    context = {
        'recent_problems': recent_problems,
        'recent_homeworks': recent_homeworks,
        'recent_cards': recent_cards,
        'stats': stats,
        'recommended_resources': recommended_resources,
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

def api_solve_problem(request):
    """处理题目解答API请求"""
    if request.method == 'POST':
        problem_type = request.POST.get('problem_type')
        
        if problem_type == 'text':
            form = TextProblemForm(request.POST)
            if form.is_valid():
                text_content = form.cleaned_data['text_content']
                
                # 保存题目到数据库
                problem = Problem.objects.create(
                    problem_type='TEXT',
                    text_content=text_content,
                    user=request.user if request.user.is_authenticated else None
                )
                
                # 调用DeepSeek API解答题目
                solution = deepseek_service.solve_text_problem(text_content)
                
                # 更新题目解答
                problem.solution = solution
                problem.save()
                
                # 如果用户已登录，生成知识卡片
                if request.user.is_authenticated:
                    KnowledgeExtractor.generate_knowledge_cards(problem, solution)
                    # 推荐学习资源
                    ResourceRecommender.recommend_resources(problem)
                
                return JsonResponse({
                    'status': 'success',
                    'solution': solution
                })
        
        elif problem_type == 'image':
            form = ImageProblemForm(request.POST, request.FILES)
            if form.is_valid():
                image = form.cleaned_data['image']
                
                # 保存题目到数据库
                problem = Problem.objects.create(
                    problem_type='IMAGE',
                    image=image,
                    user=request.user if request.user.is_authenticated else None
                )
                
                # 获取保存后的图片路径
                image_path = os.path.join(settings.MEDIA_ROOT, problem.image.name)
                
                # 调用DeepSeek API解答题目
                solution = deepseek_service.solve_image_problem(image_path)
                
                # 更新题目解答
                problem.solution = solution
                problem.save()
                
                # 如果用户已登录，生成知识卡片
                if request.user.is_authenticated:
                    KnowledgeExtractor.generate_knowledge_cards(problem, solution)
                    # 推荐学习资源
                    ResourceRecommender.recommend_resources(problem)
                
                return JsonResponse({
                    'status': 'success',
                    'solution': solution
                })
        
        return JsonResponse({
            'status': 'error',
            'message': '表单验证失败'
        })
    
    return JsonResponse({
        'status': 'error',
        'message': '仅支持POST请求'
    })

def api_correct_homework(request):
    """处理作业批改API请求"""
    if request.method == 'POST':
        form = HomeworkForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            
            # 保存作业到数据库
            homework = Homework.objects.create(
                image=image,
                correction_status='PENDING',
                user=request.user if request.user.is_authenticated else None
            )
            
            # 获取保存后的图片路径
            image_path = os.path.join(settings.MEDIA_ROOT, homework.image.name)
            
            # 调用DeepSeek API批改作业
            correction = deepseek_service.correct_homework(image_path)
            
            # 更新作业批改结果
            homework.correction_status = 'COMPLETED'
            homework.correction_result = correction['correction_result']
            homework.score = correction['score']
            homework.feedback = correction['feedback']
            homework.save()
            
            return JsonResponse({
                'status': 'success',
                'correction': correction
            })
        
        return JsonResponse({
            'status': 'error',
            'message': '表单验证失败'
        })
    
    return JsonResponse({
        'status': 'error',
        'message': '仅支持POST请求'
    })

# 用户认证相关视图
def user_register(request):
    """用户注册视图"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 创建用户资料
            UserProfile.objects.create(user=user)
            # 自动登录
            login(request, user)
            messages.success(request, '注册成功！已自动登录。')
            return redirect('home')
    else:
        form = UserRegisterForm()
    
    return render(request, 'correction_system/auth/register.html', {'form': form})

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

def user_logout(request):
    """用户登出视图"""
    logout(request)
    messages.success(request, '已成功登出！')
    return redirect('home')

@login_required
def user_profile(request):
    """用户资料视图"""
    # 获取用户资料，如果不存在则创建
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'profile': profile,
        'problem_count': Problem.objects.filter(user=request.user).count(),
        'homework_count': Homework.objects.filter(user=request.user).count(),
        'knowledge_card_count': KnowledgeCard.objects.filter(user=request.user).count(),
    }
    return render(request, 'correction_system/user/profile.html', context)

@login_required
def edit_profile(request):
    """编辑用户资料视图"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, '资料更新成功！')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'correction_system/auth/edit_profile.html', {'form': form})

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
    
    if problem_id:
        problem = get_object_or_404(Problem, id=problem_id, user=request.user)
    
    if request.method == 'POST':
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
    
    # 从AI生成卡片（如果有问题ID）
    generated_card = None
    if problem and request.GET.get('generate', False):
        # 从题目中提取更多信息来生成卡片
        problem_type_display = "图片" if problem.problem_type == 'IMAGE' else "文本"
        
        # 提取题目的前50个字符作为摘要
        if problem.problem_type == 'TEXT':
            problem_summary = problem.text_content[:100] if len(problem.text_content) > 100 else problem.text_content
        else:
            problem_summary = "图片题目"
        
        # 从解答中尝试提取关键信息
        solution_text = problem.solution or ""
        keywords = []
        solution_points = []
        
        # 提取关键概念（以"概念"、"定义"、"公式"等关键词为线索）
        import re
        concept_matches = re.findall(r'([概念|定义|公式|原理|定律|理论][：|:].+?)[。|；|\n]', solution_text)
        keywords.extend(concept_matches[:3])  # 最多取3个关键概念
        
        # 从解题过程中提取解题思路
        process_matches = re.findall(r'([解题思路|解题步骤|分析|方法][：|:].+?)[。|；|\n]', solution_text)
        solution_points.extend(process_matches[:3])  # 最多取3个解题思路
        
        # 尝试提取常见错误
        error_matches = re.findall(r'([错误|注意|易错点|误区][：|:].+?)[。|；|\n]', solution_text)
        
        # 构建卡片标题
        if "数学" in solution_text:
            subject = "数学"
        elif "物理" in solution_text:
            subject = "物理"
        elif "化学" in solution_text:
            subject = "化学"
        elif "语文" in solution_text:
            subject = "语文"
        elif "英语" in solution_text:
            subject = "英语"
        else:
            subject = "学科"
        
        # 从题目文本中提取可能的主题
        if problem.problem_type == 'TEXT':
            topic_matches = re.findall(r'[^，。；？！,.;?!]+?[是指表示意味着定义为]+.+?[。；？！.;?!]', problem.text_content)
            if topic_matches:
                topic = topic_matches[0][:20]  # 提取第一个定义句的前20个字
            else:
                # 否则从题目中提取前10个字作为主题
                topic = problem.text_content[:15] + "..."
        else:
            topic = "图片题目内容"
            
        # 构建更丰富的内容
        content_sections = []
        
        # 添加题目概述
        content_sections.append(f"## 题目概述\n\n{problem_summary}")
        
        # 添加关键概念部分
        content_sections.append("## 关键概念")
        if keywords:
            for i, keyword in enumerate(keywords, 1):
                content_sections.append(f"{i}. {keyword}")
        else:
            # 如果没有提取到关键概念，提供一些通用的内容
            if "数学" in subject:
                content_sections.append("1. 本题涉及的数学公式和原理")
            elif "物理" in subject:
                content_sections.append("1. 本题涉及的物理定律和现象")
            else:
                content_sections.append("1. 本题的核心概念和定义")
        
        # 添加解题思路部分
        content_sections.append("\n## 解题思路")
        if solution_points:
            for i, point in enumerate(solution_points, 1):
                content_sections.append(f"{i}. {point}")
        else:
            content_sections.append("1. 分析题目条件和要求")
            content_sections.append("2. 应用相关知识点解决问题")
            content_sections.append("3. 验证结果的合理性")
        
        # 添加常见错误部分
        content_sections.append("\n## 常见错误")
        if error_matches:
            for i, error in enumerate(error_matches, 1):
                content_sections.append(f"{i}. {error}")
        else:
            content_sections.append("1. 概念理解不清导致的错误")
            content_sections.append("2. 解题步骤遗漏或顺序错误")
            content_sections.append("3. 计算或推导过程中的疏忽")
        
        # 添加应用拓展部分
        content_sections.append("\n## 应用与拓展")
        content_sections.append("- 本知识点在其他类型题目中的应用")
        content_sections.append("- 与其他知识点的联系")
        content_sections.append("- 解决相似问题的方法")
        
        generated_content = "\n".join(content_sections)
        
        # 创建一个更具体的标题
        title = f"{subject}知识点：{topic}"
        
        generated_card = {
            'title': title,
            'content': generated_content
        }
    
    context = {
        'problem': problem,
        'generated_card': generated_card
    }
    return render(request, 'correction_system/knowledge/create_card.html', context)

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
    
    # 分页
    paginator = Paginator(resources, 12)  # 每页显示12个资源
    page = request.GET.get('page')
    
    try:
        resources = paginator.page(page)
    except PageNotAnInteger:
        resources = paginator.page(1)
    except EmptyPage:
        resources = paginator.page(paginator.num_pages)
    
    # 获取用户收藏的资源
    if request.user.is_authenticated:
        saved_resources = request.user.saved_resources.all()[:3]  # 只显示前3个收藏
    else:
        saved_resources = []
    
    context = {
        'resources': resources,
        'saved_resources': saved_resources,
        'selected_types': [resource_type] if resource_type else [],
        'is_paginated': resources.has_other_pages(),
        'page_obj': resources,
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
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'learning_preferences'):
        recommended_resources = get_resource_recommendations(
            request.user.id, 
            interests=getattr(request.user.profile, 'subjects_of_interest', ''),
            preferences=getattr(request.user.profile, 'learning_preferences', '')
        )[:5]
    else:
        # 如果没有足够的用户数据，返回几个评分最高的资源
        recommended_resources = LearningResource.objects.annotate(
            avg_rating=Avg('ratings__score')
        ).order_by('-avg_rating')[:5]
    
    context = {
        'resource': resource,
        'similar_resources': similar_resources,
        'recommended_resources': recommended_resources,
    }
    
    return render(request, 'correction_system/resources/view_resource.html', context)

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
    # 获取用户偏好
    user_interests = ''
    user_preferences = ''
    
    if hasattr(request.user, 'profile'):
        user_interests = getattr(request.user.profile, 'subjects_of_interest', '')
        user_preferences = getattr(request.user.profile, 'learning_preferences', '')
    
    # 获取推荐资源
    recommended = get_resource_recommendations(
        request.user.id, 
        interests=user_interests,
        preferences=user_preferences
    )
    
    # 如果没有足够的推荐，添加一些热门资源
    if len(recommended) < 10:
        popular_resources = LearningResource.objects.annotate(
            avg_rating=Avg('ratings__score')
        ).order_by('-view_count', '-avg_rating')[:10]
        
        # 合并推荐和热门资源，确保没有重复
        existing_ids = [r.id for r in recommended]
        for resource in popular_resources:
            if resource.id not in existing_ids and len(recommended) < 10:
                recommended.append(resource)
    
    context = {
        'resources': recommended,
    }
    
    return render(request, 'correction_system/resources/recommended_resources.html', context)

# 用户资料相关视图
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
    profile = request.user.profile
    
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
        'school': {'value': profile.school},
        'grade': {'value': profile.grade},
        'subjects_of_interest': {'value': profile.subjects_of_interest},
        'bio': {'value': profile.bio},
        'avatar': {'value': profile.avatar}
    }
    
    context = {
        'form': form
    }
    return render(request, 'correction_system/auth/edit_profile.html', context)

@login_required
def problem_list(request):
    """显示所有题目列表，支持搜索和筛选"""
    query = request.GET.get('q', '')
    problem_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    
    # 基本查询：当前用户的所有题目
    problems = Problem.objects.filter(user=request.user).order_by('-created_at')
    
    # 应用搜索查询
    if query:
        problems = problems.filter(
            Q(problem_content__icontains=query) |
            Q(user_answer__icontains=query) |
            Q(solution__icontains=query)
        )
    
    # 应用类型筛选
    if problem_type:
        problems = problems.filter(problem_type=problem_type)
    
    # 应用状态筛选
    if status == 'correct':
        problems = problems.filter(is_correct=True)
    elif status == 'incorrect':
        problems = problems.filter(is_correct=False)
    
    # 分页
    paginator = Paginator(problems, 9)  # 每页显示9个题目
    page = request.GET.get('page')
    
    try:
        problems = paginator.page(page)
    except PageNotAnInteger:
        problems = paginator.page(1)
    except EmptyPage:
        problems = paginator.page(paginator.num_pages)
    
    context = {
        'problems': problems,
        'query': query,
        'selected_type': problem_type,
        'selected_status': status,
    }
    return render(request, 'correction_system/problems/problem_list.html', context)

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

# 学习分析相关视图
import json
import random
from datetime import datetime, timedelta
import numpy as np
from django.db.models import Avg
from django.utils import timezone

from .ml_models import analyze_user_learning, get_resource_recommendations

@login_required
def learning_analytics(request):
    """学习分析视图，展示用户学习数据和AI分析结果"""
    user = request.user
    
    # 获取用户的问题和作业数据
    problems = Problem.objects.filter(user=user).order_by('-created_at')
    homeworks = Homework.objects.filter(user=user).order_by('-created_at')
    
    # 基本统计数据
    problem_count = problems.count()
    homework_count = homeworks.count()
    correct_problems = problems.filter(is_correct=True).count()
    correct_rate = int(correct_problems / problem_count * 100) if problem_count > 0 else 0
    avg_score = homeworks.aggregate(avg=Avg('score'))['avg'] or 0
    avg_score = round(avg_score, 1)
    
    # 准备AI分析所需数据
    problem_data = list(problems.values('id', 'problem_type', 'is_correct', 'created_at'))
    homework_data = list(homeworks.values('id', 'score', 'correction_result', 'created_at'))
    
    # 调用机器学习模型进行分析
    analysis_results = analyze_user_learning(user.id, problem_data, homework_data)
    
    # 分数走势图数据
    recent_homeworks = homeworks[:10]  # 最近10次作业
    dates = [h.created_at.strftime('%Y-%m-%d') for h in recent_homeworks]
    scores = [float(h.score) if h.score is not None else 0.0 for h in recent_homeworks]
    # 反转顺序以便按时间顺序显示
    dates.reverse()
    scores.reverse()
    
    # 准备预测数据
    current_score = scores[-1] if scores else avg_score
    prediction_data = [current_score]
    if 'score_prediction' in analysis_results and analysis_results['score_prediction']:
        prediction_data.extend(analysis_results['score_prediction'])
    else:
        # 如果没有预测数据，生成一些示例数据
        last_score = current_score
        for _ in range(5):
            next_score = max(60, min(100, last_score + random.uniform(-5, 8)))
            prediction_data.append(round(next_score, 1))
            last_score = next_score
    
    # 学科能力雷达图数据
    # 提取用户感兴趣的科目
    subjects = []
    if hasattr(user, 'profile') and user.profile.subjects_of_interest:
        subjects = [s.strip() for s in user.profile.subjects_of_interest.split(',')]
    
    if not subjects:
        # 默认科目
        subjects = ['数学', '语文', '英语', '物理', '化学', '生物']
    
    # 为每个科目生成能力值（实际中应基于真实数据）
    user_abilities = []
    avg_abilities = []
    subjects_radar = []
    
    for subject in subjects:
        # 获取该科目的问题和作业
        subject_problems = problems.filter(text_content__icontains=subject)
        subject_homeworks = homeworks.filter(text_content__icontains=subject)
        
        # 计算该科目的能力值
        correct_count = subject_problems.filter(is_correct=True).count()
        total_count = subject_problems.count()
        subject_correct_rate = correct_count / total_count * 100 if total_count > 0 else 0
        
        subject_avg_score = subject_homeworks.aggregate(avg=Avg('score'))['avg'] or 0
        
        # 基于正确率和平均分计算能力值（0-100）
        ability_value = (subject_correct_rate * 0.4 + subject_avg_score * 0.6)
        
        # 添加用户能力值和平均值（模拟）
        user_abilities.append(round(ability_value, 1))
        avg_abilities.append(round(max(50, min(90, ability_value * random.uniform(0.85, 1.1))), 1))
        
        # 雷达图指标
        subjects_radar.append({'name': subject, 'max': 100})
    
    # 学习活动热力图数据
    # 获取最近3个月的日期范围
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=90)
    calendar_range = f'{start_date.strftime("%Y-%m-%d")},{end_date.strftime("%Y-%m-%d")}'
    
    # 构建活动数据
    activity_data = []
    current_date = start_date
    
    # 收集所有活动日期
    activity_dates = []
    activity_dates.extend([p.created_at.date() for p in problems if p.created_at.date() >= start_date])
    activity_dates.extend([h.created_at.date() for h in homeworks if h.created_at.date() >= start_date])
    
    # 计算每天的活动次数
    while current_date <= end_date:
        # 计算当天活动次数
        daily_count = activity_dates.count(current_date)
        
        # 添加数据，格式：[日期字符串, 活动次数]
        if daily_count > 0:
            activity_data.append([current_date.strftime('%Y-%m-%d'), daily_count])
            
        current_date += timedelta(days=1)
    
    # 学习风格散点图数据
    # 使用PCA结果构建散点数据
    learning_styles = [
        '系统性学习者',
        '突击型学习者',
        '深度专注型',
        '探索型学习者'
    ]
    
    # 模拟不同学习风格的散点位置
    learning_styles_scatter = [
        [-1.5, 1.2, learning_styles[0]],  # 系统性学习者
        [1.8, -0.5, learning_styles[1]],  # 突击型学习者
        [-0.8, -1.7, learning_styles[2]],  # 深度专注型
        [1.2, 1.5, learning_styles[3]]    # 探索型学习者
    ]
    
    # 确定用户在散点图中的位置
    user_style_index = analysis_results.get('cluster', 0)
    if user_style_index is None or user_style_index >= len(learning_styles):
        user_style_index = 0
    
    context = {
        'stats': {
            'problem_count': problem_count,
            'homework_count': homework_count,
            'correct_rate': correct_rate,
            'avg_score': avg_score
        },
        'analysis': analysis_results,
        'dates': json.dumps(dates),
        'scores': json.dumps(scores),
        'subjects_radar': json.dumps(subjects_radar),
        'user_abilities': json.dumps(user_abilities),
        'avg_abilities': json.dumps(avg_abilities),
        'calendar_range': json.dumps(calendar_range),
        'activity_data': json.dumps(activity_data),
        'learning_styles_scatter': json.dumps(learning_styles_scatter),
        'user_style_index': json.dumps(user_style_index),
        'prediction_data': json.dumps(prediction_data)
    }
    
    return render(request, 'correction_system/analytics/learning_analytics.html', context)

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
