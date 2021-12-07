import streamlit as st
from PIL import Image
import pandas as pd 
import base64 
import matplotlib.pyplot as plt 
from bs4 import BeautifulSoup
import requests
import json
import time

#The code below tells streamlit to expand the page to full width
st.set_page_config(layout = "wide")

#logo image, width will be 500 pixels
image = Image.open('logo.jpg')

st.image(image,width = 500)
st.title('Crypto Price App')
st.markdown("""This app helps you track the top 100 crpyto currencies by market cap""")

#The about section is below, this will be an expandable div type section with info on our app/data source etc.

expander_bar = st.expander("About")
expander_bar.markdown(""" 
* **Python libtaries: pandas, streamlit, numpy, matplotlib, seaborn, BeautifulSoup
* **Data source: [CoinMarketCap] (https://coinmarketcap.com)

""")

#This divides the page into three columns, similar to how bootstrap would do it... 
#the (2,1) sets the df column(col2) to twice the width of the %change(col3) column...
col1 = st.sidebar
col2, col3 = st.columns((2,1))

#This is the sidebar header
col1.header('Input Options')

#This is the sidebar description/selector, user has the option to denominate prices in dollars, bitcoins or eth. 
# currency_price_unit = 'USD'
currency_price_unit = col1.selectbox('Select currenct for price',('USD', 'BTC', 'ETH') )

#This scrapes the web for crypto data

#the @st.cache creates a cache of the data
@st.cache
def load_data():
    #collects raw data from cmarkcap
    cmc = requests.get('https://coinmarketcap.com')

    #parses the data 
    soup = BeautifulSoup(cmc.content, 'html.parser')
    
    #finds the part of the data with the parameters we are looking for?
    data = soup.find('script', id='__NEXT_DATA__', type='application/json')
    coins = {}

    # print(data)
    #reloading the data as json structure into coin_data
    coin_data = json.loads(data.contents[0])
    #pulling the data we want from the long list of dictionaries
    listings = coin_data['props']['initialState']['cryptocurrency']['listingLatest']['data']
    #adds coins to the coin dictionary, coin id set equal to slug which is their name...
    
    ##need a better way of doing this because the Json will not make a dictionary for me automatically...
    ##this is slowing the app down significantly at the moment...
    arr2 = []
    count = 0
    for listing in listings:
        if count ==0:
            count +=1
            continue
        temp = {}
        for j in range(len(listings[0]['keysArr'])):
            print(listings[0]['keysArr'][j])
            print(listing[j])
            temp[str(listings[0]['keysArr'][j])]= listing[j]
            
        arr2.append(temp)
        
    

    # arr1 = listings[0]['keysArr']
    # idLoc = 0
    # slugLoc = 0

    # for i in range(len(arr1)):
    #     if arr1[i]=='id':
    #         idLoc = i
    #     if arr1[i]=='slug':
    #         slugLoc = i

    count = 0
    for i in arr2:
        # if count ==0:
        #     count +=1
        #     continue
        
        coins[str(i['id'])]=i['slug']
        # coins[str(i['id'])] = i['slug']



    #defining variables to be places in our array/data structur
    coin_name = []
    coin_symbol = []
    market_cap = []
    percent_change_1h = []
    percent_change_24h = []
    percent_change_7d = []
    price = []
    volume_24h = []

    #populates the arrays above with data from the json file..
    for i in arr2:
        coin_name.append(i['slug'])
        coin_symbol.append(i['symbol'])
        price.append(i['quote.'+ currency_price_unit + '.price'])
        percent_change_1h.append(i['quote.'+currency_price_unit+'.percentChange1h'])
        percent_change_24h.append(i['quote.'+currency_price_unit+'.percentChange24h'])
        percent_change_7d.append(i['quote.'+currency_price_unit+'.percentChange7d'])
        market_cap.append(i['quote.'+currency_price_unit+'.marketCap'])
        volume_24h.append(i['quote.'+currency_price_unit+'.volume24h'])
        
    #creates a pandas dataframce 
    df = pd.DataFrame(columns=['coin_name', 'coin_symbol', 'market_cap', 'percent_change_1h', 'percent_change_24h', 'percent_change_7d', 'price', 'volume_24h'])
    df['coin_name'] = coin_name
    df['coin_symbol'] = coin_symbol
    df['price'] = price
    df['percent_change_1h'] = percent_change_1h
    df['percent_change_24h'] = percent_change_24h
    df['percent_change_7d'] = percent_change_7d
    df['market_cap'] = market_cap
    df['volume_24h'] = volume_24h
    return df

df = load_data()

## Sidebar - Cryptocurrency selections
##thissorts the currencs alphabetically by the coin symbol
sorted_coin = sorted( df['coin_symbol'] )
#the line below tells streamlit to create a multiselection box, we can type in a coin and it will suggest the name and we can select that coin...
selected_coin = col1.multiselect('Cryptocurrency', sorted_coin, sorted_coin)

#shows only the selected coins...
df_selected_coin = df[ (df['coin_symbol'].isin(selected_coin)) ] # Filtering data

## Sidebar - Number of coins to display
##this is a slider from 1-100 which tells how many coins to display
##if set to 30, the top largest 30 coins are shown
num_coin = col1.slider('Display Top N Coins', 1, 100, 100)

df_coins = df_selected_coin[:num_coin]

## Sidebar - Percent change timeframe
#user can select the timeframe for which to base the percent change of the coin...
percent_timeframe = col1.selectbox('Percent change time frame',
                                    ['7d','24h', '1h'])
#this is a maps the key of '7d' etc from the select box to value of 'percent change 7d' to display to user
percent_dict = {"7d":'percent_change_7d',"24h":'percent_change_24h',"1h":'percent_change_1h'}

#assign a variable to the current prefered timeframe
selected_percent_timeframe = percent_dict[percent_timeframe]

## Sidebar - Sorting values
#creates a selectbox to ask user if they want values sorted...
sort_values = col1.selectbox('Sort values?', ['Yes', 'No'])

#creats a header, info and pupulates the dataframe...
col2.subheader('Price Data of Selected Cryptocurrency')
col2.write('Data Dimension: ' + str(df_selected_coin.shape[0]) + ' rows and ' + str(df_selected_coin.shape[1]) + ' columns.')

col2.dataframe(df_coins)

# Download CSV data..self explanatory
# https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="crypto.csv">Download CSV File</a>'
    return href

col2.markdown(filedownload(df_selected_coin), unsafe_allow_html=True)

#---------------------------------#
# Preparing data for Bar plot of % Price change
col2.subheader('Table of % Price Change')
df_change = pd.concat([df_coins.coin_symbol, df_coins.percent_change_1h, df_coins.percent_change_24h, df_coins.percent_change_7d], axis=1)
df_change = df_change.set_index('coin_symbol')
#creates columns with a 1 for positive change and a 0 for negative...
#...to use later when determining red or green bar in barchart
df_change['positive_percent_change_1h'] = df_change['percent_change_1h'] > 0
df_change['positive_percent_change_24h'] = df_change['percent_change_24h'] > 0
df_change['positive_percent_change_7d'] = df_change['percent_change_7d'] > 0
col2.dataframe(df_change)

# Conditional creation of Bar plot (time frame)
col3.subheader('Bar plot of % Price Change')

## pupulates the bar plot based on time frame selected for %change
if percent_timeframe == '7d':
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percent_change_7d'])
    col3.write('*7 days period*')
    plt.figure(figsize=(5,25))
    plt.subplots_adjust(top = 1, bottom = 0)
    df_change['percent_change_7d'].plot(kind='barh', color=df_change.positive_percent_change_7d.map({True: 'g', False: 'r'}))
    col3.pyplot(plt)
elif percent_timeframe == '24h':
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percent_change_24h'])
    col3.write('*24 hour period*')
    plt.figure(figsize=(5,25))
    plt.subplots_adjust(top = 1, bottom = 0)
    df_change['percent_change_24h'].plot(kind='barh', color=df_change.positive_percent_change_24h.map({True: 'g', False: 'r'}))
    col3.pyplot(plt)
else:
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percent_change_1h'])
    col3.write('*1 hour period*')
    plt.figure(figsize=(5,25))
    plt.subplots_adjust(top = 1, bottom = 0)
    df_change['percent_change_1h'].plot(kind='barh', color=df_change.positive_percent_change_1h.map({True: 'g', False: 'r'}))
    col3.pyplot(plt)