from rest_framework import serializers
from .models import CorpusEntry

class CorpusEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CorpusEntry
        fields = '__all__'
