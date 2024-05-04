import pandas as pd
from django.core.management.base import BaseCommand
from stock.models import SP500Stocks, NASDAQStocks, DOWStocks
import numpy as np
from decimal import Decimal

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for model, index_name in [(NASDAQStocks, 'NASDAQ'), (SP500Stocks, 'S&P 500'), (DOWStocks, 'DOW')]:
            self.stdout.write(self.style.SUCCESS(f'Processing {index_name}'))
            stocks = model.objects.exclude(slope__isnull=True, rsi__isnull=True, pe_ratio__isnull=True)
            
            data = {
                'Symbol': [stock.symbol for stock in stocks],
                'Slope': [float(stock.slope) if stock.slope is not None else 0 for stock in stocks],
                'RSI': [float(stock.rsi) if stock.rsi is not None else 0 for stock in stocks],
                'PE_Ratio': [float(stock.pe_ratio) if stock.pe_ratio is not None else 0 for stock in stocks]
            }
            df = pd.DataFrame(data)

            # normalizing
            # favor closer to average p/e ratio
            # favor rsi index inbetween 30-70
            df['Norm_Slope'] = self.normalize_series(df['Slope'])
            df['Norm_PE_Distance'] = self.normalize_series(abs(df['PE_Ratio'] - df['PE_Ratio'].mean()), inverse=True)
            df['Norm_RSI'] = self.normalize_series(df['RSI'])
            # score calcs
            df['Score'] = (
                df['Norm_Slope'] * 0.40 +
                df['Norm_RSI'] * 0.20 +
                df['Norm_PE_Distance'] * 0.40
            ) * (1.2 if ((df['RSI'] >= 30) & (df['RSI'] <= 70)).any() else 1) * 100
            df['Score'] = df['Score'].clip(upper=100) # cap at 100
            # update scores in the database
            for index, row in df.iterrows():
                score = Decimal(row['Score']).quantize(Decimal('.01')) 
                model.objects.filter(symbol=row['Symbol']).update(score=score)

            self.stdout.write(self.style.SUCCESS(f'Scores updated for {index_name}'))

    def normalize_series(self, series, inverse=False):
        min_val = series.min()
        max_val = series.max()
        range_val = max_val - min_val
        if range_val == 0:
            return series * 0 
        normalized = (series - min_val) / range_val
        return 1 - normalized if inverse else normalized
