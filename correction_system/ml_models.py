import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
import joblib
import os
from django.conf import settings
import logging
from datetime import datetime, timedelta
import random
from .models import LearningResource, Problem, Homework
from django.db.models import Q, Count, Avg

logger = logging.getLogger(__name__)

class LearningAnalyzer:
    """学习数据分析器 - 使用机器学习算法分析学习模式和进展"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2)
        self.kmeans = KMeans(n_clusters=4, random_state=42)
        self.model_path = os.path.join(settings.BASE_DIR, 'correction_system/ml_models')
        os.makedirs(self.model_path, exist_ok=True)
    
    def analyze_performance(self, user_data):
        """
        分析用户学习表现，使用聚类算法识别学习模式
        
        参数:
            user_data: 包含用户学习数据的DataFrame (作业分数、问题解决次数等)
        
        返回:
            dict: 包含分析结果的字典
        """
        try:
            if len(user_data) < 3:
                return {
                    'cluster': None,
                    'learning_style': '数据不足',
                    'strengths': [],
                    'weaknesses': [],
                    'recommendations': ['继续积累更多的学习数据以获得更准确的分析']
                }
            
            # 预处理数据
            features = ['problem_count', 'homework_score_avg', 'correct_rate']
            X = self.scaler.fit_transform(user_data[features])
            
            # 应用聚类算法
            cluster = self.kmeans.fit_predict(X)[0]
            
            # 降维用于可视化
            pca_result = self.pca.fit_transform(X)
            
            # 基于聚类结果确定学习风格
            learning_styles = [
                '系统性学习者 - 稳定平衡的学习模式',
                '突击型学习者 - 学习效果波动较大',
                '深度专注型 - 在特定领域表现出色',
                '探索型学习者 - 涉猎广泛但深度不足'
            ]
            
            # 根据用户数据确定强项和弱项
            strengths = []
            weaknesses = []
            
            if user_data['homework_score_avg'].mean() > 80:
                strengths.append('作业完成质量高')
            else:
                weaknesses.append('作业完成质量有待提高')
                
            if user_data['correct_rate'].mean() > 0.7:
                strengths.append('问题解答准确率高')
            else:
                weaknesses.append('问题解答准确率有待提高')
            
            # 生成个性化建议
            recommendations = []
            if '作业完成质量有待提高' in weaknesses:
                recommendations.append('建议关注作业中的常见错误，提高作业质量')
            if '问题解答准确率有待提高' in weaknesses:
                recommendations.append('建议多复习和巩固基础知识，提高解题准确性')
            
            # 如果没有明显弱点，提供进一步提升的建议
            if not weaknesses:
                recommendations.append('建议尝试更具挑战性的题目来进一步提升能力')
            
            # 保存模型供后续使用
            joblib.dump(self.kmeans, os.path.join(self.model_path, 'kmeans_model.pkl'))
            joblib.dump(self.scaler, os.path.join(self.model_path, 'scaler_model.pkl'))
            joblib.dump(self.pca, os.path.join(self.model_path, 'pca_model.pkl'))
            
            return {
                'cluster': int(cluster),
                'learning_style': learning_styles[cluster],
                'pca_visualization': pca_result.tolist(),
                'strengths': strengths,
                'weaknesses': weaknesses,
                'recommendations': recommendations
            }
        except Exception as e:
            logger.error(f"学习分析错误: {str(e)}")
            return {
                'error': str(e),
                'learning_style': '分析出错',
                'strengths': [],
                'weaknesses': [],
                'recommendations': ['系统无法完成分析，请联系管理员']
            }
    
    def predict_performance_trend(self, history_data, periods=5):
        """
        使用简单的时间序列预测学习表现趋势
        
        参数:
            history_data: 历史学习数据，按时间排序
            periods: 预测未来的周期数
        
        返回:
            list: 预测的未来表现数据
        """
        try:
            if len(history_data) < 3:
                # 数据不足，返回平均值作为预测
                avg = history_data.mean() if len(history_data) > 0 else 70
                return [avg] * periods
            
            # 简单的指数平滑预测
            alpha = 0.3  # 平滑因子
            predictions = []
            last_value = history_data.iloc[-1]
            
            for _ in range(periods):
                # 指数平滑公式: next = alpha * current + (1-alpha) * previous
                next_value = alpha * history_data.iloc[-1] + (1 - alpha) * last_value
                predictions.append(float(next_value))
                last_value = next_value
                
            return predictions
        except Exception as e:
            logger.error(f"趋势预测错误: {str(e)}")
            return [70] * periods  # 发生错误时返回默认值


class ContentRecommender:
    """基于内容的推荐系统，为用户推荐相关学习资源"""
    
    def __init__(self):
        self.model_path = os.path.join(settings.BASE_DIR, 'correction_system/ml_models')
        os.makedirs(self.model_path, exist_ok=True)
    
    def build_feature_matrix(self, resources_data):
        """从资源数据构建特征矩阵"""
        # 假设我们有以下特征: 类型(向量化), 难度, 评分, 受欢迎程度
        # 实际应用中可以使用 TF-IDF 从描述中提取特征
        feature_matrix = []
        
        for resource in resources_data:
            # 简单特征工程 - 实际项目中应该更复杂
            features = [
                resource.get('difficulty', 2),  # 1-5的难度
                resource.get('avg_rating', 3.0),  # 1-5的评分
                resource.get('view_count', 0) / 100  # 标准化的浏览量
            ]
            
            # 资源类型的一位有效编码
            resource_type = resource.get('resource_type', 'ARTICLE')
            types = ['ARTICLE', 'VIDEO', 'BOOK', 'WEBSITE', 'EXERCISE']
            for t in types:
                features.append(1 if resource_type == t else 0)
                
            feature_matrix.append(features)
            
        return np.array(feature_matrix)
    
    def recommend_resources(self, user_profile, all_resources, n=5):
        """
        基于用户配置文件推荐学习资源
        
        参数:
            user_profile: 用户特征 (历史兴趣、弱项等)
            all_resources: 所有可用资源列表
            n: 推荐数量
            
        返回:
            list: 推荐资源ID列表
        """
        try:
            if not all_resources:
                return []
                
            # 构建资源特征矩阵
            resource_features = self.build_feature_matrix(all_resources)
            
            # 根据用户配置文件确定兴趣向量 (简化版)
            # 实际应用中，这应该基于用户的历史行为和偏好构建
            user_vector = np.array([
                user_profile.get('preferred_difficulty', 3),
                5.0,  # 偏好高评分
                0.5,  # 中等受欢迎程度
                # 用户对各种资源类型的偏好
                user_profile.get('prefer_article', 0.5),
                user_profile.get('prefer_video', 0.8),
                user_profile.get('prefer_book', 0.3),
                user_profile.get('prefer_website', 0.4),
                user_profile.get('prefer_exercise', 0.7)
            ])
            
            # 计算余弦相似度
            similarities = cosine_similarity([user_vector[:len(resource_features[0])]], resource_features)[0]
            
            # 获取最相似的资源索引
            top_indices = similarities.argsort()[-n:][::-1]
            
            # 返回推荐的资源ID
            recommended_ids = [all_resources[i]['id'] for i in top_indices]
            return recommended_ids
        except Exception as e:
            logger.error(f"资源推荐错误: {str(e)}")
            # 发生错误时返回随机推荐
            resource_ids = [r.get('id') for r in all_resources]
            return random.sample(resource_ids, min(n, len(resource_ids)))


# 公开API函数
def analyze_user_learning(user_id, problem_data, homework_data):
    """
    分析用户学习特点和趋势
    
    参数:
    - user_id: 用户ID
    - problem_data: 问题数据列表
    - homework_data: 作业数据列表
    
    返回:
    - 包含分析结果的字典
    """
    try:
        # 确保有足够的数据进行分析
        if len(problem_data) < 3 or len(homework_data) < 3:
            return {
                'learning_style': '数据不足，无法确定学习风格',
                'strength_subjects': ['需要更多数据'],
                'weakness_subjects': ['需要更多数据'],
                'score_prediction': [random.uniform(70, 90) for _ in range(5)],
                'consistency_score': 60,
                'engagement_score': 70,
                'improvement_score': 65,
                'recommendations': ['继续积累学习数据', '尝试更多类型的题目', '保持学习记录'],
                'cluster': 0  # 默认聚类
            }
        
        # 准备数据
        # 将问题数据转换为DataFrame
        problem_df = pd.DataFrame(problem_data)
        
        # 将作业数据转换为DataFrame
        homework_df = pd.DataFrame(homework_data)
        
        # 添加时间特征
        for df in [problem_df, homework_df]:
            df['created_at'] = pd.to_datetime(df['created_at'])
            df['day_of_week'] = df['created_at'].dt.dayofweek
            df['hour_of_day'] = df['created_at'].dt.hour
        
        # 计算特征
        # 1. 学习频率 - 每周学习天数
        weekly_learning_days = len(pd.concat([
            problem_df['created_at'].dt.date,
            homework_df['created_at'].dt.date
        ]).unique())
        
        # 2. 学习规律性 - 标准差
        problem_times = problem_df['hour_of_day'].values
        consistency_score = max(0, 100 - (np.std(problem_times) * 10)) if len(problem_times) > 0 else 50
        
        # 3. 进步指数 - 基于作业分数
        if len(homework_df) >= 3:
            # 确保分数是数值类型
            homework_df['score'] = homework_df['score'].apply(
                lambda x: float(x) if x is not None else 0.0
            )
            
            # 计算最近分数与之前分数的差异
            recent_scores = homework_df.sort_values('created_at')['score'].values
            
            # 避免None值
            recent_scores = [s for s in recent_scores if s is not None]
            
            if len(recent_scores) >= 2:
                score_diffs = np.diff(recent_scores)
                avg_improvement = np.mean(score_diffs)
                improvement_score = 50 + (avg_improvement * 5)  # 转换为0-100的分数
                improvement_score = max(0, min(100, improvement_score))
            else:
                improvement_score = 50
        else:
            improvement_score = 50
        
        # 4. 参与度 - 基于总活动量
        total_activities = len(problem_df) + len(homework_df)
        engagement_score = min(100, total_activities * 5)
        
        # 学习风格聚类 - 修改聚类逻辑，跳过K-means直接确定风格
        features = np.array([
            [consistency_score, engagement_score, improvement_score, weekly_learning_days]
        ])
        
        # 根据特征值直接确定学习风格，而不使用K-means聚类
        # 这避免了样本数量不足的问题
        if consistency_score > 70 and engagement_score > 50:
            cluster = 0  # 系统性学习者
        elif consistency_score < 50 and engagement_score > 70:
            cluster = 1  # 突击型学习者
        elif improvement_score > 70 and engagement_score < 60:
            cluster = 2  # 深度专注型
        else:
            cluster = 3  # 探索型学习者
        
        # 学习风格映射
        learning_styles = [
            '系统性学习者',  # 高一致性，中等参与度
            '突击型学习者',  # 低一致性，高参与度
            '深度专注型',    # 高改进，低参与度
            '探索型学习者'   # 中等一致性，高参与度
        ]
        
        learning_style = learning_styles[cluster]
        
        # 预测未来分数
        if len(homework_df) >= 3:
            recent_scores = homework_df.sort_values('created_at')['score'].values[-3:]
            # 确保没有None值
            recent_scores = [s if s is not None else 0.0 for s in recent_scores]
            
            # 简单线性预测
            slope = np.mean(np.diff(recent_scores))
            last_score = recent_scores[-1]
            
            # 生成预测，确保在范围内
            predictions = []
            for i in range(1, 6):
                pred = last_score + (slope * i)
                pred = max(60, min(100, pred))  # 限制在60-100范围内
                predictions.append(round(pred, 1))
        else:
            # 没有足够数据时生成随机预测
            predictions = [random.uniform(70, 90) for _ in range(5)]
            predictions = [round(p, 1) for p in predictions]
        
        # 分析优势和劣势科目 (模拟)
        strengths = ['数学', '物理'] if cluster in [0, 2] else ['语文', '英语']
        weaknesses = ['化学'] if cluster in [1, 3] else ['生物']
        
        # 生成建议
        recommendations = [
            '根据学习模式制定更合理的学习计划',
            '针对弱势学科增加练习量',
            '建议使用记忆卡片加强知识点记忆'
        ]
        
        if cluster == 0:  # 系统性学习者
            recommendations.append('保持当前学习节奏，可以尝试更有挑战性的题目')
        elif cluster == 1:  # 突击型学习者
            recommendations.append('建议分散学习时间，避免集中突击，提高学习效率')
        elif cluster == 2:  # 深度专注型
            recommendations.append('适当扩展学习范围，涉猎更多相关知识领域')
        else:  # 探索型学习者
            recommendations.append('在广泛学习的基础上，可以适当深入部分关键领域')
        
        # 返回分析结果
        return {
            'learning_style': learning_style,
            'strength_subjects': strengths,
            'weakness_subjects': weaknesses,
            'score_prediction': predictions,
            'consistency_score': round(float(consistency_score), 1),
            'engagement_score': round(float(engagement_score), 1),
            'improvement_score': round(float(improvement_score), 1),
            'recommendations': recommendations,
            'cluster': int(cluster)
        }
        
    except Exception as e:
        logger.error(f"用户学习分析错误: {str(e)}")
        # 返回默认分析结果
        return {
            'learning_style': '分析过程中出现错误',
            'strength_subjects': ['无法确定'],
            'weakness_subjects': ['无法确定'],
            'score_prediction': [75.0, 78.0, 80.0, 82.0, 85.0],
            'consistency_score': 60,
            'engagement_score': 70,
            'improvement_score': 65,
            'recommendations': ['继续积累学习数据', '系统记录学习过程', '尝试不同类型的题目'],
            'cluster': 0  # 默认聚类
        }

def get_resource_recommendations(user_id, interests='', preferences=''):
    """
    基于用户兴趣和学习偏好推荐学习资源
    
    参数:
        user_id (int): 用户ID
        interests (str): 用户感兴趣的学科，逗号分隔
        preferences (str): 用户学习偏好，逗号分隔
    
    返回:
        list: 推荐的学习资源列表
    """
    # 获取用户的问题和作业数据，用于分析用户兴趣
    user_problems = Problem.objects.filter(user_id=user_id)
    user_homeworks = Homework.objects.filter(user_id=user_id)
    
    # 从用户记录中提取关键词
    keywords = []
    
    # 从兴趣中提取关键词
    if interests:
        keywords.extend([i.strip() for i in interests.split(',')])
    
    # 从问题和作业中提取关键词
    for problem in user_problems:
        if problem.text_content:
            # 简单提取中文关键词（实际应用中可以使用更复杂的NLP技术）
            import re
            # 提取可能的学科名称
            subjects = ['数学', '语文', '英语', '物理', '化学', '生物', '历史', '地理', '政治']
            for subject in subjects:
                if subject in problem.text_content:
                    keywords.append(subject)
            
            # 提取问题中的其他关键词
            keywords.extend(re.findall(r'函数|方程|几何|力学|电学|原子|分子|细胞|基因|语法|阅读', problem.text_content))
    
    # 获取用户可能的资源类型偏好
    resource_type_preference = None
    if preferences:
        pref_list = [p.strip() for p in preferences.split(',')]
        if '视频学习' in pref_list:
            resource_type_preference = 'VIDEO'
        elif '阅读学习' in pref_list:
            resource_type_preference = 'ARTICLE'
    
    # 根据用户行为和偏好查询推荐资源
    query = LearningResource.objects.all()
    
    # 根据关键词筛选
    if keywords:
        keyword_query = Q()
        for keyword in set(keywords):  # 使用set去重
            keyword_query |= Q(title__icontains=keyword) | Q(description__icontains=keyword) | Q(tags__icontains=keyword)
        query = query.filter(keyword_query)
    
    # 根据资源类型偏好筛选
    if resource_type_preference:
        query = query.filter(resource_type=resource_type_preference)
    
    # 获取高评分和高查看量的资源
    query = query.annotate(avg_rating=Avg('ratings__score'), rating_count=Count('ratings'))
    
    # 先尝试获取同时满足关键词和类型的资源
    recommended = list(query.order_by('-avg_rating', '-view_count')[:10])
    
    # 如果推荐不足10个，添加一些高评分的资源
    if len(recommended) < 10:
        existing_ids = [r.id for r in recommended]
        more_resources = LearningResource.objects.exclude(id__in=existing_ids).annotate(
            avg_rating=Avg('ratings__score')
        ).order_by('-avg_rating', '-view_count')[:10-len(recommended)]
        
        recommended.extend(more_resources)
    
    return recommended 