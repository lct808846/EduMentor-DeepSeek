from django import forms
from .models import Problem, Homework

class TextProblemForm(forms.Form):
    """文字题目表单"""
    text_content = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        label='输入题目内容',
        required=True
    )

class ImageProblemForm(forms.Form):
    """图片题目表单"""
    image = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label='上传题目图片',
        required=True
    )

class HomeworkForm(forms.Form):
    """作业表单"""
    image = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label='上传作业图片',
        required=True
    ) 