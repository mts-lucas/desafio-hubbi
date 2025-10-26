from rest_framework import serializers

from .models import Part


class PartListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = ('id', 'name', 'price', 'quantity', 'description')
        read_only_fields = ('id')

class PartDetailSerializer(PartListSerializer):
    class Meta(PartListSerializer.Meta):
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')