from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from correction_system.models import LearningResource
import random
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = '添加示例学习资源数据'

    def handle(self, *args, **kwargs):
        # 示例资源数据
        sample_resources = [
            # 数学类资源
            {
                'title': '高中数学必考公式大全',
                'description': '全面整理高中数学各册教材中的重要公式和定理，包含函数、导数、三角函数、立体几何等内容，是高考数学复习的必备资料。',
                'content': '<h3>函数部分</h3><ul><li>二次函数：y = ax² + bx + c (a≠0)</li><li>对数函数：y = log<sub>a</sub>x (a>0且a≠1)</li></ul><h3>导数公式</h3><ul><li>(C)′ = 0</li><li>(x<sup>n</sup>)′ = nx<sup>n-1</sup></li><li>(sin x)′ = cos x</li></ul>',
                'resource_type': 'ARTICLE',
                'tags': '数学,公式,高考,函数,导数',
                'difficulty_level': 2,
                'file_url': 'https://example.com/math-formulas.pdf',
                'view_count': random.randint(100, 500),
            },
            {
                'title': '立体几何解题技巧视频课程',
                'description': '本课程由知名数学特级教师讲解，深入浅出地讲解立体几何的常见解题思路和技巧，帮助学生攻克立体几何难题。',
                'content': '<p>本视频课程包含以下内容：</p><ol><li>空间几何体的基本性质</li><li>直线与平面的位置关系</li><li>二面角和三面角的计算</li><li>空间向量在立体几何中的应用</li><li>典型例题详解</li></ol>',
                'resource_type': 'VIDEO',
                'tags': '数学,立体几何,视频课程,空间向量',
                'difficulty_level': 3,
                'video_url': 'https://www.bilibili.com/video/BV1xx411c7mD',
                'view_count': random.randint(200, 800),
            },
            # 物理类资源
            {
                'title': '高中物理实验技巧与数据处理',
                'description': '详细讲解高中物理各项实验的操作要点和数据处理方法，帮助学生在实验题中获取高分。',
                'content': '<h3>实验注意事项</h3><p>1. 实验前要认真阅读实验要求和原理</p><p>2. 测量过程中注意读数方法，避免视差</p><h3>数据处理方法</h3><p>1. 有效数字的保留</p><p>2. 误差分析与处理</p><p>3. 线性回归方法</p>',
                'resource_type': 'ARTICLE',
                'tags': '物理,实验,数据处理,误差分析',
                'difficulty_level': 2,
                'file_url': 'https://example.com/physics-lab.pdf',
                'view_count': random.randint(80, 300),
            },
            {
                'title': '电磁学精讲与习题解析',
                'description': '系统讲解电磁学的基本概念、定律和应用，包含大量例题和习题解析，适合高中生深入学习电磁学知识。',
                'content': '<p>本资源包含以下内容：</p><ul><li>电场强度与电势的计算</li><li>磁场与安培力</li><li>电磁感应现象与法拉第定律</li><li>典型习题解析</li></ul>',
                'resource_type': 'BOOK',
                'tags': '物理,电磁学,习题,电场,磁场',
                'difficulty_level': 3,
                'file_url': 'https://example.com/electromagnetics.pdf',
                'view_count': random.randint(150, 600),
            },
            # 英语类资源
            {
                'title': '英语写作高分句型与范文',
                'description': '收集整理高考英语写作中常用的高级句型和地道表达，并提供各类型作文的优秀范文，帮助学生提高英语写作水平。',
                'content': '<h3>高级句型示例</h3><p>1. Not only...but also... 不仅...而且...</p><p>2. It is universally acknowledged that... 众所周知...</p><h3>议论文范文</h3><p>Topic: The Importance of Environmental Protection</p><p>Nowadays, environmental protection has become a concern of paramount importance...</p>',
                'resource_type': 'ARTICLE',
                'tags': '英语,写作,句型,范文,高考',
                'difficulty_level': 2,
                'file_url': 'https://example.com/english-writing.pdf',
                'view_count': random.randint(200, 700),
            },
            {
                'title': '英语听力训练与技巧',
                'description': '提供系统的英语听力训练材料和方法，包含新闻、对话、讲座等多种类型的听力材料，帮助学生提高英语听力能力。',
                'content': '<h3>听力提升方法</h3><ol><li>每天坚持听英语，培养语感</li><li>听前预测内容，带着问题听</li><li>听后复述内容，检验理解程度</li></ol><p>本资源包含60段精选听力材料，难度逐级提升。</p>',
                'resource_type': 'VIDEO',
                'tags': '英语,听力,技巧,训练',
                'difficulty_level': 2,
                'video_url': 'https://www.bilibili.com/video/BV1Wb411P7Lh',
                'view_count': random.randint(300, 900),
            },
            # 化学类资源
            {
                'title': '有机化学反应机理详解',
                'description': '深入讲解高中有机化学各类反应的机理，帮助学生理解反应本质，灵活应对各类有机化学题目。',
                'content': '<h3>加成反应</h3><p>加成反应是不饱和烃与其他试剂发生的反应，打开π键形成新的σ键...</p><h3>取代反应</h3><p>取代反应是有机物分子中的某些原子或原子团被其他原子或原子团替换的反应...</p>',
                'resource_type': 'ARTICLE',
                'tags': '化学,有机化学,反应机理,高中化学',
                'difficulty_level': 3,
                'file_url': 'https://example.com/organic-chemistry.pdf',
                'view_count': random.randint(100, 400),
            },
            {
                'title': '元素化学知识点总结',
                'description': '系统总结高中化学中常见元素的性质、化合物及其应用，包含金属、非金属元素的重要知识点。',
                'content': '<h3>非金属元素</h3><h4>氧族元素</h4><p>氧气：无色无味气体，难溶于水，是强氧化剂...</p><h4>卤族元素</h4><p>氯气：黄绿色有刺激性气味的气体，有强烈的漂白性和杀菌性...</p><h3>金属元素</h3><p>碱金属：化学性质活泼，易与氧、水反应...</p>',
                'resource_type': 'BOOK',
                'tags': '化学,元素化学,无机化学,金属,非金属',
                'difficulty_level': 2,
                'file_url': 'https://example.com/element-chemistry.pdf',
                'view_count': random.randint(150, 500),
            },
            # 生物类资源
            {
                'title': '细胞生物学图解教程',
                'description': '通过大量精美的图解，直观展示细胞结构、功能及细胞代谢等重要生物学过程，帮助学生理解抽象的细胞生物学概念。',
                'content': '<h3>细胞结构</h3><p>真核细胞的主要结构包括：细胞膜、细胞质、细胞核等...</p><h3>细胞代谢</h3><p>细胞呼吸过程包括：糖酵解、三羧酸循环和电子传递链...</p>',
                'resource_type': 'BOOK',
                'tags': '生物,细胞生物学,图解,细胞结构',
                'difficulty_level': 2,
                'file_url': 'https://example.com/cell-biology.pdf',
                'view_count': random.randint(120, 450),
            },
            {
                'title': '遗传学解题方法与技巧',
                'description': '详细讲解遗传学中的经典问题解题思路和方法，包含孟德尔遗传、连锁与交换、突变等内容的习题解析。',
                'content': '<h3>孟德尔遗传习题解析</h3><p>单因子遗传问题的分析方法：1. 确定显隐性关系 2. 分析亲本基因型 3. 计算子代比例...</p><h3>连锁遗传图解</h3><p>连锁交换的计算方法及图解...</p>',
                'resource_type': 'ARTICLE',
                'tags': '生物,遗传学,解题方法,孟德尔定律',
                'difficulty_level': 3,
                'file_url': 'https://example.com/genetics-problem-solving.pdf',
                'view_count': random.randint(100, 350),
            },
            # 通用学习工具
            {
                'title': '思维导图学习法完全指南',
                'description': '详细介绍思维导图的制作方法和在各学科学习中的应用，帮助学生高效整理知识点，提高学习效率。',
                'content': '<h3>思维导图的基本原则</h3><p>1. 中心主题放在中央</p><p>2. 使用关键词和图像</p><p>3. 分支呈放射状展开</p><h3>各学科应用示例</h3><p>数学：函数知识思维导图...</p><p>历史：朝代更替思维导图...</p>',
                'resource_type': 'TOOL',
                'tags': '学习方法,思维导图,知识整理,学习效率',
                'difficulty_level': 1,
                'file_url': 'https://example.com/mind-mapping.pdf',
                'view_count': random.randint(300, 1000),
            },
            {
                'title': '高效记忆技巧与方法',
                'description': '介绍多种科学有效的记忆方法，包括联想记忆法、位置记忆法、图像记忆法等，帮助学生在备考中快速记忆大量知识点。',
                'content': '<h3>联想记忆法</h3><p>将需要记忆的内容与已熟悉的事物建立联系，形成记忆链...</p><h3>位置记忆法</h3><p>将信息与特定的位置或场景联系起来，通过想象场景来提取信息...</p><h3>记忆宫殿技巧</h3><p>构建一个熟悉的场景作为"宫殿"，将信息放置在宫殿的不同位置...</p>',
                'resource_type': 'ARTICLE',
                'tags': '学习方法,记忆技巧,备考,高效学习',
                'difficulty_level': 1,
                'file_url': 'https://example.com/memory-techniques.pdf',
                'view_count': random.randint(250, 800),
            },
            # 综合类练习
            {
                'title': '高考模拟试题集锦',
                'description': '精选各省市近年高考模拟试题，涵盖语文、数学、英语、物理、化学、生物等学科，是考前冲刺的优质复习资料。',
                'content': '<h3>试题内容</h3><p>本资料包含10套完整的高考模拟试题，每套试题均配有详细解析和评分标准。学科包括：语文、数学（文/理）、英语、物理、化学、生物、政治、历史、地理。</p><h3>使用建议</h3><p>建议在复习基本完成后使用，模拟真实考试环境，严格按时间要求完成，然后对照解析进行订正。</p>',
                'resource_type': 'EXERCISE',
                'tags': '高考,模拟试题,综合练习,考前冲刺',
                'difficulty_level': 3,
                'file_url': 'https://example.com/exam-simulation.pdf',
                'view_count': random.randint(500, 1500),
            },
            {
                'title': '中考核心考点精讲精练',
                'description': '针对中考各学科核心考点进行详细讲解并配套针对性练习，帮助初三学生高效备战中考。',
                'content': '<h3>数学部分</h3><p>1. 解方程与不等式</p><p>2. 函数及其图像</p><p>3. 几何证明题解法</p><h3>物理部分</h3><p>1. 力学基础知识</p><p>2. 电学核心考点</p><h3>英语部分</h3><p>1. 重点语法知识</p><p>2. 阅读理解技巧</p>',
                'resource_type': 'EXERCISE',
                'tags': '中考,核心考点,练习题,初三,复习',
                'difficulty_level': 2,
                'file_url': 'https://example.com/middle-school-exam.pdf',
                'view_count': random.randint(300, 1000),
            }
        ]
        
        created_count = 0
        for resource_data in sample_resources:
            # 创建资源
            resource = LearningResource.objects.create(
                title=resource_data['title'],
                description=resource_data['description'],
                content=resource_data['content'],
                resource_type=resource_data['resource_type'],
                tags=resource_data['tags'],
                difficulty_level=resource_data['difficulty_level'],
                view_count=resource_data['view_count'],
                created_at=timezone.now() - timedelta(days=random.randint(1, 90)),
            )
            
            # 添加视频或文件URL
            if 'video_url' in resource_data:
                resource.video_url = resource_data['video_url']
            if 'file_url' in resource_data:
                resource.file_url = resource_data['file_url']
                
            resource.save()
            created_count += 1
            
            # 为资源创建一些随机评价
            self.create_random_ratings(resource)
            
            # 更新进度
            self.stdout.write(f"已创建资源: {resource.title}")
            
        self.stdout.write(self.style.SUCCESS(f'成功创建 {created_count} 个示例学习资源'))
    
    def create_random_ratings(self, resource):
        """为资源创建随机评价"""
        from correction_system.models import ResourceRating
        
        # 获取系统中的一些用户
        users = User.objects.all()[:5]  # 获取前5个用户
        
        if not users:
            self.stdout.write("没有可用的用户来创建评价，跳过评价创建")
            return  # 如果没有用户，就不创建评价
        
        # 评价内容样本
        positive_comments = [
            "这个资源非常有用，内容很全面。",
            "讲解清晰，对我的学习帮助很大。",
            "资料整理得很系统，很适合复习使用。",
            "正是我需要的内容，感谢分享！",
            "内容深入浅出，通俗易懂。"
        ]
        
        neutral_comments = [
            "内容还行，有一些地方可以更详细。",
            "基本符合预期，但希望有更多练习题。",
            "对初学者有帮助，但对进阶内容涉及不多。",
            "还不错，但排版可以再优化一下。",
            "内容较基础，适合入门学习。"
        ]
        
        negative_comments = [
            "内容过于简单，没有涉及难点。",
            "有些概念解释不够清楚。",
            "例题较少，应用性不强。",
            "内容组织不够合理，查找信息比较困难。",
            "与描述不太符合，期望值过高。"
        ]
        
        # 确保用户数量足够，否则调整评价数量范围
        num_users = len(users)
        if num_users == 0:
            return  # 已经在上面处理了，这里是额外检查
        
        # 为每个资源创建1到N个评价，其中N是用户数量和5中的较小值
        min_ratings = 1 if num_users > 0 else 0
        max_ratings = min(num_users, 5)
        num_ratings = random.randint(min_ratings, max_ratings)
        
        for i in range(num_ratings):
            user = users[i]
            score = random.choices([5, 4, 3, 2, 1], weights=[0.4, 0.3, 0.15, 0.1, 0.05])[0]
            
            if score >= 4:
                comment = random.choice(positive_comments)
            elif score >= 3:
                comment = random.choice(neutral_comments)
            else:
                comment = random.choice(negative_comments)
            
            ResourceRating.objects.create(
                user=user,
                resource=resource,
                score=score,
                comment=comment,
                created_at=timezone.now() - timedelta(days=random.randint(0, 30))
            )
            
            self.stdout.write(f"  - 已为资源创建评价：{user.username}, 评分: {score}") 