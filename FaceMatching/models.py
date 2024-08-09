from django.db import models

# Create your models here.
# models.py
# models.py

from django.db import models

class UserData(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='user_images/')

    def __str__(self):
        return str(self.id)

