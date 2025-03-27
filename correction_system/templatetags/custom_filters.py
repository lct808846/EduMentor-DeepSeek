from django import template
import re

register = template.Library()

@register.filter
def trim(value):
    """删除字符串前后的空白字符"""
    return value.strip()

@register.filter
def split_lines(value):
    """将文本拆分为行列表"""
    if not value:
        return []
    return value.split('\n')

@register.filter
def startswith(value, arg):
    """检查字符串是否以指定文本开头"""
    return value.startswith(arg)

@register.filter
def matches(value, pattern):
    """检查字符串是否匹配指定的正则表达式模式"""
    return bool(re.match(pattern, value))

@register.filter
def get_number(value):
    """从列表项中提取数字"""
    match = re.match(r'(\d+)\.\s', value)
    if match:
        return match.group(1)
    return ""

@register.filter
def strip_number(value):
    """从列表项中移除序号部分"""
    return re.sub(r'^\d+\.\s', '', value)

@register.filter
def replace(value, arg):
    """替换字符串中的指定内容"""
    if value is None:
        return ""
    parts = arg.split(":")
    if len(parts) != 2:
        return value
    return value.replace(parts[0], parts[1])

@register.filter
def extract_section(value, section_name):
    """从文本中提取指定章节的内容"""
    if not value or not section_name:
        return ""
    
    # 尝试匹配'## 题目理解'和'# 题目理解'两种格式
    pattern1 = r'## ' + re.escape(section_name) + r'.*?(?=## |# |$)'
    pattern2 = r'# ' + re.escape(section_name) + r'.*?(?=## |# |$)'
    
    # 先尝试匹配'##'格式
    match = re.search(pattern1, value, re.DOTALL)
    if match:
        section_content = match.group(0)
        # 移除章节标题
        section_content = re.sub(r'^## ' + re.escape(section_name) + r'.*?\n', '', section_content)
        return section_content.strip()
    
    # 再尝试匹配'#'格式
    match = re.search(pattern2, value, re.DOTALL)
    if match:
        section_content = match.group(0)
        # 移除章节标题
        section_content = re.sub(r'^# ' + re.escape(section_name) + r'.*?\n', '', section_content)
        return section_content.strip()
    
    # 尝试匹配带"解题过程"的任何格式（更宽松的匹配）
    pattern3 = r'[#]+ .*?' + re.escape(section_name) + r'.*?(?=[#]+ |$)'
    match = re.search(pattern3, value, re.DOTALL)
    if match:
        section_content = match.group(0)
        # 移除章节标题（匹配任何数量的#）
        section_content = re.sub(r'^[#]+ .*?' + re.escape(section_name) + r'.*?\n', '', section_content)
        return section_content.strip()
    
    return ""

@register.filter
def detect_sections(value):
    """检测文本中的所有章节标题，用于调试"""
    if not value:
        return ""
    
    # 匹配所有章节标题
    sections = re.findall(r'(^|\n)[#]+ (.*?)($|\n)', value, re.MULTILINE)
    result = []
    for section in sections:
        if len(section) >= 2:
            result.append(section[1].strip())
    
    return ", ".join(result) if result else "未找到章节"

@register.filter
def markdown_to_html(value):
    """将简单的Markdown格式转换为HTML"""
    if not value:
        return ""
        
    # 处理标题（确保标题前有换行符，避免匹配中间的#）
    value = re.sub(r'(^|\n)# (.*?)($|\n)', r'\1<h3 class="fw-bold mt-3 mb-2">\2</h3>\3', value)
    value = re.sub(r'(^|\n)## (.*?)($|\n)', r'\1<h4 class="fw-bold mt-2 mb-1">\2</h4>\3', value)
    value = re.sub(r'(^|\n)### (.*?)($|\n)', r'\1<h5 class="fw-bold mt-2 mb-1">\2</h5>\3', value)
    
    # 处理数字列表（例如：1. **标题**：内容）
    value = re.sub(r'(^|\n)(\d+)\. \*\*(.*?)\*\*：(.*?)($|\n)', 
                  r'\1<div class="list-item"><span class="list-number">\2.</span> <strong class="list-title">\3：</strong><span class="list-content">\4</span></div>\5', 
                  value)
    
    # 处理数字列表（无冒号版本）
    value = re.sub(r'(^|\n)(\d+)\. \*\*(.*?)\*\*(.*?)($|\n)', 
                  r'\1<div class="list-item"><span class="list-number">\2.</span> <strong class="list-title">\3</strong><span class="list-content">\4</span></div>\5', 
                  value)
    
    # 处理普通数字列表
    value = re.sub(r'(^|\n)(\d+)\. (.*?)($|\n)', 
                  r'\1<div class="list-item"><span class="list-number">\2.</span> <span class="list-content">\3</span></div>\4', 
                  value)
    
    # 处理强调（粗体）
    value = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', value)
    
    # 处理强调（斜体）
    value = re.sub(r'\*(.*?)\*', r'<em>\1</em>', value)
    
    # 处理无序列表
    value = re.sub(r'(^|\n)- (.*?)($|\n)', r'\1<div class="list-item"><span class="list-bullet">•</span> <span class="list-content">\2</span></div>\3', value)
    
    # 处理分隔线
    value = re.sub(r'(^|\n)---+($|\n)', r'\1<hr>\2', value)
    
    # 将换行符转换为HTML换行
    value = value.replace('\n', '<br>')
    
    return value 