import csv
from django.core.management.base import BaseCommand
from stock.models import SP500Stocks, NASDAQStocks
from django.conf import settings
import os
import pandas as pd
import yfinance as yf
from scipy.stats import linregress
import numpy as np
import requests # library to handle requests
from bs4 import BeautifulSoup
import time
from yahoo_fin.stock_info import *
from decimal import Decimal

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        stocks = NASDAQStocks.objects.exclude(slope__isnull=True, rsi__isnull=True, pe_ratio__isnull=True)
        
        # Create DataFrame from QuerySet
        data = {
            'Symbol': [stock.symbol for stock in stocks],
            'Slope': [float(stock.slope) if stock.slope is not None else np.nan for stock in stocks],
            'RSI': [float(stock.rsi) if stock.rsi is not None else np.nan for stock in stocks],
            'PE_Ratio': [float(stock.pe_ratio) if stock.pe_ratio is not None else np.nan for stock in stocks]
        }
        df = pd.DataFrame(data)
        # Normalize data
        df['Norm_Slope'] = self.normalize_series(df['Slope'])
        df['Norm_RSI'] = self.normalize_series(df['RSI'])
        df['Norm_PE_Ratio'] = self.normalize_series(df['PE_Ratio'], inverse=True)
        
        # Weights
        weights = {'Slope': 0.45, 'RSI': 0.10, 'P/E Ratio': 0.45}
        df['Score'] = (df['Norm_Slope'] * weights['Slope'] +
                       df['Norm_RSI'] * weights['RSI'] +
                       df['Norm_PE_Ratio'] * weights['P/E Ratio']) * 100

        # Handle NaN scores
        df['Score'].fillna(0, inplace=True)  # Replace NaN with 0 or another appropriate value

        # Update the database with new scores
        for index, row in df.iterrows():
            if not np.isnan(row['Score']):  # Only update if score is not NaN
                NASDAQStocks.objects.filter(symbol=row['Symbol']).update(score=row['Score'])

    def normalize_series(self, series, inverse=False):
        """ Normalize a pandas series to a 0-1 range, optionally inversing the values. """
        series = series.astype(float)  # Ensure all data is float
        normalized = (series - series.min()) / (series.max() - series.min())
        return 1 - normalized if inverse else normalized