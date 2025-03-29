from django.contrib import admin

# Register your models here.

from .models import LearningResource, ResourceRating

class ResourceRatingInline(admin.TabularInline):
    model = ResourceRating
    extra = 0
    readonly_fields = ['user', 'score', 'comment', 'created_at']
    can_delete = False

@admin.register(LearningResource)
class LearningResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'resource_type', 'difficulty_level', 'view_count', 'get_avg_rating', 'created_at']
    list_filter = ['resource_type', 'difficulty_level', 'created_at']
    search_fields = ['title', 'description', 'tags']
    readonly_fields = ['view_count', 'saved_by', 'created_at', 'updated_at']
    filter_horizontal = ['saved_by']
    fieldsets = [
        ('基本信息', {'fields': ['title', 'description', 'content', 'resource_type', 'difficulty_level', 'tags']}),
        ('媒体和链接', {'fields': ['image', 'file_url', 'video_url', 'external_url']}),
        ('统计信息', {'fields': ['view_count', 'saved_by', 'created_at', 'updated_at']}),
    ]
    inlines = [ResourceRatingInline]
    
    def get_avg_rating(self, obj):
        from django.db.models import Avg
        avg = obj.ratings.aggregate(Avg('score'))['score__avg']
        if avg:
            return round(avg, 1)
        return '暂无评分'
    get_avg_rating.short_description = '平均评分'

@admin.register(ResourceRating)
class ResourceRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource', 'score', 'created_at']
    list_filter = ['score', 'created_at']
    search_fields = ['user__username', 'resource__title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
