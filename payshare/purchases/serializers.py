from django.contrib.auth.models import User
from moneyed import Money
from rest_framework import serializers

from payshare.purchases.models import Collective
from payshare.purchases.models import Liquidation
from payshare.purchases.models import Purchase
from payshare.purchases.models import Reaction


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "avatar",
            "first_name",
            "full_name",
            "id",
            "last_name",
            "username",
        )

    def get_avatar(self, user):
        return user.profile.avatar_image_url

    def get_full_name(self, user):
        return user.get_full_name()


class CollectiveSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True)

    class Meta:
        model = Collective
        fields = (
            "created_at",
            "currency_symbol",
            "id",
            "key",
            "members",
            "name",
            "readonly",
            "stats",
            "token",
        )


class MoneyField(serializers.Field):
    """https://github.com/django-money/django-money/issues/179"""

    def to_representation(self, obj):
        return {
            "amount": "%f" % (obj.amount),
            "currency": "%s" % (obj.currency),
        }

    def to_internal_value(self, data):
        return Money(data["amount"], data["currency"])


class ReactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reaction
        fields = (
            "created_at",
            "id",
            "meaning",
            "member",
        )


def _get_sorted_serialzed_reactions_for_transfer(transfer):
    reactions = transfer.reactions.order_by("created_at")
    return ReactionSerializer(reactions, many=True).data


class LiquidationSerializer(serializers.ModelSerializer):
    amount = MoneyField()
    reactions = serializers.SerializerMethodField()

    class Meta:
        model = Liquidation
        fields = (
            "amount",
            "created_at",
            "creditor",
            "debtor",
            "id",
            "kind",
            "modified_at",
            "name",
            "reactions",
        )

    def get_reactions(self, liquidation):
        return _get_sorted_serialzed_reactions_for_transfer(liquidation)


class PurchaseSerializer(serializers.ModelSerializer):
    price = MoneyField()
    reactions = serializers.SerializerMethodField()

    class Meta:
        model = Purchase
        fields = (
            "buyer",
            "created_at",
            "id",
            "kind",
            "modified_at",
            "name",
            "price",
            "reactions",
        )

    def get_reactions(self, purchase):
        return _get_sorted_serialzed_reactions_for_transfer(purchase)


class TransferSerializer(serializers.Serializer):
    """Accept both Purchase and Liquidation and delegate."""

    def to_representation(self, instance):
        if instance.__class__ == Purchase:
            return PurchaseSerializer(instance).data
        elif instance.__class__ == Liquidation:
            return LiquidationSerializer(instance).data
        raise ValueError("Cannot serialize this thing: {}".format(instance))
