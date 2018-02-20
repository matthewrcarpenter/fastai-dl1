"""Financial utility functions."""
import pandas as pd
import datetime as dt
import pandas_datareader.data as web

import pytrends
from pytrends.request import TrendReq

DATA_PATH = "data"

def get_df_start_date(data_frame) :
	return min(data_frame.index).date()


def get_df_end_date(data_frame) :
	return max(data_frame.index).date()


def get_price_data(ticker) :
	"""Get price data for ticker. Rows with NA values will be removed from data."""
	# Defualt to yahoo for now
	data = get_price_data_yahoo(ticker).dropna()
	start_date = get_df_start_date(data)
	end_date = get_df_end_date(data)


	print(f'Loaded data for {ticker}: {start_date} to {end_date}.')
	return data

def update_price_data_yahoo(price_data, ticker) :
    # try to update from next day after end of data
    price_data_end_date = get_df_end_date(price_data) 
    req_start_date =  price_data_end_date + dt.timedelta(1)
    # ... until yesterday
    req_end_date = dt.date.today() - dt.timedelta(1)
    
    # Might not need to do update
    if (req_end_date <= req_start_date) :
    	return price_data

    price_data_path = f'{DATA_PATH}/yahoo/{ticker}.csv'
    
    # default to original data if update fails
    updated_data = price_data
    
    try :
	    updated_data = web.DataReader(ticker, 'yahoo', req_start_date, req_end_date)
	    actual_end_date = get_df_end_date(updated_data)

	    # just return original price_data if acupdate needed
	    if (actual_end_date <= price_data_end_date) :
	    	return price_data
	    else :
        	updated_data = price_data.append(updated_data)
        	print(f'Updated data for {ticker} from yahoo: {req_start_date} to {actual_end_date}')
        	updated_data.to_csv(price_data_path)
    except :
    	print(f'Could not load updates for {ticker} from yahoo. Using cached data.')

    return updated_data        

def get_price_data_yahoo(ticker) :
    """Get raw ticker price data from yahoo. No data cleaning is performed on data."""
    start = dt.datetime(1970, 1, 1)
    end = dt.date.today() - dt.timedelta(1)
    
    price_data_path = f'{DATA_PATH}/yahoo/{ticker}.csv'
    
    # Load local copy
    try :
    	# read local copy
        price_data = pd.read_csv(price_data_path, parse_dates=True, index_col=0)
        # try to update
        #price_data = update_price_data_yahoo(price_data_yahoo)
        #price_data.set_index('Date', inplace=True)
        # FIXME check if up to date, if not update and save
    except :
        print(f'Could not read file: {price_data_path}. Downloading data for "{ticker}" from yahoo.com...')
        price_data = web.DataReader(ticker, 'yahoo', start, end)
        price_data.to_csv(price_data_path)
    
    return price_data


def add_sma_column(data_frame, col_name, num_days) :
    """Calculate the Simple Moving Average (SMA) over num_days for col_name and add to data_frame."""  
    data_frame[f'{col_name} SMA{num_days}'] = data_frame[col_name].rolling(window=num_days).mean()


def add_sma_info(data_frame, col_name) :
    """Calculate several Simple Moving Averages (SMAs) of col_name in a data_frame and add the SMA values to the data_frame"""
    sma_days = [5, 10, 20, 50, 100, 200]
    for d in sma_days :
        add_sma_column(data_frame, col_name, d)


def get_google_trends(data_frame, search):
        
        # create data_range
        date_range = [f'{get_df_start_date(data_frame)} {get_df_end_date(data_frame)}']
        
        # Set up the trend fetching object
        pytrends = TrendReq(hl='en-US', tz=360)
        kw_list = [search]

        try:
        
            # Create the search object
            pytrends.build_payload(kw_list, cat=0, timeframe=date_range[0], geo='', gprop='news')
            
            # Retrieve the interest over time
            trends = pytrends.interest_over_time()

            related_queries = pytrends.related_queries()

        except Exception as e:
            print('\nGoogle Search Trend retrieval failed.')
            print(e)
            return

        # Upsample the data for joining with training data
        trends = trends.resample('D').mean()
        trends = trends.interpolate(method='linear')
        #trends = trends.reset_index(level=0)
        
        return trends, related_queries