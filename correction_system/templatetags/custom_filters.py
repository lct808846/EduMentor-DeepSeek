from django import template
import re
import markdown
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def trim(text):
    """移除字符串前后的空白"""
    if text:
        return text.strip()
    return ""

@register.filter
def split_lines(text):
    """将文本分割成行"""
    if text:
        return text.splitlines()
    return []

@register.filter
def startswith(text, start):
    """检查文本是否以特定字符串开始"""
    if text and start:
        return text.startswith(start)
    return False

@register.filter
def matches(text, pattern):
    """检查文本是否匹配指定的正则表达式模式"""
    if text and pattern:
        return bool(re.match(pattern, text))
    return False

@register.filter
def get_number(line):
    """从列表项中提取编号"""
    if not line:
        return ""
    match = re.match(r'^(\d+\.\s*)', line)
    if match:
        return match.group(1)
    return ""

@register.filter
def strip_number(line):
    """移除列表项的编号"""
    if not line:
        return ""
    return re.sub(r'^\d+\.\s*', '', line)

@register.filter
def replace(text, args):
    """
    替换文本中的内容
    用法: {{ text|replace:"old,new" }}
    """
    if not text or not args:
        return text
    
    old, new = args.split(',', 1)
    return text.replace(old, new)

@register.filter
def extract_section(text, section_name):
    """
    从文本中提取指定的章节内容
    支持 # 章节名 和 ## 章节名 两种格式
    返回的内容是安全的HTML
    """
    if not text or not section_name:
        return ""
    
    # 尝试匹配 '# 章节名' 或 '## 章节名' 格式
    pattern1 = rf"(?:^|\n)#\s+{re.escape(section_name)}\s*?\n(.*?)(?:\n#\s+|$)"
    pattern2 = rf"(?:^|\n)##\s+{re.escape(section_name)}\s*?\n(.*?)(?:\n##\s+|$)"
    
    # 尝试所有可能的模式
    match = re.search(pattern1, text, re.DOTALL)
    if not match:
        match = re.search(pattern2, text, re.DOTALL)
    
    # 如果匹配成功，返回内容部分（去除前后空白）
    if match:
        content = match.group(1).strip()
        return mark_safe(markdown_to_html(content))
    
    # 备用方案：尝试更宽松的匹配（不依赖格式）
    alt_pattern = rf"(?:^|\n){re.escape(section_name)}[：:]\s*(.*?)(?:\n(?:[^a-zA-Z0-9\s])+\s*\w|$)"
    alt_match = re.search(alt_pattern, text, re.DOTALL)
    if alt_match:
        return mark_safe(markdown_to_html(alt_match.group(1).strip()))
    
    return ""

@register.filter
def detect_sections(text):
    """调试用：检测文本中的所有章节标题"""
    if not text:
        return []
    
    # 匹配 # 标题 或 ## 标题 格式
    sections = re.findall(r'(?:^|\n)(#|##)\s+(.*?)\s*(?:\n|$)', text)
    return [s[1] for s in sections]

@register.filter
def markdown_to_html(text):
    """
    将Markdown格式的文本转换为HTML
    返回标记为安全的HTML字符串
    """
    if not text:
        return ""
    
    # 创建Markdown转换器，启用扩展
    md = markdown.Markdown(
        extensions=['extra', 'nl2br', 'sane_lists', 'tables'],
        output_format='html5'
    )
    
    # 自定义处理常见Markdown样式
    
    # 处理数学公式 (使用 $ 包裹的内容)
    text = re.sub(r'\$([^$]+)\$', r'<span class="math">\1</span>', text)
    
    # 生成HTML
    html = md.convert(text)
    
    # 特殊后处理 - 添加类和样式
    
    # 处理有序列表项，添加蓝色编号
    html = re.sub(
        r'<li>(\d+\.\s*)(.*?)</li>', 
        r'<li class="solution-list-item"><span class="solution-list-number">\1</span><span class="solution-list-content">\2</span></li>',
        html
    )
    
    # 返回标记为安全的HTML
    return mark_safe(html)

@register.filter
def split_by_newline(text):
    """将文本按换行符分割成列表"""
    if not text:
        return []
    
    return [line.strip() for line in text.split('\n') if line.strip()] 