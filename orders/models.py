from django.utils.timezone import now
from django.db import models
from accounts.models import Trader
from djongo.models.fields import ObjectIdField


class Order(models.Model):
    _id = ObjectIdField()
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE)
    TYPE = (
        ('S', 'SALE'),
        ('P', 'PURCHASE')
    )
    type = models.CharField(max_length=1, choices=TYPE)
    btc = models.FloatField()
    price = models.FloatField()
    active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.trader}, {self.timestamp}, {self.type}"
