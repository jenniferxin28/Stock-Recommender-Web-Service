import csv
from django.core.management.base import BaseCommand
from stock.models import SP500Stocks, NASDAQStocks, DOWStocks
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

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        dow_symbols = tickers_dow(False)
        #yfinance uses dashes instead of dots - but only for historical data?
        dow = [item.replace(".", "-") for item in dow_symbols]
        # calculate p/e ratio
        dow_ratios = {}
        for symbol in dow:
            ticker = yf.Ticker(symbol)
            ratio = ticker.info.get('trailingPE')
            try:
                # Ensure ratio is a float before appending
                ratio = float(ratio) if ratio is not None else None
            except ValueError:
                # Handle the case where conversion to float fails (e.g., if ratio is a string that cannot be converted)
                ratio = None
            dow_ratios[symbol] = ratio

        valid_ratios = [ratio for ratio in dow_ratios.values() if ratio is not None]
        average_pe_ratio = sum(valid_ratios) / len(valid_ratios) if valid_ratios else None
        std_pe_ratio = np.std(valid_ratios) if valid_ratios else None
        max_pe_ratio = max(valid_ratios)
        min_pe_ratio = min(valid_ratios)
        #print(f'Average P/E ratio: {average_pe_ratio}')
        #print(f'STD P/E ratio: {std_pe_ratio}')
        #print(f'Max P/E ratio: {max_pe_ratio}')
        #print(f'Min P/E ratio: {min_pe_ratio}')
        # convert to np array
        valid_ratios = np.array([ratio for ratio in dow_ratios.values() if ratio is not None])
        Q1 = np.percentile(valid_ratios, 25)
        Q3 = np.percentile(valid_ratios, 75)
        # calculate IQR
        IQR = Q3 - Q1
        # Determine outliers
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        # Filter out outliers
        filtered_ratios = valid_ratios[(valid_ratios >= lower_bound) & (valid_ratios <= upper_bound)]
        average_pe_ratio_without_outliers = np.mean(filtered_ratios)
        std_pe_ratio_without_outliers = np.std(filtered_ratios)
        #print(f"Average P/E Ratio without outliers: {average_pe_ratio_without_outliers}")
        #print(f"Standard Deviation P/E Ratio without outliers: {std_pe_ratio_without_outliers}")


        # calculate top stocks
        def fetch_data_with_retry(symbol, retries=6, delay=1):
            for attempt in range(retries):
                try:
                    return yf.Ticker(symbol).history(period="1y")
                except Exception as e:
                    print(f"Attempt {attempt+1} failed: {e}")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
            print(f"Failed to fetch data for {symbol} after {retries} attempts.")
            return None
        # calculate RSI
        def calculate_rsi(data, window=14):
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).fillna(0)
            loss = (-delta.where(delta < 0, 0)).fillna(0)
            avg_gain = gain.rolling(window=window, min_periods=window).mean()
            avg_loss = loss.rolling(window=window, min_periods=window).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.dropna()

        results = []
        for symbol in dow_symbols:
            stock_data = fetch_data_with_retry(symbol, retries=6, delay=1)
            if stock_data is None or stock_data.empty:
                print(f"Data for {symbol} is empty or could not be fetched.")
                continue
            x_stock = np.arange(len(stock_data.index))
            y_stock = stock_data['Close'].values
            # get latest RSI
            rsi_series = calculate_rsi(stock_data['Close'])
            if not rsi_series.empty:
                rsi_stock = rsi_series.iloc[-1]
            else:
                rsi_stock = None
            # Calculate linear regression for each stock
            slope_stock, intercept_stock, _, _, _ = linregress(x_stock, y_stock)
            # P/E ratio
            pe_ratio = dow_ratios[symbol.replace("-", ".")]
            results.append({'Symbol': symbol, 'Slope': slope_stock, 'Intercept': intercept_stock, 'RSI': rsi_stock, 'P/E Ratio': pe_ratio})
        results_df = pd.DataFrame(results)

        # normalizing data
        # apply scoring to the slope, p/e ratio, rsi
        # normalize data
        def normalize_series(data, inverse=False):
            # normalize to 0-1 range, inverse=True to reward lower values like P/E ratio
            normalized = (data - data.min()) / (data.max() - data.min())
            return 1 - normalized if inverse else normalized
        # scoring weights
        weights = {'Slope': 0.45, 'RSI': 0.10, 'P/E Ratio': 0.45}
        results_df['Norm_Slope'] = normalize_series(results_df['Slope'])
        results_df['Norm_RSI'] = normalize_series(results_df['RSI'])
        results_df['Norm_PE_Ratio'] = normalize_series(results_df['P/E Ratio'], inverse=True)
        results_df['Score'] = (results_df['Norm_Slope'] * weights['Slope'] +
                        results_df['Norm_RSI'] * weights['RSI'] +
                        results_df['Norm_PE_Ratio'] * weights['P/E Ratio'])*100
        sorted_data = results_df.sort_values(by='Score', ascending=False)
        for column in ['Slope', 'Intercept', 'RSI', 'P/E Ratio', 'Score']:
            sorted_data[column] = sorted_data[column].apply(lambda x: None if pd.isna(x) or x== "nan" else x)
        df_clean = sorted_data.copy()
        df_clean['Slope'] = pd.to_numeric(df_clean['Slope'], errors='coerce')
        df_clean['Intercept'] = pd.to_numeric(df_clean['Intercept'], errors='coerce')
        df_clean['RSI'] = pd.to_numeric(df_clean['RSI'], errors='coerce')
        df_clean['P/E Ratio'] = pd.to_numeric(df_clean['P/E Ratio'], errors='coerce')
        df_clean['Score'] = pd.to_numeric(df_clean['Score'], errors='coerce')
        # Django keeps having issues inserting rows with NaN even though I cleaned it multiple times
        for index, row in df_clean.iterrows():
            stock, created = DOWStocks.objects.update_or_create(
                symbol=row['Symbol'], 
                defaults={
                    'slope': None if pd.isna(row['Slope']) else round(row['Slope'], 5),
                    'intercept': None if pd.isna(row['Intercept']) else round(row['Intercept'], 5),
                    'rsi': None if pd.isna(row['RSI']) else round(row['RSI'], 5),
                    'pe_ratio': None if pd.isna(row['P/E Ratio']) else round(row['P/E Ratio'], 5),
                    'score': None if pd.isna(row['Score']) else round(row['Score'], 5)
                }
            )
            if created:
                print(f"Created new entry for: {stock.symbol}")
            else:
                print(f"Updated existing entry for: {stock.symbol}")
                