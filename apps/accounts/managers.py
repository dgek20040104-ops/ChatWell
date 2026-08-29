from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Номер телефона обязателен")

        phone = self.normalize_phone(phone)

        user = self.model(
            phone=phone,
            **extra_fields,
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_phone_verified", True)

        if not password:
            raise ValueError("У суперпользователя должен быть пароль")

        return self.create_user(
            phone=phone,
            password=password,
            **extra_fields,
        )

    @staticmethod
    def normalize_phone(phone):
      phone = str(phone or "").strip()

      phone = phone.replace(
        " ",
        "",
      ).replace(
        "-",
        "",
      ).replace(
        "(",
        "",
      ).replace(
        ")",
        "",
      )

      if phone.startswith("8"):
        phone = "+7" + phone[1:]

      elif phone.startswith("7"):
        phone = "+" + phone

      return phone