from django.shortcuts import render
import os
import json
from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Problem, Homework
from .forms import TextProblemForm, ImageProblemForm, HomeworkForm
from .services import DeepSeekService

# 创建DeepSeek服务实例
deepseek_service = DeepSeekService()

def home(request):
    """主页视图"""
    return render(request, 'correction_system/home.html')

def solve_problem(request):
    """题目解答页面"""
    text_form = TextProblemForm()
    image_form = ImageProblemForm()
    context = {
        'text_form': text_form,
        'image_form': image_form,
        'solution': None,
    }
    return render(request, 'correction_system/solve.html', context)

def correct_homework(request):
    """作业批改页面"""
    form = HomeworkForm()
    context = {
        'form': form,
        'correction': None,
    }
    return render(request, 'correction_system/correct.html', context)

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
                    text_content=text_content
                )
                
                # 调用DeepSeek API解答题目
                solution = deepseek_service.solve_text_problem(text_content)
                
                # 更新题目解答
                problem.solution = solution
                problem.save()
                
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
                    image=image
                )
                
                # 获取保存后的图片路径
                image_path = os.path.join(settings.MEDIA_ROOT, problem.image.name)
                
                # 调用DeepSeek API解答题目
                solution = deepseek_service.solve_image_problem(image_path)
                
                # 更新题目解答
                problem.solution = solution
                problem.save()
                
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
                correction_status='PENDING'
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
