from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DroneDoc',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='标题')),
                ('model_name', models.CharField(blank=True, max_length=100, verbose_name='适用机型')),
                ('category', models.CharField(choices=[('debug', '调试教程'), ('operation', '操作手册'), ('maintenance', '维护保养'), ('faq', '常见问题'), ('safety', '安全规范'), ('firmware', '固件升级'), ('parameter', '参数配置'), ('flight', '飞行技巧')], db_index=True, max_length=40, verbose_name='分类')),
                ('tags', models.CharField(blank=True, max_length=200, verbose_name='标签')),
                ('content', models.TextField(verbose_name='内容')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '无人机文档',
                'verbose_name_plural': '无人机文档',
                'ordering': ['-created_at'],
            },
        ),
    ]
