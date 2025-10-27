from rest_framework import serializers

from .models import Part


class PartListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = ('id', 'name', 'price', 'quantity', 'description')

class PartDetailSerializer(PartListSerializer):
    class Meta(PartListSerializer.Meta):
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']



class PartImportSerializer(serializers.Serializer):

    file = serializers.FileField(
        help_text="Arquivo CSV contendo os dados das peças a serem importadas."
    )

    def validate_file(self, value):
        if not value.name.endswith(".csv"):
            raise serializers.ValidationError("O arquivo deve ter extensão .csv")
        return value
