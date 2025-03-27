# 智能作业批改系统

## 项目简介

智能作业批改系统是一个基于人工智能的教育辅助平台，旨在帮助学生和教师提高学习效率和教学质量。系统利用先进的AI技术自动解答问题、批改作业，并生成个性化的知识卡片和学习资源推荐，为用户提供全方位的学习支持。

## 主要功能

### 智能解题

- **文本题目解答**：输入文字题目，AI自动分析并给出详细解答
- **图片题目解答**：上传题目图片，AI识别内容并提供解答
- **多学科支持**：支持数学、物理、化学、语文、英语等多个学科的题目

### 作业批改

- **自动评分**：上传作业图片，AI自动评分并给出详细反馈
- **优缺点分析**：指出作业中的优点和需要改进的地方
- **学习建议**：基于作业表现提供针对性的学习建议

### 知识管理

- **智能知识卡片**：自动从题目和作业中提取关键知识点，生成结构化知识卡片
- **个性化笔记**：用户可以创建、编辑和管理自己的知识卡片
- **知识关联**：将相关知识点连接，形成知识网络

### 学习资源

- **智能推荐**：基于用户的学习情况推荐相关学习资源
- **资源收藏**：收藏有用的学习资源，方便日后查阅
- **资源评价**：对学习资源进行评分和评价，帮助其他用户选择

### 学习记录

- **学习数据分析**：记录和分析用户的学习数据，展示学习进度和成果
- **问题历史**：查看和回顾已解答的问题
- **作业历史**：查看和回顾已批改的作业

## 技术架构

- **前端**：HTML, CSS, JavaScript, Bootstrap
- **后端**：Django, Python
- **AI引擎**：DeepSeek API
- **数据库**：SQLite/PostgreSQL
- **文件存储**：Django默认文件系统

## 使用指南

### 系统安装

1. 克隆代码库
```
git clone https://github.com/yourusername/correction_system.git
cd correction_system
```

2. 安装依赖
```
pip install -r requirements.txt
```

3. 数据库迁移
```
python manage.py migrate
```

4. 启动服务器
```
python manage.py runserver
```

5. 访问系统
在浏览器中访问 http://127.0.0.1:8000/ 开始使用系统

### 基本使用流程

1. **注册/登录**：创建账户或使用已有账户登录系统
2. **解题**：在"解题"页面输入文本题目或上传题目图片，获取AI解答
3. **批改作业**：在"批改作业"页面上传作业图片，获取AI批改结果
4. **知识卡片**：查看系统生成的知识卡片，或创建自己的知识卡片
5. **学习资源**：浏览和搜索学习资源，根据需要收藏和评价
6. **学习历史**：查看自己的学习历史记录，包括已解答的问题和已批改的作业

## 功能筛选说明

系统提供了多种筛选功能来帮助用户快速找到所需内容：

1. **问题筛选**：
   - 按问题类型（文本/图片）筛选
   - 按正确/错误状态筛选
   - 关键词搜索

2. **作业筛选**：
   - 按分数段筛选（优秀/良好/中等/及格/不及格）

3. **知识卡片筛选**：
   - 按标签筛选
   - 关键词搜索

4. **学习资源筛选**：
   - 按资源类型筛选
   - 按难度筛选
   - 关键词搜索

## 系统特色

1. **智能化**：利用先进AI技术实现智能解题和作业批改
2. **个性化**：根据用户学习情况提供个性化的知识卡片和资源推荐
3. **系统化**：将零散的知识点系统化整理，形成完整的知识体系
4. **可视化**：通过图表和统计数据直观展示学习进度和成果
5. **互动性**：用户可以评价和分享学习资源，促进交流与合作

## 常见问题

1. **为什么筛选功能不生效？**
   - 请尝试清除浏览器缓存或强制刷新页面(Ctrl+F5)
   - 确保选择了正确的筛选选项后点击了筛选按钮

2. **为什么知识卡片内容显示不正确？**
   - 系统使用Markdown格式显示内容，请确保内容格式正确
   - 如遇问题，可尝试编辑知识卡片重新保存

3. **系统支持哪些题目类型？**
   - 文字题目：直接输入题目文本
   - 图片题目：上传题目图片（支持jpg, png, jpeg格式）

## 联系方式

如有任何问题或建议，请通过以下方式联系我们：
- 邮箱：support@example.com
- 问题反馈：[GitHub Issues](https://github.com/yourusername/correction_system/issues)

## 开发团队

智学导师由Python和Django爱好者团队开发，旨在将AI技术应用于教育领域，提高学习效率。

## 许可证

本项目采用MIT许可证

 