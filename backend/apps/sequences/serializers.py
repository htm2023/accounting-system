from rest_framework import serializers
from .models import DocumentSequence

class DocumentSequenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentSequence
        fields = ['id', 'document_type', 'prefix', 'current_number', 'fiscal_year']
        read_only_fields = ['id']
