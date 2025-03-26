# 智学导师

基于Django和DeepSeek API开发的智能作业批改与问题解答系统，帮助学生解决学习问题并提供详细的解题思路。

## 系统简介

智学导师是一个专为学生和教师设计的AI辅助教育平台。利用OCR技术和大语言模型，系统可以：
- 自动解答文字或图片形式的学科问题
- 智能批改学生作业，提供详细的评析和改进建议
- 为学习过程提供结构化的答案和解题思路

## 主要功能

### 1. 题目解答
- **文字题目**：直接输入题目文本，获取详细解答
- **图片题目**：上传题目图片，系统自动识别文字并解答
- **结构化解答**：所有解答都按照固定结构呈现，包括题目理解、解题思路、解题过程、最终答案和知识点总结

### 2. 作业批改
- **作业评改**：上传作业图片，获取专业批改意见
- **错误分析**：详细指出作业中的错误并分析原因
- **改进建议**：提供针对性的学习建议
- **评分系统**：给出客观评分（满分100分）

## 技术架构

- **前端**：Bootstrap 5、jQuery、HTML/CSS/JavaScript
- **后端**：Django框架
- **OCR技术**：Tesseract OCR（识别图片中的文字）
- **AI引擎**：DeepSeek API（智能解答和批改）
- **数据存储**：SQLite数据库（问题和批改历史）

## 安装步骤

### 1. 环境准备
- Python 3.8或更高版本
- Tesseract OCR引擎

### 2. 克隆代码库并安装依赖
```bash
git clone [repository-url]
cd [project-folder]
pip install -r requirements.txt
```

### 3. 安装Tesseract OCR
- **Windows**：
  - 从[Tesseract-OCR下载页面](https://github.com/UB-Mannheim/tesseract/wiki)下载安装包
  - 安装时选择中文语言包（Chinese simplified）
  - 确保安装路径添加到系统PATH

- **macOS**：
  ```bash
  brew install tesseract
  brew install tesseract-lang  # 安装语言包
  ```

- **Linux**：
  ```bash
  sudo apt install tesseract-ocr
  sudo apt install tesseract-ocr-chi-sim  # 安装中文语言包
  ```

### 4. 配置环境变量
创建`.env`文件，添加以下内容：
```
DEEPSEEK_API_KEY=your_api_key_here
```

### 5. 数据库迁移
```bash
python manage.py migrate
```

### 6. 启动服务器
```bash
python manage.py runserver
```

## 配置说明

### DeepSeek API配置
- 在[DeepSeek官网](https://www.deepseek.com)注册并获取API密钥
- 将API密钥配置在`.env`文件或环境变量中

### Tesseract OCR配置
如果系统无法自动找到Tesseract，可以在`correction_system/services.py`中手动设置路径：
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows示例
```

## 使用指南

1. 访问 http://127.0.0.1:8000/ 打开系统主页
2. 选择"题目解答"或"作业批改"功能
3. 根据提示上传图片或输入文字
4. 等待系统处理并查看结果
5. 可以复制、打印或保存结果

## 注意事项

- **图片质量**：清晰的图片能提高OCR识别准确率
- **中文识别**：确保Tesseract安装了中文语言包
- **API限制**：DeepSeek API可能有请求频率限制，请合理使用
- **敏感信息**：避免上传含有个人敏感信息的内容

## 常见问题

### OCR无法识别中文
- 确认已安装中文语言包
- 检查Tesseract安装路径是否正确
- 尝试使用更清晰的图片

### API错误
- 验证API密钥是否正确
- 检查网络连接
- 确认API账户余额是否充足

## 开发团队

智学导师由Python和Django爱好者团队开发，旨在将AI技术应用于教育领域，提高学习效率。

## 许可证

本项目采用MIT许可证

 