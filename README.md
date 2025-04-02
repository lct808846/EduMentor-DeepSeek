# 智学导师 - AI驱动的智能学习辅助系统


## 📖 项目简介

智学导师是一个基于人工智能技术的智能学习辅助系统，集成了先进的大语言模型与图像识别技术，旨在为学生提供全方位的学习支持。本系统通过智能解题、作业批改、知识管理、学习分析等功能，帮助学生高效学习、科学掌握知识点，提升学习体验和学习效果。

### 🎯 目标用户

- 中小学生：需要题目解答和作业批改辅助
- 高中及大学生：需要深度知识理解和学习规划
- 教师：需要高效批改工具和学生学习分析
- 家长：需要了解孩子的学习情况和学习建议

## ✨ 核心功能

### 1. 智能题目解答

- **文本题目解答**：支持语文、数学、英语、物理、化学、生物等学科的文本题目智能解答
- **图片题目识别与解答**：通过OCR技术，支持拍照上传题目，自动识别文字并给出详细解答
- **解题过程展示**：不仅提供答案，更展示完整解题思路和方法，帮助学生理解知识点
- **多角度解法**：对于同一道题目，提供多种解题思路，培养灵活思维能力

### 2. 智能作业批改

- **作业自动评分**：支持文本和图片作业上传，智能评分并给出详细批改意见
- **错误分析与建议**：针对错误点进行深入分析，并提供有针对性的改进建议
- **知识点关联**：将作业中涉及的知识点与知识卡片系统关联，便于复习和巩固
- **进步追踪**：记录批改历史，分析学习曲线，追踪学习进步

### 3. 知识卡片系统

- **智能卡片生成**：基于题目和作业批改自动生成知识卡片，归纳重要知识点
- **卡片分类管理**：按学科、章节、难度等多维度分类管理知识卡片
- **关联推荐**：根据知识点关联性，推荐相关卡片，构建完整知识网络
- **记忆曲线优化**：基于艾宾浩斯遗忘曲线，提醒复习，巩固记忆

### 4. 学习资源库

- **精选学习资源**：提供高质量的学习材料、视频教程、习题集等
- **个性化推荐**：根据学习历史和偏好，智能推荐适合的学习资源
- **用户评价系统**：允许用户对资源进行评分和评价，优化推荐质量
- **收藏与分享**：支持收藏喜欢的资源，并分享给其他用户

### 5. 学习分析

- **学习数据可视化**：通过直观的图表展示学习情况、强弱项、学习时间分布等
- **学科能力雷达图**：多维度展示各学科能力水平，明确提升方向
- **学习风格分析**：识别个人学习风格，提供匹配的学习策略建议
- **进步趋势预测**：基于历史数据预测学习趋势，制定合理的学习目标

### 6. 学习历史记录

- **全面历史记录**：记录解题、作业批改、知识卡片创建等学习活动
- **时间轴展示**：按时间顺序展示学习历程，直观了解学习轨迹
- **数据导出**：支持导出学习数据，便于长期分析和存档
- **隐私保护**：严格保护用户学习数据，提供数据管理选项

## 🛠️ 技术栈

### 后端框架
- **Django 4.2.7**：Python Web框架，负责整体系统架构
- **Django REST framework 3.14.0**：提供API服务，支持前后端分离

### 前端技术
- **Bootstrap 5.1.3**：响应式UI框架，提供美观的用户界面
- **jQuery 3.6.0**：JavaScript库，简化DOM操作
- **ECharts 5.4.0**：数据可视化图表库，用于学习分析模块

### 数据库
- **SQLite**（开发环境）：轻量级数据库，便于开发和测试
- **PostgreSQL**（生产环境）：强大的关系型数据库，保障数据安全和性能

### AI与机器学习
- **DeepSeek API**：大语言模型，提供智能问答和内容生成能力
- **Tesseract OCR 5.3.0**：开源光学字符识别引擎，用于图片题目文字识别
- **OpenCV 4.8.1**：计算机视觉库，用于图像预处理
- **scikit-learn 1.3.2**：机器学习库，用于数据分析和预测

### 其他工具
- **Redis**：缓存系统，提升响应速度
- **Celery**：分布式任务队列，处理异步任务
- **Git**：版本控制系统，管理代码更新

## 📦 安装与使用

### 系统要求
- Python 3.8+
- pip 20.0+
- Tesseract OCR 5.0+
- Git

### 安装步骤

#### 1. 克隆代码仓库
```bash
git clone https://github.com/lct808846/EduMentor-DeepSeek.git
cd EduMentor-DeepSeek
```

#### 2. 创建并激活虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装Python依赖
```bash
pip install -r requirements.txt
```

#### 4. 安装Tesseract OCR

##### Windows
1. 从[官方GitHub](https://github.com/UB-Mannheim/tesseract/wiki)下载安装包
2. 安装时选择中文语言包（如需其他语言也可选择）
3. 添加Tesseract到系统环境变量（默认路径：`C:\Program Files\Tesseract-OCR`）

##### macOS
```bash
brew install tesseract
brew install tesseract-lang  # 安装语言包
```

##### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-chi-sim  # 中文简体语言包
```

#### 5. 配置环境变量
创建`.env`文件，配置必要的环境变量：
```
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///db.sqlite3
DEEPSEEK_API_KEY=your_deepseek_api_key
TESSERACT_CMD=path/to/tesseract  # Windows可能需要手动设置
```

#### 6. 初始化数据库
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 7. 创建超级用户
```bash
python manage.py createsuperuser
```

#### 8. 添加示例数据（可选）
```bash
python  manage.py add_sample_resources
```

#### 9. 启动开发服务器
```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000/ 开始使用智学导师系统。

### 生产环境部署

对于生产环境，建议使用：
- **Gunicorn** 作为WSGI服务器
- **Nginx** 作为反向代理
- **PostgreSQL** 作为数据库
- **Redis** 用于缓存和Celery
- **HTTPS** 确保安全通信

详细部署文档请参考`docs/deployment.md`。

## 📁 项目结构

```
EduMentor-DeepSeek/
├── correction_system/        # 主应用
│   ├── management/           # 管理命令
│   ├── migrations/           # 数据库迁移文件
│   ├── models/               # 数据模型
│   ├── services/             # 服务层
│   │   ├── ai_service.py     # AI服务接口
│   │   ├── deepseek.py       # DeepSeek API集成
│   │   └── ocr_service.py    # OCR服务
│   ├── static/               # 静态文件
│   ├── templates/            # HTML模板
│   ├── tests/                # 测试代码
│   ├── utils/                # 工具函数
│   ├── views/                # 视图函数
│   ├── apps.py               # 应用配置
│   ├── signals.py            # 信号处理
│   └── urls.py               # URL路由
├── ml_models/                # 机器学习模型
│   ├── data_analysis.py      # 数据分析工具
│   ├── learning_analytics.py # 学习分析算法
│   └── recommender.py        # 推荐系统
├── docs/                     # 项目文档
├── static/                   # 全局静态文件
├── media/                    # 用户上传文件
├── templates/                # 全局模板
├── manage.py                 # Django管理脚本
├── requirements.txt          # Python依赖
└── README.md                 # 项目说明
```

## 📊 数据模型设计

### 用户相关模型
- **User**：Django内置用户模型，包含基本用户信息
- **UserProfile**：用户扩展信息，包含头像、个人简介、学习目标等

### 学习内容模型
- **Problem**：题目模型，记录用户提交的题目和系统解答
- **Homework**：作业模型，记录用户提交的作业和批改结果
- **KnowledgeCard**：知识卡片模型，存储知识点、解释和关联信息
- **LearningResource**：学习资源模型，包含资源信息和分类

### 学习记录模型
- **LearningActivity**：学习活动记录，包含活动类型、时间和详情
- **UserProgress**：用户学习进度，记录各学科能力水平和进步情况
- **ResourceInteraction**：用户与资源交互记录，包含收藏、评分等

## 🔒 隐私与安全

智学导师系统高度重视用户数据隐私和安全：

- **数据加密**：敏感数据使用强加密算法保护
- **访问控制**：严格的权限管理，确保用户只能访问自己的数据
- **安全审计**：定期进行安全审计和漏洞扫描
- **数据最小化**：仅收集必要的用户数据
- **透明政策**：明确的隐私政策，告知用户数据使用方式
- **数据导出**：用户可以导出和删除自己的数据

## 🤝 贡献指南

我们欢迎社区贡献，帮助改进智学导师系统：

1. Fork仓库并克隆到本地
2. 创建新分支：`git checkout -b feature/your-feature-name`
3. 提交更改：`git commit -m 'Add some feature'`
4. 推送到分支：`git push origin feature/your-feature-name`
5. 提交Pull Request

请确保代码符合项目的代码规范，并添加适当的测试。

## 📄 许可证

本项目采用MIT许可证。详情请参阅[LICENSE](LICENSE)文件。

## 📞 联系方式

- **电子邮件**：1303009157@qq.com
- **GitHub Issues**：[项目Issues页面](https://github.com/lct808846/EduMentor-DeepSeek.git)


 