# 基于DeepSeek的智能作业批改系统

这是一个基于DeepSeek AI技术的智能作业批改系统，具有题目解答和作业批改两大功能。系统使用Django框架开发，界面美观现代。

## 主要功能

1. **题目解答**：用户可以上传题目（图片或文字），系统将自动给出解答。
2. **作业批改**：用户可以上传作业图片，系统将自动批改并给出详细反馈和评分。

## 安装和配置

### 环境要求

- Python 3.8+
- Django 3.2+
- Pillow (用于图像处理)
- Requests (用于API调用)

### 安装步骤

1. 克隆或下载本项目

2. 安装依赖
   ```
   pip install -r requirements.txt
   ```

3. 复制环境变量示例文件并配置
   ```
   cp .env.example .env
   ```
   然后在`.env`文件中填入您的DeepSeek API密钥和其他配置信息。

4. 数据库迁移
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

5. 创建超级用户（可选，用于管理后台）
   ```
   python manage.py createsuperuser
   ```

6. 创建媒体文件存储目录
   ```
   mkdir -p media/problems media/homeworks
   ```

7. 运行开发服务器
   ```
   python manage.py runserver
   ```

8. 打开浏览器，访问 http://127.0.0.1:8000/ 即可使用系统。

## 使用指南

### 题目解答

1. 点击导航栏中的"题目解答"链接
2. 根据题目类型选择"文字题目"或"图片题目"标签
3. 对于文字题目，直接输入题目内容；对于图片题目，上传题目图片
4. 点击"获取解答"按钮，等待系统处理
5. 查看解答结果

### 作业批改

1. 点击导航栏中的"作业批改"链接
2. 上传需要批改的作业图片
3. 点击"批改作业"按钮，等待系统处理
4. 查看批改结果，包括具体评语和总分

## 技术实现

- 前端：HTML5, CSS3, JavaScript, Bootstrap 5, jQuery
- 后端：Django, Python
- AI引擎：DeepSeek API

## 注意事项

- 本系统需要有效的DeepSeek API密钥才能正常工作
- 上传的图片应当清晰、完整，以确保AI能够准确识别内容
- 批改结果仅供参考，复杂题目可能需要人工复核

 