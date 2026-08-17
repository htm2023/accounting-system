import uuid
from django.core.serializers.json import DjangoJSONEncoder

def generate_uuid():
    return uuid.uuid4()

def json_default(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    return DjangoJSONEncoder().default(obj)
