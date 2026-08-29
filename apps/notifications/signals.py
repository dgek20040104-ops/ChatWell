from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.posts.models import Comment
from apps.posts.models import Follow
from apps.posts.models import PostLike

from .models import Notification
from .services import create_notification


def get_username(user):
    if user is None:
        return "пользователь"

    return (
        getattr(user, "username", None)
        or getattr(user, "display_name", None)
        or "пользователь"
    )


@receiver(
    post_save,
    sender=Follow,
)
def create_follow_notification(
    sender,
    instance,
    created,
    **kwargs,
):
    """
    Создаёт уведомление при новой подписке
    или при отправке запроса на подписку.
    """

    if not created:
        return

    follower = getattr(
        instance,
        "follower",
        None,
    )

    following = getattr(
        instance,
        "following",
        None,
    )

    if follower is None or following is None:
        return

    username = get_username(follower)

    if instance.is_accepted:
        notification_type = (
            Notification.TYPE_FOLLOW
        )

        text = (
            f"Пользователь @{username} "
            "подписался на вас."
        )
    else:
        notification_type = (
            Notification.TYPE_FOLLOW_REQUEST
        )

        text = (
            f"Пользователь @{username} "
            "отправил запрос на подписку."
        )

    create_notification(
        recipient=following,
        actor=follower,
        notification_type=notification_type,
        text=text,
    )


@receiver(
    post_save,
    sender=PostLike,
)
def create_like_notification(
    sender,
    instance,
    created,
    **kwargs,
):
    """
    Создаёт уведомление о новом лайке.
    """

    if not created:
        return

    post = getattr(
        instance,
        "post",
        None,
    )

    actor = getattr(
        instance,
        "user",
        None,
    )

    if post is None or actor is None:
        return

    post_author = getattr(
        post,
        "author",
        None,
    )

    if post_author is None:
        return

    username = get_username(actor)

    create_notification(
        recipient=post_author,
        actor=actor,
        notification_type=(
            Notification.TYPE_LIKE
        ),
        text=(
            f"Пользователь @{username} "
            "поставил лайк вашей публикации."
        ),
        post_id=post.id,
    )


@receiver(
    post_save,
    sender=Comment,
)
def create_comment_notification(
    sender,
    instance,
    created,
    **kwargs,
):
    """
    Создаёт уведомление о новом комментарии.
    """

    if not created:
        return

    post = getattr(
        instance,
        "post",
        None,
    )

    actor = getattr(
        instance,
        "author",
        None,
    )

    if post is None or actor is None:
        return

    post_author = getattr(
        post,
        "author",
        None,
    )

    if post_author is None:
        return

    username = get_username(actor)

    create_notification(
        recipient=post_author,
        actor=actor,
        notification_type=(
            Notification.TYPE_COMMENT
        ),
        text=(
            f"Пользователь @{username} "
            "прокомментировал вашу публикацию."
        ),
        post_id=post.id,
    )