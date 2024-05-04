from decimal import Decimal
import time
import yfinance as yf
from django.core.management.base import BaseCommand
from stock.models import SP500Stocks, DOWStocks, NASDAQStocks, StockData

class Command(BaseCommand):
    help = 'Loads stock data from the past year for the top and bottom 10 stocks of SP500, DOW, and NASDAQ'

    def handle(self, *args, **options):
        indices = [
            (SP500Stocks, 'S&P 500'),
            (DOWStocks, 'DOW'),
            (NASDAQStocks, 'NASDAQ')
        ]

        for model, index_name in indices:
            self.stdout.write(self.style.SUCCESS(f'Processing {index_name} stocks'))

            top_10_stocks = list(model.objects.filter(slope__isnull=False, pe_ratio__isnull=False, rsi__isnull=False)
                     .order_by('-score')[:10]
                     .values_list('symbol', flat=True))

            bottom_10_stocks = list(model.objects.filter(slope__isnull=False, pe_ratio__isnull=False, rsi__isnull=False)
                        .order_by('score')[:10]
                        .values_list('symbol', flat=True))
            stocks_to_load = list(set(top_10_stocks + bottom_10_stocks))

            for symbol in stocks_to_load:
                retry_count = 0
                max_retries = 5
                success = False

                while retry_count < max_retries and not success:
                    self.stdout.write(f'Attempting to load data for {symbol} (Attempt {retry_count + 1})')
                    data = yf.download(symbol, period="1y")

                    if not data.empty:
                        success = True
                        self.stdout.write(f'Successfully loaded data for {symbol}')
                        for index, row in data.iterrows():
                            StockData.objects.update_or_create(
                                symbol=symbol,
                                date=index.date(),
                                defaults={
                                    'open': Decimal(row['Open']),
                                    'close': Decimal(row['Close']),
                                    'high': Decimal(row['High']),
                                    'low': Decimal(row['Low']),
                                    'volume': int(row['Volume'])
                                }
                            )
                    else:
                        self.stdout.write(self.style.WARNING(f'Data not found for {symbol}, retrying...'))
                        time.sleep(5)  # avoid api limits
                        retry_count += 1

                if not success:
                    self.stdout.write(self.style.ERROR(f'Failed to load data for {symbol} after {max_retries} attempts'))

        self.stdout.write(self.style.SUCCESS('Finished loading stock data'))

