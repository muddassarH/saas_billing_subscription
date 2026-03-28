from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import UserRole

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "password")

    def create(self, validated_data):
        return User.objects.create_user(role=UserRole.USER, **validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "role", "stripe_customer_id")
        read_only_fields = fields


class MeSerializer(serializers.ModelSerializer):
    plan_slug = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "role", "stripe_customer_id", "plan_slug", "subscription_status")
        read_only_fields = fields

    def get_plan_slug(self, obj):
        from billing.services import FeatureAccessService

        return FeatureAccessService.get_effective_plan(obj).slug

    def get_subscription_status(self, obj):
        from billing.models import Subscription

        sub = Subscription.objects.filter(user=obj).first()
        return sub.status if sub else None
