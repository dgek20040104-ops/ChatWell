from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import TemplateView

from apps.posts.models import Post
from apps.posts.serializers import PostSerializer


class ReelsFeedView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        reels = (
            Post.objects
            .filter(
                post_type=Post.REEL,
                is_archived=False,
            )
            .select_related(
                "author",
            )
            .prefetch_related(
                "media",
                "likes",
                "comments",
                "saved_by_users",
            )
            .order_by(
                "-created_at",
            )
        )

        serializer = PostSerializer(
            reels,
            many=True,
            context={
                "request": request,
            },
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class ReelsPageView(TemplateView):
    template_name = "reels/reels.html"