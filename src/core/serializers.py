from rest_framework import serializers

class HypermediaSerializer(serializers.Serializer):
    links = serializers.SerializerMethodField()

    def get_links(self, obj):
        return {}