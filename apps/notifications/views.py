from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        notifications = Notification.objects.filter(
            recipient=request.user,
        ).select_related(
            "actor",
        )[:100]

        serializer = NotificationSerializer(
            notifications,
            many=True,
            context={
                "request": request,
            },
        )

        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()

        return Response({
            "results": serializer.data,
            "unread_count": unread_count,
        })


class NotificationReadView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, notification_id):
        updated = Notification.objects.filter(
            id=notification_id,
            recipient=request.user,
        ).update(
            is_read=True,
        )

        if not updated:
            return Response(
                {
                    "detail": (
                        "Уведомление не найдено."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            "detail": "Уведомление прочитано.",
        })


class NotificationReadAllView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(
            is_read=True,
        )

        return Response({
            "detail": (
                "Все уведомления прочитаны."
            ),
        })