from django.db import models

class DroneDoc(models.Model):
    CATEGORY_CHOICES = [
        ('debug', '调试教程'),
        ('operation', '操作手册'),
        ('maintenance', '维护保养'),
        ('faq', '常见问题'),
        ('safety', '安全规范'),
        ('firmware', '固件升级'),
        ('parameter', '参数配置'),
        ('flight', '飞行技巧'),
    ]

    title = models.CharField('标题', max_length=200)
    model_name = models.CharField('适用机型', max_length=100, blank=True)
    category = models.CharField('分类', max_length=40, choices=CATEGORY_CHOICES, db_index=True)
    tags = models.CharField('标签', max_length=200, blank=True)
    content = models.TextField('内容')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '无人机文档'
        verbose_name_plural = '无人机文档'

    def __str__(self):
        return self.title

    def to_rag_text(self):
        parts = [f'标题：{self.title}']
        if self.model_name:
            parts.append(f'适用机型：{self.model_name}')
        parts.append(f'分类：{self.get_category_display()}')
        if self.tags:
            parts.append(f'标签：{self.tags}')
        parts.append(f'内容：{self.content}')
        return '\n'.join(parts)
