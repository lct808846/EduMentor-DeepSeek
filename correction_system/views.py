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
from django.db.models import Q, Avg, Count, Max
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Problem, Homework, KnowledgeCard, LearningResource, ResourceRecommendation, UserProfile, ResourceReview
from .forms import (
    TextProblemForm, ImageProblemForm, HomeworkForm, 
    UserRegisterForm, UserLoginForm, ProfileForm,
    KnowledgeCardForm, LearningResourceForm,
    ResourceSearchForm, ResourceReviewForm,
    ProblemSolveForm, HomeworkCorrectForm
)
from .services import DeepSeekService, KnowledgeExtractor, ResourceRecommender
from django.utils import timezone

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
    """查看单个题目详情"""
    problem = get_object_or_404(Problem, id=problem_id, user=request.user)
    
    # 获取相关知识卡片
    related_cards = KnowledgeCard.objects.filter(problem=problem)
    
    # 获取推荐学习资源（不依赖problem.tags，改为获取随机资源）
    recommended_resources = LearningResource.objects.all().order_by('?')[:3]
    
    context = {
        'problem': problem,
        'related_cards': related_cards,
        'recommended_resources': recommended_resources
    }
    return render(request, 'correction_system/history/view_problem.html', context)

@login_required
def view_homework(request, homework_id):
    """查看单个作业详情"""
    homework = get_object_or_404(Homework, id=homework_id, user=request.user)
    
    # 解析优点和缺点 - 检查属性是否存在
    strengths = []
    weaknesses = []
    
    # 安全地获取strengths属性
    if hasattr(homework, 'strengths') and homework.strengths:
        strengths = homework.strengths.split(';')
    
    # 安全地获取weaknesses属性
    if hasattr(homework, 'weaknesses') and homework.weaknesses:
        weaknesses = homework.weaknesses.split(';')
    
    # 获取相关知识卡片
    related_cards = KnowledgeCard.objects.filter(homework=homework)
    
    # 获取推荐学习资源（改为随机获取）
    recommended_resources = LearningResource.objects.all().order_by('?')[:3]
    
    context = {
        'homework': homework,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'related_cards': related_cards,
        'recommended_resources': recommended_resources
    }
    return render(request, 'correction_system/history/view_homework.html', context)

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
    """显示学习资源列表"""
    types = request.GET.getlist('type')
    keyword = request.GET.get('keyword')
    sort = request.GET.get('sort', 'relevance')
    
    resources = LearningResource.objects.all()
    
    # 应用筛选
    if types:
        resources = resources.filter(resource_type__in=types)
    
    if keyword:
        resources = resources.filter(title__icontains=keyword) | resources.filter(description__icontains=keyword) | resources.filter(tags__icontains=keyword)
    
    # 应用排序
    if sort == 'latest':
        resources = resources.order_by('-created_at')
    elif sort == 'rating':
        resources = resources.annotate(avg_rating=Avg('resourcereview__rating')).order_by('-avg_rating')
    elif sort == 'popular':
        resources = resources.annotate(save_count=Count('saved_by')).order_by('-save_count')
    
    # 获取用户收藏的资源
    saved_resources = request.user.saved_resources.all()[:5]
    
    # 分页
    paginator = Paginator(resources, 10)
    page_number = request.GET.get('page', 1)
    resources = paginator.get_page(page_number)
    
    context = {
        'resources': resources,
        'selected_types': types,
        'saved_resources': saved_resources,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': resources
    }
    return render(request, 'correction_system/resources/learning_resources.html', context)

@login_required
def view_resource(request, resource_id):
    """查看单个学习资源详情"""
    resource = get_object_or_404(LearningResource, id=resource_id)
    
    # 获取相关资源
    related_resources = None
    if resource.tags:
        related_resources = LearningResource.objects.filter(
            tags__icontains=resource.tags.split(',')[0],
            resource_type=resource.resource_type
        ).exclude(id=resource.id)[:3]
    
    # 获取用户评价
    reviews = ResourceReview.objects.filter(resource=resource).order_by('-created_at')
    user_review = ResourceReview.objects.filter(resource=resource, user=request.user).first()
    user_rating = user_review.rating if user_review else None
    
    context = {
        'resource': resource,
        'related_resources': related_resources,
        'reviews': reviews,
        'user_review': user_review,
        'user_rating': user_rating
    }
    return render(request, 'correction_system/resources/view_resource.html', context)

@login_required
def recommend_resources(request):
    """推荐学习资源"""
    problem_id = request.GET.get('problem_id')
    homework_id = request.GET.get('homework_id')
    
    problem = None
    homework = None
    recommended_resources = []
    
    if problem_id:
        problem = get_object_or_404(Problem, id=problem_id, user=request.user)
    
    if homework_id:
        homework = get_object_or_404(Homework, id=homework_id, user=request.user)
    
    # 处理搜索
    if request.method == 'GET' and 'keyword' in request.GET:
        keyword = request.GET.get('keyword')
        resource_types = request.GET.getlist('resource_type')
        difficulty = request.GET.get('difficulty')
        
        # 基础查询
        resources = LearningResource.objects.all()
        
        if keyword:
            resources = resources.filter(
                title__icontains=keyword
            ) | resources.filter(
                description__icontains=keyword
            ) | resources.filter(
                tags__icontains=keyword
            )
        
        if resource_types:
            resources = resources.filter(resource_type__in=resource_types)
        
        if difficulty:
            resources = resources.filter(difficulty=difficulty)
        
        recommended_resources = resources.order_by('-avg_rating')[:10]
    
    # 自动推荐
    elif problem or homework:
        tags = []
        if problem and problem.tags:
            tags.extend(problem.tags.split(','))
        if homework and homework.tags:
            tags.extend(homework.tags.split(','))
        
        if tags:
            for tag in tags:
                resources = LearningResource.objects.filter(tags__icontains=tag)
                recommended_resources.extend(resources)
            
            # 去重
            recommended_resources = list({resource.id: resource for resource in recommended_resources}.values())
            recommended_resources = recommended_resources[:10]
    
    context = {
        'problem': problem,
        'homework': homework,
        'recommended_resources': recommended_resources
    }
    return render(request, 'correction_system/resources/recommend.html', context)

@login_required
def save_resource(request, resource_id):
    """收藏学习资源"""
    resource = get_object_or_404(LearningResource, id=resource_id)
    
    if request.method == 'POST':
        if request.user not in resource.saved_by.all():
            resource.saved_by.add(request.user)
            messages.success(request, f'已将"{resource.title}"添加到收藏')
    
    return redirect(request.META.get('HTTP_REFERER', 'learning_resources'))

@login_required
def unsave_resource(request, resource_id):
    """取消收藏学习资源"""
    resource = get_object_or_404(LearningResource, id=resource_id)
    
    if request.method == 'POST':
        if request.user in resource.saved_by.all():
            resource.saved_by.remove(request.user)
            messages.success(request, f'已将"{resource.title}"从收藏中移除')
    
    return redirect(request.META.get('HTTP_REFERER', 'learning_resources'))

@login_required
def rate_resource(request, resource_id):
    """评价学习资源"""
    resource = get_object_or_404(LearningResource, id=resource_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        
        if not rating:
            messages.error(request, '请选择评分')
            return redirect('view_resource', resource_id=resource.id)
        
        # 检查用户是否已经评价过
        review, created = ResourceReview.objects.get_or_create(
            user=request.user,
            resource=resource,
            defaults={'rating': rating, 'comment': comment}
        )
        
        # 如果已经评价过，则更新
        if not created:
            review.rating = rating
            review.comment = comment
            review.save()
            messages.success(request, '评价已更新')
        else:
            messages.success(request, '评价已提交')
        
        # 更新资源的平均评分
        resource.avg_rating = ResourceReview.objects.filter(resource=resource).aggregate(avg=Avg('rating'))['avg']
        resource.review_count = ResourceReview.objects.filter(resource=resource).count()
        resource.save()
        
    return redirect('view_resource', resource_id=resource.id)

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
