from .models import AuditLog

def log_action(*, user=None, action, model_name, object_id, changes=None, description='', request=None):
    """
    تسجيل عملية في سجل التدقيق.
    - user: المستخدم (اختياري)
    - action: من AuditLog.Action
    - model_name: اسم النموذج
    - object_id: معرف الكائن (كـ string)
    - changes: dict يحتوي على التغييرات (اختياري)
    - description: وصف إضافي
    - request: كائن request لاستخراج IP (اختياري)
    """
    ip = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        changes=changes or {},
        description=description,
        ip_address=ip,
    )
