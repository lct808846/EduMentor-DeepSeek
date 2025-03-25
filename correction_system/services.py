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
            return "错误：pytesseract未正确安装，无法识别图片文字"
        
        try:
            # 打开图片
            img = Image.open(image_path)
            
            # 使用pytesseract识别图片文字（使用中文和英文）
            # 如果您在安装时选择了中文语言包，可以使用chi_sim(简体中文)或chi_tra(繁体中文)
            extracted_text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            
            if not extracted_text.strip():
                return "未能从图片中识别出文字，请确保图片清晰且包含文字内容"
                
            return extracted_text
        except Exception as e:
            return f"图片文字识别错误: {str(e)}"
    
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
        
        # 如果识别失败，返回错误信息
        if extracted_text.startswith("错误") or extracted_text.startswith("图片文字识别错误") or extracted_text.startswith("未能"):
            return {
                'correction_result': extracted_text,
                'score': 0,
                'feedback': extracted_text
            }
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 使用结构化提示词模板
        system_prompt = """你是一个专业的教师，负责批改学生作业。请按照以下固定结构提供批改结果：

## 作业内容概述
[简要描述学生作业的内容和题目]

## 批改详情
[按题目顺序提供详细批改意见]

## 错误分析
[指出学生的错误并分析原因]

## 正确解答
[提供每道题的正确答案和解题过程]

## 改进建议
[给出具体的学习建议]

## 总体评分
[给出一个总体评分（满分100分），并用粗体标记]

请确保每个部分都有内容，并严格按照此结构回答。"""
        
        payload = {
            "model": "deepseek-chat",  # 使用文本模型
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请批改以下学生作业内容：\n\n{extracted_text}"}
            ]
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # 获取批改内容
            correction_text = result.get('choices', [{}])[0].get('message', {}).get('content', '未能获取批改结果')
            
            # 从批改文本中提取分数（改进提取逻辑）
            score = 0
            for line in correction_text.split('\n'):
                if '总体评分' in line or '分' in line and any(char.isdigit() for char in line):
                    # 提取数字
                    digits = ''.join(c for c in line if c.isdigit() or c == '.')
                    try:
                        score = float(digits)
                        if score > 100:  # 确保分数不超过100
                            score = 100
                        break
                    except:
                        pass
            
            # 添加OCR识别文本到批改结果
            full_correction_result = f"""Tesseract OCR识别文本结果:
{extracted_text}

---批改结果开始---
{correction_text}"""
            
            return {
                'correction_result': full_correction_result,
                'score': score,
                'feedback': correction_text  # 简单起见，使用相同的文本作为反馈
            }
        except Exception as e:
            return {
                'correction_result': f"批改过程出错: {str(e)}",
                'score': 0,
                'feedback': f"批改过程出错: {str(e)}"
            } 