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

class RUSSELLStocks(models.Model):
    symbol = models.CharField(max_length=10, primary_key=True)
    slope = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    intercept = models.DecimalField(max_digits=15, decimal_places=5, null=True, blank=True)
    rsi = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    pe_ratio = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)
    score = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)

    def __str__(self):
        return self.symbol