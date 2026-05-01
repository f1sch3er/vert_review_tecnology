from rest_framework_simplejwt import serializers


class HypermediaSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()

    class Meta:
        abstract = True

    def get_links(self, obj):
        return {}