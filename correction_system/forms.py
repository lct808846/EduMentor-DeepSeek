from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile, Problem, Homework, KnowledgeCard, LearningResource

class UserRegisterForm(UserCreationForm):
    """用户注册表单"""
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserLoginForm(AuthenticationForm):
    """用户登录表单"""
    class Meta:
        model = User
        fields = ['username', 'password']

class ProfileForm(forms.ModelForm):
    """用户资料编辑表单"""
    class Meta:
        model = UserProfile
        fields = ['avatar', 'school', 'grade', 'subjects_of_interest', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'subjects_of_interest': forms.TextInput(attrs={'placeholder': '例如：数学,物理,化学'}),
        }

class TextProblemForm(forms.ModelForm):
    """文本题目表单"""
    class Meta:
        model = Problem
        fields = ['text_content', 'solution']
        widgets = {
            'text_content': forms.Textarea(attrs={'rows': 5, 'placeholder': '请输入题目内容...'}),
            'solution': forms.Textarea(attrs={'rows': 8, 'placeholder': '请输入解答...'}),
        }

class ImageProblemForm(forms.ModelForm):
    """图片题目表单"""
    class Meta:
        model = Problem
        fields = ['image', 'text_content', 'solution']
        widgets = {
            'text_content': forms.Textarea(attrs={'rows': 3, 'placeholder': '可以添加题目的文字说明（可选）...'}),
            'solution': forms.Textarea(attrs={'rows': 8, 'placeholder': '请输入解答...'}),
        }

class ProblemSolveForm(forms.ModelForm):
    """通用题目解答表单"""
    problem_type = forms.ChoiceField(
        choices=Problem.PROBLEM_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='TEXT'
    )
    
    class Meta:
        model = Problem
        fields = ['problem_type', 'text_content', 'image', 'solution']
        widgets = {
            'text_content': forms.Textarea(attrs={'rows': 5, 'placeholder': '请输入题目内容...'}),
            'solution': forms.Textarea(attrs={'rows': 8, 'placeholder': '请输入解答...'}),
        }

class HomeworkForm(forms.ModelForm):
    """作业表单"""
    class Meta:
        model = Homework
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

class HomeworkCorrectForm(forms.ModelForm):
    """作业批改表单"""
    class Meta:
        model = Homework
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

class KnowledgeCardForm(forms.ModelForm):
    """知识卡片表单"""
    class Meta:
        model = KnowledgeCard
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': '例如：二次方程解法'}),
            'content': forms.Textarea(attrs={'rows': 10, 'placeholder': '请输入知识点内容，支持Markdown格式...'}),
        }
        
class LearningResourceForm(forms.ModelForm):
    """学习资源表单"""
    class Meta:
        model = LearningResource
        fields = [
            'title', 
            'description', 
            'content', 
            'resource_type', 
            'image', 
            'file_url', 
            'video_url', 
            'external_url',
            'tags', 
            'difficulty_level'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'content': forms.Textarea(attrs={'class': 'form-control rich-editor', 'rows': 10}),
            'resource_type': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '用逗号分隔多个标签，例如：数学,公式,高考'}),
            'difficulty_level': forms.Select(attrs={'class': 'form-control'}),
            'file_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': '输入文件下载链接'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': '输入视频链接'}),
            'external_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': '输入外部资源链接'}),
        }
        labels = {
            'title': '标题',
            'description': '描述',
            'content': '内容',
            'resource_type': '资源类型',
            'image': '封面图片',
            'file_url': '文件链接',
            'video_url': '视频链接',
            'external_url': '外部链接',
            'tags': '标签',
            'difficulty_level': '难度级别',
        }
        help_texts = {
            'tags': '多个标签请用逗号分隔',
            'content': '支持HTML格式',
        }

class ResourceSearchForm(forms.Form):
    """资源搜索表单"""
    keywords = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '搜索关键词'})
    )
    resource_types = forms.MultipleChoiceField(
        choices=LearningResource.RESOURCE_TYPES,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    difficulty = forms.ChoiceField(
        choices=[('', '所有难度'), ('beginner', '初级'), ('intermediate', '中级'), ('advanced', '高级')],
        required=False
    )

class ResourceReviewForm(forms.Form):
    """资源评价表单"""
    rating = forms.IntegerField(min_value=1, max_value=5)
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)