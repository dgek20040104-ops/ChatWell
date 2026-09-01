from django.db import migrations
from django.db import models


class Migration(
    migrations.Migration
):
    dependencies = [
        (
            "accounts",
            "0002_user_is_online",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_verified",
            field=models.BooleanField(
                default=False,
            ),
        ),
    ]
