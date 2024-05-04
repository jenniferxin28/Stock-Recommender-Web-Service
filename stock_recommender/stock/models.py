from django.db import models

# Create your models here.
class SP500Stocks(models.Model):
    symbol = models.CharField(max_length=10, primary_key=True)
    slope = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    intercept = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    rsi = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    score = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)

    def __str__(self):
        return self.symbol

class NASDAQStocks(models.Model):
    symbol = models.CharField(max_length=10, primary_key=True)
    slope = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    intercept = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    rsi = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    score = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)

    def __str__(self):
        return self.symbol

class DOWStocks(models.Model):
    symbol = models.CharField(max_length=10, primary_key=True)
    slope = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    intercept = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    rsi = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    score = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)

    def __str__(self):
        return self.symbol

class StockData(models.Model):
    symbol = models.CharField(max_length=10)
    open = models.DecimalField(max_digits=10, decimal_places=2)
    close = models.DecimalField(max_digits=10, decimal_places=2)
    high = models.DecimalField(max_digits=10, decimal_places=2)
    low = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    date = models.DateField()

    def __str__(self):
        return self.symbol
    
    class Meta:
        unique_together = [['symbol', 'date']]