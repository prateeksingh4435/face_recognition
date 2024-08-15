from django.db import models

from django.db import models

class UserData(models.Model):
    empid = models.CharField(max_length =100)
    image = models.ImageField(upload_to='user_images/')

    def __str__(self):
        return self.empid

