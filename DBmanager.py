import sqlite3
class dbManager:
  def __init__(self,dbname):
    self.conn = sqlite3.connect(dbname)
    self.cursor = self.conn.cursor()
  
  def __enter__(self):
    return self
    
  def __exit__(self, exc_class, exc, traceback):
    self.conn.commit()
    self.conn.close()
  
  def get_leaders(self, param, high):
    if high:
      stocks = []
      for stock_data_tuple in self.cursor.execute('SELECT stockName,askPrice,(%s),stockSymbol FROM stockTbl WHERE %s IS NOT NULL ORDER BY (%s) DESC LIMIT 10' % (param,param,param)):
        stock = {}
        stock['Stock Name'] = stock_data_tuple[0]
        stock['Ask Price'] = stock_data_tuple[1]
        stock['Parameter'] = stock_data_tuple[2]
        stock['Stock Symbol'] = stock_data_tuple[3]
        stocks.append(stock)
    else:
      stocks = []
      for stock_data_tuple in self.cursor.execute('SELECT stockName,askPrice,(%s),stockSymbol FROM stockTbl WHERE %s IS NOT NULL ORDER BY (%s) ASC LIMIT 10' % (param,param,param)):
        stock = {}
        stock['Stock Name'] = stock_data_tuple[0]
        stock['Ask Price'] = stock_data_tuple[1]
        stock['Parameter'] = stock_data_tuple[2]
        stock['Stock Symbol'] = stock_data_tuple[3]
        stocks.append(stock)
    return stocks

  def get_stocks_in_range(self,start,end,param,high,search):
    stocks = []
    #Gets rudimentary data from database for each stock
    if high:
      for stock in self.cursor.execute('SELECT stockName, stockSymbol, askPrice, forwardEPS, forwardPE,(%s) FROM stockTbl WHERE stockName LIKE(?) ORDER BY (%s) DESC LIMIT ? OFFSET ?' % (param,param),(search+'%',end-start,start)):
        stock_dict = {}
        stock_dict['Stock Name'] = stock[0]
        stock_dict['Stock Symbol'] = stock[1]
        stock_dict['Ask Price'] = stock[2]
        stock_dict['Forward EPS'] = stock[3]
        stock_dict['Forward PE'] = stock[4]
        stock_dict['Param'] = stock[5]
        stocks.append(stock_dict)
    else:
      for stock in self.cursor.execute('SELECT stockName, stockSymbol, askPrice, forwardEPS, forwardPE,(%s) FROM stockTbl ORDER BY (%s) DESC LIMIT ? OFFSET ?' % (param,param),(end-start,start)):
        stock_dict = {}
        stock_dict['Stock Name'] = stock[0]
        stock_dict['Stock Symbol'] = stock[1]
        stock_dict['Ask Price'] = stock[2]
        stock_dict['Forward EPS'] = stock[3]
        stock_dict['Forward PE'] = stock[4]
        stock_dict['Param'] = stock[5]
        stocks.append(stock_dict)
    return stocks
    
  def get_value(self,column,table,query,values):
    value = [0]
    valuesR = []
    for value_tuple in self.cursor.execute('SELECT %s FROM %s WHERE %s' % (column,table,query),values):
      value = value_tuple
      valuesR.append(value_tuple)
    return value,valuesR
  
  def update(self,column_statement,table,query,values):
    self.cursor.execute('UPDATE %s SET %s WHERE %s' % (table,column_statement,query),values)

  def delete(self,table,query,values):
    self.cursor.execute('DELETE FROM %s WHERE %s' % (table,query),values)

  def insert(self,tabula,marks,values):
    self.cursor.execute('INSERT INTO %s %s' % (tabula,marks),values)

  def like_search(self,column,table,case,value):
    values = []
    for value_tuple in self.cursor.execute('SELECT %s FROM %s WHERE %s LIKE(?)' % (column,table,case),(value,)):
      values.append(value_tuple[0])
    return values