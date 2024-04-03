from django.core.management.base import BaseCommand
import pandas as pd
from yahoo_fin.stock_info import get_data
from single_page_app.models import Stock, StockPrice

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        ticker_list = ['AAPL', 'AMZN', 'MSFT', 'GOOGL', 'NVDA']
        one_month_data = {}
        for ticker in ticker_list:
            one_month_data[ticker] = get_data(ticker, start_date = "11/01/2023", 
                end_date = "02/01/2024", index_as_date = True, interval = "1d")
        for ticker, data in one_month_data.items():
            stock, created = Stock.objects.get_or_create(symbol=ticker)
            for index, row in data.iterrows():
                StockPrice.objects.update_or_create(
                    stock=stock,
                    date=index,
                    defaults={
                        'open_price': row['open'], 
                        'high_price': row['high'],
                        'low_price': row['low'], 
                        'close_price': row['close'], 
                        'volume': row['volume']
                    }
                )