import yfinance as stocks #Imports yahoo finance package
import sqlite3 as sqlite
from datetime import datetime
import requests

def compileStockData(stockData):
  #List of attribute names and their respective key in .info's dictionary
  attributes = [['Beta','beta'],
    ['Sector','sector'],
    ['Market Capitalization','marketCap'],
    ['Trailing P/E','trailingPE'],
    ['Forward P/E','forwardPE'],
    ['Trailing EPS','trailingEps'],
    ['Forward EPS','forwardEps'],
    ['52 Week High','fiftyTwoWeekHigh'],
    ['52 Week Low','fiftyTwoWeekLow'],
    ['Daily Low','dayLow'],
    ['Daily High','dayHigh'],
    ['Long Summary','longBusinessSummary'],
    ['Dividend Yield','dividendYield'],
    ['Dividend Rate', 'dividendRate'],
    ['5 Year Average Dividend Yield','fiveYearAvgDividendYield'],
    ['10 Day Average Volume','averageVolume10Days'],
    ['Previous Close','previousClose'],
    ['Open Price','open'],
    ['Ask Price','ask'],
    ['Average Volume','averageVolume'],
    ['Volume','volume'],
    ['Website','website'],
    ['Logo URL','logo_url']]
  for stockSet in stockData:
    #Create stock object used to extract stock's data
    stock = stocks.Ticker(stockSet['Symbol'])
    #.info dictionary is stored as a constant so it isn't loaded multiple times as this greatly decreases program efficiency
    #Try except in case stock isn't listed on yfinance 
    try:
      info = stock.info
    except:
      {}
    #Loop stores data from .info dictionary into stockSet dictionary
    for attribute in attributes:
      try:
        stockSet[attribute[0]] = info[attribute[1]]
      except:
        stockSet[attribute[0]] = None
    del(stock)
  return stockData

def updateDatabase(stockData):
  #Create connection to database
  stockDB = sqlite.connect('stockDB.db')
  db = stockDB.cursor()


  dateTimeObj = datetime.now()
  timestamp = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S)")

  #Loop through list of stock data
  for stock in stockData:
    #Inserts stock data in stockTbl
    db.execute("""UPDATE stockTbl 
    SET businessSummary = ?,
    website = ?,
    logoURL = ?,
    askPrice = ?,
    openPrice = ?,
    previousClose = ?,
    dailyLow = ?,
    dailyHigh = ?,
    fiftyTwoWeekLow = ?,
    fiftyTwoWeekHigh = ?,
    capitalization = ?,
    volume = ?,
    averageVolume = ?,
    tenDayAvgVolume = ?,
    dividend = ?,
    fiveYearAvgDividendYield = ?,
    beta = ?,
    trailingEPS = ?,
    forwardEPS = ?,
    trailingPE = ?,
    forwardPE = ?,
    lastUpdated = ?
    WHERE stockSymbol = ?""",
    (
    stock['Long Summary'],
    stock['Website'],
    stock['Logo URL'],
    stock['Ask Price'],
    stock['Open Price'],
    stock['Previous Close'],
    stock['Daily Low'],
    stock['Daily High'],
    stock['52 Week Low'],
    stock['52 Week High'],
    stock['Market Capitalization'],
    stock['Volume'],
    stock['Average Volume'],
    stock['10 Day Average Volume'],
    stock['Dividend Yield'],
    stock['5 Year Average Dividend Yield'],
    stock['Beta'],
    stock['Trailing EPS'],
    stock['Forward EPS'],
    stock['Trailing P/E'],
    stock['Forward P/E'],
    timestamp,
    stock['Symbol']
    ))
    stockDB.commit()
    

  stockDB.close()

def update(stock_symbol):
  #Runs all functions
  stock_set = {}
  stock_set['Symbol'] = stock_symbol
  stock_data = [stock_set]
  stock_data = compileStockData(stock_data)
  updateDatabase(stock_data)