from django.shortcuts import render
from rest_framework import viewsets, permissions, generics
from .models import Transaction, CollectionRequest
from .serializers import TransactionSerializer, CollectMoneySerializer
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from django.db import models

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]  
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['transaction_type', 'status', 'date']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Transaction.objects.all()
        
        return Transaction.objects.filter(
            models.Q(from_wallet__user=user) | 
            models.Q(to_wallet__user=user)
        ).order_by('-date')
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            transaction = serializer.save()
            output_serializer = self.get_serializer(transaction)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)


class CollectionRequestViewSet(viewsets.ModelViewSet):
    serializer_class = CollectMoneySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["from_user", "created_at", "status"]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return CollectionRequest.objects.all()

        return CollectionRequest.objects.filter(
            models.Q(to_user=user) | models.Q(from_user=user)
        )
    
    @action(detail=False, methods=["get"], url_path="received")
    def received_requests(self, request):
        status_param = request.query_params.get("status")
        filters = {"to_user": request.user}
        if status_param:
            filters["status"] = status_param

        queryset = CollectionRequest.objects.filter(**filters)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="sent")
    def sent_requests(self, request):
        filters = {"from_user": request.user}
        status_param = request.query_params.get("status")
        if status_param:
            filters["status"] = status_param

        queryset = CollectionRequest.objects.filter(**filters)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='approve')
    def approve_request(self, request, pk=None):
        collection_req = self.get_object()
        
        # Only recipient can approve
        if collection_req.to_user != request.user:
            return Response(
                {"error": "❌ Only the recipient can approve this request"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if already processed
        if collection_req.status != CollectionRequest.Status.PENDING:
            return Response(
                {"error": "❌ Request already processed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create transaction
        from .services import TransactionOperation
        operation = TransactionOperation(
            from_user=collection_req.to_user,
            to_phone=collection_req.from_user.phone_number,
            payment_type=Transaction.TransactionType.SEND,
            amount=collection_req.amount
        )
        
        try:
            transaction = operation.execute_transaction()
            collection_req.status = CollectionRequest.Status.APPROVED
            collection_req.transaction = transaction    
            collection_req.save()
            
            return Response({
                "message": "✅ Request approved and money transferred",
                "transaction_id": transaction.id,
                "amount": str(transaction.amount)
            }, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response(
                {"error": f"❌ {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['patch'], url_path='reject')
    def reject_request(self, request, pk=None):
        collection_req = self.get_object()
        
        if collection_req.to_user != request.user:
            return Response(
                {"error": "❌ Only the recipient can reject this request"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if collection_req.status != CollectionRequest.Status.PENDING:
            return Response(
                {"error": "❌ Request already processed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        collection_req.status = CollectionRequest.Status.REJECTED
        collection_req.save()
        
        return Response({
            "message": "✅ Request rejected"
        }, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)