from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)


class UserManager(BaseUserManager):
	def create_user(self, user_id, access_token, refresh_token):
		user = self.model(username = user_id,
			spotify_access_token = access_token,
			spotify_refresh_token = refresh_token)

		user.set_unusable_password()
		user.save(using = self._db)
		return user

	def create_superuser(self, user_id, access_token, refresh_token):
		return create_user(user_id, access_token, refresh_token)

class User(AbstractBaseUser):
	username = models.CharField(primary_key = True, max_length = 500)
	spotify_access_token = models.CharField(max_length = 500)
	spotify_refresh_token = models.CharField(max_length = 500)

	objects = UserManager()

	USERNAME_FIELD = 'username'
	REQUIRED_FIELDS = ['spotify_access_token', 'spotify_refresh_token']

	def __str__(self):
		return self.username

	def has_perm(self, perm, obj = None):
		return True

	def has_model_perms(self, app_label):
		return True

	@property
	def is_staff(self):
		return False
	