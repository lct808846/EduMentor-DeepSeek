import os
import json
import base64
import requests
from PIL import Image
import io
import tempfile

# 替换PaddleOCR相关导入
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    print("警告: pytesseract未安装，图片识别功能将不可用。请安装: pip install pytesseract")
    TESSERACT_AVAILABLE = False

class DeepSeekService:
    """与DeepSeek API交互的服务"""
    
    def __init__(self, api_key=None):
        # 从环境变量获取API密钥，或使用传入的密钥
        self.api_key = api_key or os.environ.get('DEEPSEEK_API_KEY')
        self.api_url = "https://api.deepseek.com/v1/chat/completions"  # 假设的API端点
        
        if not self.api_key:
            print("警告: 未配置DeepSeek API密钥，请在设置中配置或作为环境变量传入")
        
        # 设置Tesseract OCR路径
        if TESSERACT_AVAILABLE:
            try:
                # 根据实际安装路径修改
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                print("Tesseract OCR初始化成功")
            except Exception as e:
                print(f"Tesseract OCR初始化失败: {str(e)}")
    
    def encode_image(self, image_path):
        """将图片编码为base64字符串"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
            
    def pil_to_base64(self, pil_image):
        """将PIL图像对象转换为base64字符串"""
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def extract_text_from_image(self, image_path):
        """使用Tesseract OCR从图片中提取文字"""
        if not TESSERACT_AVAILABLE:
            print("错误：pytesseract未正确安装，无法识别图片文字")
            return "错误：pytesseract未正确安装，无法识别图片文字"
        
        try:
            # 打开图片
            img = Image.open(image_path)
            
            # 使用pytesseract识别图片文字（使用中文和英文）
            # 如果您在安装时选择了中文语言包，可以使用chi_sim(简体中文)或chi_tra(繁体中文)
            extracted_text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            
            if not extracted_text or not extracted_text.strip():
                print("警告：OCR未能提取到任何文本内容")
                # 返回默认文本，确保文本字段不为空
                return "OCR未能识别出文字，可能是图片清晰度不够或者不包含文本内容。"
                
            # 打印识别到的文字（用于调试）
            print(f"OCR识别结果：{extracted_text[:100]}...")
            return extracted_text
        except Exception as e:
            error_msg = f"图片文字识别错误: {str(e)}"
            print(error_msg)
            return error_msg
    
    def solve_text_problem(self, problem_text):
        """解答文字题目"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 使用结构化提示词模板
        system_prompt = """你是一个专业的学科老师，擅长解答各类学科问题并提供详细的解答过程。
请按照以下固定结构提供答案：

## 题目理解
[简要描述题目要求和关键信息]

## 解题思路
[详细说明解题的思路和方法]

## 解题过程
[分步骤展示解题过程，每一步都要清晰标注]

## 最终答案
[给出最终答案，用粗体标记]

## 知识点总结
[总结本题涉及的知识点和解题技巧]

请确保每个部分都有内容，并严格按照此结构回答。"""

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请解答以下题目：\n\n{problem_text}"}
            ]
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get('choices', [{}])[0].get('message', {}).get('content', '未能获取解答')
        except Exception as e:
            return f"解答过程出错: {str(e)}"
    
    def solve_image_problem(self, image_path):
        """解答图片题目（使用OCR识别后再处理）"""
        # 第一步：使用Tesseract OCR识别图片中的文字
        extracted_text = self.extract_text_from_image(image_path)
        
        # 如果识别失败，返回错误信息
        if extracted_text.startswith("错误") or extracted_text.startswith("图片文字识别错误") or extracted_text.startswith("未能"):
            return extracted_text
            
        # 第二步：将提取的文字发送给DeepSeek API处理
        # 使用solve_text_problem方法处理提取的文字
        answer = self.solve_text_problem(extracted_text)
        
        # 返回OCR识别文本和解答结果
        return f"""Tesseract OCR识别文本结果:
{extracted_text}

---解答开始---
{answer}"""
    
    def correct_homework(self, image_path):
        """批改作业（使用OCR识别后再处理）"""
        # 先使用Tesseract OCR识别图片中的文字
        extracted_text = self.extract_text_from_image(image_path)
        print(f"OCR识别结果: {extracted_text[:100]}...")
        
        # 确保text_content不为空，即使OCR识别失败
        if not extracted_text or not extracted_text.strip():
            extracted_text = "OCR未能识别出文字，请确保图片清晰且包含文字内容。"
        
        # 如果识别失败，返回错误信息
        if extracted_text.startswith("错误") or extracted_text.startswith("图片文字识别错误"):
            return {
                'correction_result': "无法识别作业内容，请上传更清晰的图片。",
                'score': 0,
                'feedback': extracted_text,
                'is_correct': False,
                'text_content': extracted_text,  # 确保text_content有值
                'problem_type': '未知',
                'answer': '',
                'correct_answer': '',
                'strengths': ["提交作业，积极参与学习"],
                'weaknesses': ["提供的图片内容无法识别，请重新上传更清晰的图片"]
            }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 简化提示词，确保模型能生成有用的回复
        system_prompt = """你是一位专业教师，请批改学生的作业内容(书写规范不规范不扣分，错误原因不分析题目的原因，选择题选对就100分)。分析学生作业，给出以下信息：
1. 分数评价（0-100分）
2. 题目类型（选择题/填空题/计算题等）
3. 学生的答案是什么
4. 正确答案是什么
5. 学生的答案是否正确
6. 如果错误，分析错误原因
7. 详细解题过程
8. 学生做得好的方面
9. 学生需要改进的地方

请直接回复，不需要格式化为JSON。"""

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请批改以下学生作业内容：\n\n{extracted_text}"}
            ]
        }
        
        try:
            print("调用DeepSeek API...")
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # 获取批改内容
            correction_text = result.get('choices', [{}])[0].get('message', {}).get('content', '未能获取批改结果')
            print(f"API返回内容: {correction_text[:100]}...")
            
            # 提取评分
            import re
            
            # 尝试提取分数
            score_patterns = [
                r'分[数|值][:：]?\s*(\d+)',
                r'评分[:：]?\s*(\d+)',
                r'得分[:：]?\s*(\d+)',
                r'[\(（](\d+)分[\)）]',
                r'(\d+)\s*[/／]\s*100',
                r'(\d+)\s*分'
            ]
            
            score = 0
            for pattern in score_patterns:
                score_matches = re.findall(pattern, correction_text)
                if score_matches:
                    try:
                        score = int(score_matches[0])
                        if 0 <= score <= 100:  # 确保分数在合理范围内
                            break
                    except:
                        continue
            
            # 判断是否正确
            correct_indicators = ['正确', '对的', '答对了', '完全正确', '答案正确']
            incorrect_indicators = ['错误', '不正确', '不对', '答错了', '有误']
            
            is_correct = False
            
            # 检查是否包含正确指示词
            if any(indicator in correction_text for indicator in correct_indicators):
                # 再检查是否同时包含否定词
                if not any(neg in correction_text for neg in ['不', '没有']):
                    is_correct = True
            
            # 如果包含错误指示词，则确认为错误
            if any(indicator in correction_text for indicator in incorrect_indicators):
                is_correct = False
            
            # 题目类型识别
            problem_type = '未知'
            type_patterns = [
                r'题[目]?类型[:：]?\s*([^，。\n]+)',
                r'这[是]?[一]?道([^，。\n]+)题'
            ]
            
            for pattern in type_patterns:
                type_matches = re.search(pattern, correction_text)
                if type_matches:
                    problem_type = type_matches.group(1).strip()
                    break
            
            # 常见题型关键词检测
            if problem_type == '未知':
                type_keywords = {
                    '选择题': ['选择题', '单选题', '多选题', 'ABCD', '选项'],
                    '填空题': ['填空题', '填写'],
                    '计算题': ['计算题', '计算', '算式'],
                    '解答题': ['解答题', '证明题'],
                    '判断题': ['判断题', '判断正误']
                }
                
                for type_name, keywords in type_keywords.items():
                    if any(keyword in correction_text for keyword in keywords):
                        problem_type = type_name
                        break
            
            # 提取学生答案
            student_answer = ''
            answer_patterns = [
                r'学生[的]?答案[:：]?\s*([^，。\n]+)',
                r'学生[的]?回答[:：]?\s*([^，。\n]+)',
                r'学生选择了\s*([^，。\n]+)'
            ]
            
            for pattern in answer_patterns:
                answer_matches = re.search(pattern, correction_text)
                if answer_matches:
                    student_answer = answer_matches.group(1).strip()
                    break
            
            # 提取正确答案
            correct_answer = ''
            correct_patterns = [
                r'正确答案[:：]?\s*([^，。\n]+)',
                r'正确[的]?答案应该是\s*([^，。\n]+)',
                r'答案应该是\s*([^，。\n]+)'
            ]
            
            for pattern in correct_patterns:
                correct_matches = re.search(pattern, correction_text)
                if correct_matches:
                    correct_answer = correct_matches.group(1).strip()
                    break
            
            # 如果是选择题，尝试直接从文本中提取选项字母
            if '选择题' in problem_type:
                # 针对选择题的特殊处理
                letter_match = re.search(r'[正确]?答案[是为应该]?[：:]?\s*([A-D])', correction_text)
                if letter_match:
                    correct_answer = letter_match.group(1).strip()
                
                student_letter_match = re.search(r'学生[选择回答]了\s*([A-D])', correction_text)
                if student_letter_match:
                    student_answer = student_letter_match.group(1).strip()
            
            # 提取错误分析
            error_analysis = ''
            if not is_correct:
                error_patterns = [
                    r'错误分析[:：]?\s*([\s\S]+?)(?=\n\n|\n[A-Z]|$)',
                    r'错误原因[:：]?\s*([\s\S]+?)(?=\n\n|\n[A-Z]|$)',
                    r'错误在于[:：]?\s*([\s\S]+?)(?=\n\n|\n[A-Z]|$)'
                ]
                
                for pattern in error_patterns:
                    error_matches = re.search(pattern, correction_text)
                    if error_matches:
                        error_analysis = error_matches.group(1).strip()
                        break
                
                # 如果没找到特定的错误分析部分，使用整个批改内容
                if not error_analysis:
                    error_analysis = "答案有误，请参考详细解析。"
            
            # 提取学生优点
            strengths = []
            # 多种可能的标题格式
            strength_sections = re.findall(r'(?:优点|做得好的[地方方面]|值得肯定的[地方方面]|表现良好的[地方方面])[:：]?\s*([\s\S]+?)(?=\n\n|需要改进|改进之处|不足之处|$)', correction_text)
            
            if strength_sections:
                # 取第一个匹配的部分
                section = strength_sections[0].strip()
                # 按行或按数字序号拆分
                if '\n' in section:
                    # 多行情况
                    lines = [line.strip() for line in section.split('\n') if line.strip()]
                    for line in lines:
                        # 去除数字前缀
                        clean_line = re.sub(r'^\d+[.、]\s*', '', line).strip()
                        if clean_line:
                            strengths.append(clean_line)
                else:
                    # 单行情况
                    strengths.append(section)
            
            # 如果未找到优点，添加一个通用优点
            if not strengths and is_correct:
                strengths.append("答案正确，思路清晰。")
            elif not strengths:
                strengths.append("尝试解答问题，积极参与学习。")
            
            # 提取需要改进的地方
            weaknesses = []
            weakness_sections = re.findall(r'(?:需要改进|改进之处|不足之处|缺点|有待提高的[地方方面])[:：]?\s*([\s\S]+?)(?=\n\n|优点|做得好|$)', correction_text)
            
            if weakness_sections:
                section = weakness_sections[0].strip()
                if '\n' in section:
                    lines = [line.strip() for line in section.split('\n') if line.strip()]
                    for line in lines:
                        clean_line = re.sub(r'^\d+[.、]\s*', '', line).strip()
                        if clean_line:
                            weaknesses.append(clean_line)
                else:
                    weaknesses.append(section)
            
            # 如果找不到改进点，但答案错误，添加通用改进建议
            if not weaknesses and not is_correct:
                weaknesses.append("需要仔细审题，理解题目要求。")
                weaknesses.append("建议复习相关知识点，加强练习。")
            
            # 返回完整结果
            return {
                'text_content': extracted_text,
                'correction_result': correction_text,  # 保存完整批改内容
                'score': score,
                'is_correct': is_correct,
                'problem_type': problem_type,
                'answer': student_answer,
                'correct_answer': correct_answer,
                'error_analysis': error_analysis,
                'strengths': strengths,
                'weaknesses': weaknesses,
                'feedback': correction_text  # 保持兼容性
            }
            
        except Exception as e:
            print(f"批改过程出错: {str(e)}")
            # 出错时返回基本信息
            return {
                'text_content': extracted_text,
                'correction_result': f"批改过程遇到错误: {str(e)}",
                'score': 0,
                'is_correct': False,
                'problem_type': '未知',
                'answer': '',
                'correct_answer': '',
                'error_analysis': f"系统错误: {str(e)}",
                'strengths': ["提交作业，积极参与学习"],
                'weaknesses': ["系统暂时无法给出具体改进建议"],
                'feedback': f"批改过程出错: {str(e)}"
            }

class KnowledgeExtractor:
    """从解答结果中提取知识点"""
    
    @staticmethod
    def extract_knowledge_points(solution_text):
        """提取知识点"""
        knowledge_points = []
        
        # 尝试找到"知识点总结"部分
        if "知识点总结" in solution_text:
            try:
                # 提取知识点总结部分
                knowledge_summary_section = solution_text.split("知识点总结")[1].strip()
                
                # 如果有下一个大标题，截取到下一个大标题前
                if "##" in knowledge_summary_section:
                    knowledge_summary_section = knowledge_summary_section.split("##")[0].strip()
                
                # 按行分割，去除空行
                lines = [line.strip() for line in knowledge_summary_section.split('\n') if line.strip()]
                
                # 如果以列表形式呈现（- 或* 开头）
                if any(line.startswith(('-', '*')) for line in lines):
                    for line in lines:
                        if line.startswith(('-', '*')):
                            # 去除前导符号并清理
                            point = line.lstrip('-* ').strip()
                            if point:
                                knowledge_points.append(point)
                else:
                    # 整段作为一个知识点
                    knowledge_points.append(knowledge_summary_section)
            except Exception as e:
                print(f"提取知识点时出错: {str(e)}")
                # 如果出错，返回空列表
                pass
        
        return knowledge_points
    
    @staticmethod
    def generate_knowledge_cards(problem, solution_text):
        """生成知识卡片"""
        from .models import KnowledgeCard
        
        knowledge_points = KnowledgeExtractor.extract_knowledge_points(solution_text)
        created_cards = []
        
        for point in knowledge_points:
            # 为每个知识点创建一个卡片
            title = point[:100] if len(point) > 100 else point
            content = point
            
            # 如果知识点过短，可能不是完整的知识点，跳过
            if len(content) < 10:
                continue
                
            try:
                card = KnowledgeCard(
                    user=problem.user,
                    title=title,
                    content=content,
                    problem=problem
                )
                card.save()
                created_cards.append(card)
            except Exception as e:
                print(f"创建知识卡片时出错: {str(e)}")
        
        return created_cards

class ResourceRecommender:
    """学习资源推荐系统"""
    
    @staticmethod
    def extract_keywords(text, max_keywords=5):
        """从文本中提取关键词"""
        # 简单实现：按词频提取
        # 实际应用中可使用更复杂的NLP算法如TF-IDF或关键词提取模型
        import re
        from collections import Counter
        
        # 移除标点和特殊字符
        text = re.sub(r'[^\w\s]', '', text)
        
        # 分词并统计频率（简单实现）
        words = text.split()
        word_counts = Counter(words)
        
        # 过滤掉停用词（简单实现）
        stop_words = ['的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都']
        for word in stop_words:
            if word in word_counts:
                del word_counts[word]
        
        # 返回频率最高的几个词
        return [word for word, _ in word_counts.most_common(max_keywords)]
    
    @staticmethod
    def recommend_resources(problem, max_recommendations=3):
        """根据问题推荐学习资源"""
        from .models import LearningResource, ResourceRecommendation
        
        # 组合题目内容和解答结果
        text = ''
        if problem.text_content:
            text += problem.text_content + ' '
        if problem.solution:
            text += problem.solution
        
        # 提取关键词
        keywords = ResourceRecommender.extract_keywords(text)
        
        # 根据关键词查找相关资源
        recommendations = []
        for keyword in keywords:
            # 在标题和描述中搜索关键词
            resources = LearningResource.objects.filter(
                models.Q(title__icontains=keyword) | 
                models.Q(description__icontains=keyword)
            ).distinct()
            
            for resource in resources:
                # 创建推荐记录
                recommendation, created = ResourceRecommendation.objects.get_or_create(
                    user=problem.user,
                    problem=problem,
                    resource=resource,
                    defaults={'relevance_score': 0.5}  # 默认相关性分数
                )
                
                # 如果已存在，提高相关性分数
                if not created:
                    recommendation.relevance_score += 0.1
                    recommendation.save()
                
                recommendations.append(recommendation)
        
        # 按相关性分数排序并返回前几个
        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
        return recommendations[:max_recommendations] 