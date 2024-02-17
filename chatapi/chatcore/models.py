from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.
User = get_user_model()


class ChatGptBot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    messageInput = models.TextField()
    bot_response = models.TextField()

    def __str__(self):
        return self.user.username


class ChatGptApiKey(models.Model):
    api_key = models.CharField(max_length=255)

    def __str__(self):
        return self.api_key


def content_file_name(instance, filename):
    return 'openapp/doc/' + instance.speciality + '/' + filename


class ChatGptPdf(models.Model):
    speciality = models.CharField(max_length=255)
    document = models.FileField(upload_to=content_file_name)

    def __str__(self):
        return str(self.document)


class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    speciality = models.CharField(max_length=255)

    def __str__(self):
        return self.user.username