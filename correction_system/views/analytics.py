import json
import random
from datetime import datetime, timedelta
import numpy as np
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Case, When, IntegerField, F
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse

from correction_system.models import Problem, Homework, LearningResource
from correction_system.ml_models import analyze_user_learning, get_resource_recommendations

@login_required
def learning_analytics(request):
    """学习分析视图，展示用户学习数据和AI分析结果"""
    user = request.user
    
    # 调试模式 - 如果URL中有debug参数，使用模拟数据
    if request.GET.get('debug'):
        # 返回包含完整模拟数据的简化分析页面
        return debug_analytics(request)
    
    # 获取用户的问题和作业数据
    problems = Problem.objects.filter(user=user).order_by('-created_at')
    homeworks = Homework.objects.filter(user=user).order_by('-created_at')
    
    # 判断用户是否是新用户（没有数据）
    is_new_user = problems.count() == 0 and homeworks.count() == 0
    
    # 基本统计数据
    problem_count = problems.count()
    homework_count = homeworks.count()
    correct_problems = problems.filter(solution__isnull=False).exclude(solution='').count()
    correct_rate = int(correct_problems / problem_count * 100) if problem_count > 0 else 0
    avg_score = homeworks.aggregate(avg=Avg('score'))['avg'] or 0
    avg_score = round(avg_score, 1)
    
    # 准备AI分析所需数据 
    problem_data = list(problems.values('id', 'problem_type', 'created_at'))
    
    # 手动添加is_correct属性，用于兼容analyze_user_learning函数
    for p in problem_data:
        # 获取原始问题对象
        problem = problems.get(id=p['id'])
        # 根据solution字段判断是否正确
        p['is_correct'] = bool(problem.solution and problem.solution.strip())
    
    homework_data = list(homeworks.values('id', 'score', 'correction_result', 'created_at'))
    
    # 处理所有None值，确保score字段为数值
    for h in homework_data:
        if h['score'] is None:
            h['score'] = 0.0
        else:
            try:
                h['score'] = float(h['score'])
            except (ValueError, TypeError):
                h['score'] = 0.0
    
    # 调用机器学习模型进行分析
    analysis_results = analyze_user_learning(user.id, problem_data, homework_data)
    
    # 输出分析结果到日志，帮助调试
    print("分析结果:", json.dumps(analysis_results, ensure_ascii=False))
    
    # 分数走势图数据
    recent_homeworks = homeworks[:10]  # 最近10次作业
    dates = []
    scores = []
    
    for h in recent_homeworks:
        if h.created_at and h.score is not None:
            dates.append(h.created_at.strftime('%Y-%m-%d'))
            try:
                scores.append(float(h.score))
            except (ValueError, TypeError):
                scores.append(0.0)
    
    # 反转顺序以便按时间顺序显示
    dates.reverse()
    scores.reverse()
    
    # 为新用户准备空数据集而不是随机数据
    if is_new_user:
        empty_data = True
        # 提供空数据或占位符
        dates = []
        scores = []
        prediction_data = []
    else:
        empty_data = False
        # 如果数据不足但不是新用户，提供简单的预测数据
        if len(dates) < 3:
            today = timezone.now().date()
            dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(2)]
            dates.reverse()
            # 使用用户平均分而不是随机数
            scores = [avg_score] * 2
        
        # 预测数据
        current_score = scores[-1] if scores else 75.0
        prediction_data = [current_score]
        if 'score_prediction' in analysis_results and analysis_results['score_prediction']:
            prediction_data.extend(analysis_results['score_prediction'])
        else:
            # 使用平缓上升的预测而不是随机波动
            for i in range(5):
                next_score = min(100, current_score + 1.5 * (i+1))
                prediction_data.append(round(next_score, 1))
    
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
        
        # 修复：Homework模型没有text_content字段，改用correction_result或feedback字段
        subject_homeworks = homeworks.filter(
            Q(correction_result__icontains=subject) | 
            Q(feedback__icontains=subject)
        )
        
        # 计算该科目的能力值
        correct_count = subject_problems.filter(solution__isnull=False).exclude(solution='').count()
        total_count = subject_problems.count()
        subject_correct_rate = correct_count / total_count * 100 if total_count > 0 else 0
        
        subject_avg_score = subject_homeworks.aggregate(avg=Avg('score'))['avg'] or 0
        
        # 基于正确率和平均分计算能力值（0-100）
        ability_value = (subject_correct_rate * 0.4 + subject_avg_score * 0.6)
        
        # 对于新用户，所有科目能力值为0
        if is_new_user:
            ability_value = 0
        elif ability_value == 0 and not is_new_user:
            # 对于有部分数据的用户，使用一个基础值而不是随机值
            ability_value = 50
        
        # 添加用户能力值和平均值
        user_abilities.append(round(ability_value, 1))
        avg_abilities.append(75.0)  # 使用固定平均值作为参考
        
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
    activity_dates.extend([p.created_at.date() for p in problems if p.created_at and p.created_at.date() >= start_date])
    activity_dates.extend([h.created_at.date() for h in homeworks if h.created_at and h.created_at.date() >= start_date])
    
    # 计算每天的活动次数
    while current_date <= end_date:
        # 计算当天活动次数
        daily_count = activity_dates.count(current_date)
        
        # 添加数据，格式：[日期字符串, 活动次数]
        if daily_count > 0:
            activity_data.append([current_date.strftime('%Y-%m-%d'), daily_count])
            
        current_date += timedelta(days=1)
    
    # 对于新用户不生成随机热力图数据
    if is_new_user:
        activity_data = []
    
    # 学习风格散点图数据
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
        'calendar_range': calendar_range,
        'activity_data': json.dumps(activity_data),
        'learning_styles_scatter': json.dumps(learning_styles_scatter),
        'user_style_index': user_style_index,
        'prediction_data': json.dumps(prediction_data),
        'debug_mode': False,
        'is_new_user': is_new_user,
        'empty_data': empty_data
    }
    
    return render(request, 'correction_system/analytics/learning_analytics.html', context)

def debug_analytics(request):
    """简化版分析页面，使用模拟数据进行调试"""
    # 基本统计
    stats = {
        'problem_count': 25,
        'homework_count': 12,
        'correct_rate': 78,
        'avg_score': 85.5
    }
    
    # 分析结果
    analysis = {
        'learning_style': '系统性学习者',
        'strength_subjects': ['数学', '物理'],
        'weakness_subjects': ['化学'],
        'consistency_score': 82.5,
        'engagement_score': 75.0,
        'improvement_score': 68.5,
        'recommendations': [
            '根据学习模式制定更合理的学习计划',
            '针对弱势学科增加练习量',
            '建议使用记忆卡片加强知识点记忆',
            '保持当前学习节奏，可以尝试更有挑战性的题目'
        ],
        'cluster': 0
    }
    
    # 分数走势图数据
    today = timezone.now().date()
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(10)]
    dates.reverse()
    scores = [75, 78, 72, 80, 82, 79, 85, 83, 88, 90]
    
    # 预测数据
    prediction_data = [90, 92, 93, 95, 96, 98]
    
    # 科目雷达图
    subjects = ['数学', '语文', '英语', '物理', '化学', '生物']
    subjects_radar = [{'name': subject, 'max': 100} for subject in subjects]
    user_abilities = [85, 75, 80, 88, 60, 72]
    avg_abilities = [75, 78, 72, 80, 75, 70]
    
    # 活动热力图
    activity_data = []
    for i in range(90):
        if random.random() > 0.7:  # 30%的概率有活动
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            activity_data.append([date, random.randint(1, 3)])
    
    # 学习风格散点
    learning_styles = ['系统性学习者', '突击型学习者', '深度专注型', '探索型学习者']
    learning_styles_scatter = [
        [-1.5, 1.2, learning_styles[0]],
        [1.8, -0.5, learning_styles[1]],
        [-0.8, -1.7, learning_styles[2]],
        [1.2, 1.5, learning_styles[3]]
    ]
    
    # 日历范围
    start_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    calendar_range = f'{start_date},{end_date}'
    
    context = {
        'stats': stats,
        'analysis': analysis,
        'dates': json.dumps(dates),
        'scores': json.dumps(scores),
        'subjects_radar': json.dumps(subjects_radar),
        'user_abilities': json.dumps(user_abilities),
        'avg_abilities': json.dumps(avg_abilities),
        'calendar_range': calendar_range,
        'activity_data': json.dumps(activity_data),
        'learning_styles_scatter': json.dumps(learning_styles_scatter),
        'user_style_index': 0,
        'prediction_data': json.dumps(prediction_data),
        'debug_mode': True,
        'is_new_user': False,
        'empty_data': False
    }
    
    return render(request, 'correction_system/analytics/learning_analytics.html', context) 