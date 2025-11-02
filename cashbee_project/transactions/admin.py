from django.contrib import admin

from users.models import User
from wallet.models import Wallet
from .models import CollectionRequest, Transaction
from .services import CollectMoney, TransactionOperation
from django import forms
from django.forms import ValidationError


class TransactionAdminForm(forms.ModelForm):
    sender_user = forms.ModelChoiceField(queryset=User.objects.all(), label="Sender User")
    receiver_phone = forms.CharField(label="Receiver Phone")

    class Meta:
        model = Transaction
        fields = ['sender_user', 'receiver_phone', 'transaction_type', 'amount', 'status']

    def clean(self):
        cleaned_data = super().clean()
        sender = cleaned_data.get('sender_user')
        receiver_phone = cleaned_data.get('receiver_phone')
        amount = cleaned_data.get('amount')

        if amount <= 0:
            raise forms.ValidationError("❌ Amount must be positive.")

        if sender.phone_number == receiver_phone:
            raise forms.ValidationError("❌ Cannot send money to yourself.")

        receiver = User.objects.filter(phone_number=receiver_phone).first()
        if not receiver:
            raise forms.ValidationError("❌ Receiver not found.")

        cleaned_data['receiver_user'] = receiver
        return cleaned_data

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    form = TransactionAdminForm

    list_display = ('id', 'from_wallet_id', 'to_wallet_id', 'amount', 'transaction_type', 'date','status')
    list_filter = ('transaction_type', 'date')
    search_fields = ('amount',)
    ordering = ('-date',)

    def from_wallet_id(self, obj):
        return obj.from_wallet.id if obj.from_wallet else '-'

    def to_wallet_id(self, obj):
        return obj.to_wallet.id if obj.to_wallet else '-'

    def save_model(self, request, obj, form, change):
        sender = form.cleaned_data['sender_user']
        receiver = form.cleaned_data['receiver_user']
        amount = form.cleaned_data['amount']
        tx_type = form.cleaned_data['transaction_type']

        operation = TransactionOperation(sender, receiver.phone_number, tx_type, amount)
        message = operation.execute_transaction()

        # ما نحاولش نعمل obj.from_wallet = msg.from_wallet لأن msg مجرد string
        self.message_user(request, f"✅ Transaction executed: {message}")

class CollectionRequestAdminForm(forms.ModelForm):
    from_user = forms.ModelChoiceField(queryset=User.objects.all(), label="Requester (From User)")
    to_phone = forms.CharField(label="Receiver Phone")

    class Meta:
        model = CollectionRequest
        fields = ['from_user', 'to_phone', 'amount', 'status']

    def clean(self):
        cleaned_data = super().clean()
        from_user = cleaned_data.get('from_user')
        to_phone = cleaned_data.get('to_phone')
        amount = cleaned_data.get('amount')

        if amount <= 0:
            raise forms.ValidationError("❌ Amount must be positive.")

        to_user = User.objects.filter(phone_number=to_phone).first()
        if not to_user:
            raise ValidationError("❌ Receiver not found.")

        if from_user.national_id == to_user.national_id:
            raise ValidationError("❌ Cannot send a request to yourself.")

        cleaned_data['to_user'] = to_user
        return cleaned_data

@admin.register(CollectionRequest)
class CollectionRequestAdmin(admin.ModelAdmin):
    form = CollectionRequestAdminForm

    list_display = ('id', 'from_user', 'to_user', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('from_user__national_id', 'to_user__phone_number')
    ordering = ('-created_at',)

    def save_model(self, request, obj, form, change):
        from_user = form.cleaned_data['from_user']
        to_user = form.cleaned_data['to_user']
        amount = form.cleaned_data['amount']

        try:
            collect = CollectMoney(from_user, amount, to_user.phone_number)
            collection_request = collect.execute()
            obj.from_user = collection_request.from_user
            obj.to_user = collection_request.to_user
            obj.amount = collection_request.amount
            obj.status = collection_request.status
            obj.req_type = collection_request.req_type
            obj.save()
            self.message_user(request, "✅ Collect request created successfully.")
        except ValidationError as e:
            raise ValidationError(f"❌ {str(e)}")

       

