#TradeEnv#
from flask import Flask, session, url_for, request, render_template, jsonify, redirect
import os
import sqlite3 as sqlite
import update_stock
import encrypt
from DBmanager import dbManager as DBmanager

#Gets balance using username
def get_balance(username):
  try:
    userDB = sqlite.connect('userDB.db')
    udb = userDB.cursor()
    for balance in udb.execute('SELECT money FROM userTbl WHERE username=?',(username,)):
      balance = balance[0]
  finally:
    userDB.close()
  return round(balance,2)

#Gets stock ID using stock symbol
def get_stockID(stock_symbol):
  try:
    stockDB = sqlite.connect('stockDB.db')
    rdb = stockDB.cursor()
    for stockID_tuple in rdb.execute('SELECT stockID FROM stockTbl WHERE stockSymbol=?',(stock_symbol,)):
      stockID = stockID_tuple[0]
  finally:
    stockDB.close()
  return stockID

#Gets username using userID
def get_username(userID):
  try:
    userDB = sqlite.connect('userDB.db')
    udb = userDB.cursor()
    for username_tuple in udb.execute('SELECT username FROM userTbl WHERE userID=?',(userID,)):
      username = username_tuple[0]
  finally:
    userDB.close()
  return username

#Gets user ID using username
def get_userID(username):
  try:
    userDB = sqlite.connect('userDB.db')
    udb = userDB.cursor()
    for userID_tuple in udb.execute('SELECT userID FROM userTbl WHERE username=?',(username,)):
      userID = userID_tuple[0]
  finally:
    userDB.close()
  return userID
  
#Takes first item from each tuple in list of tuples  
def clean_list_tuples(list):
  clean_list = []
  for item in list:
    clean_list.append(item[0])
  return clean_list

class Bespoke_Form:
  def __init__(self,form):
    self.form = form

  #Checks if a key is in form, returns bool
  def check_form(self,key):
    try:
      self.form[key]
      return True
    except:
      return False
    
  #Processes purchase/sell form
  def process_transaction(self,stock_symbol,purchase):
    shares = int(request.form['shares'])
    balance = float(get_balance(session['Username']))
    if not purchase:

      #Gets the quantity of shares from said stock the user owns
      with DBmanager('userDB.db') as userDB:
        stockID = get_stockID(stock_symbol)
        shares_owned = userDB.get_value('sharesOwned','ownershipTbl','userID=? AND stockID=?',(session['User ID'],stockID))[0][0]

      #Ensures the user owns enough shares of the stock for their request
      if shares > shares_owned:
        return redirect(url_for('sell', stock_symbol=stock_symbol, error_type='q'))

      #Updates the stock data
      update_stock.update(stock_symbol)

      #Gets the bid price for the stock
      with DBmanager('stockDB.db') as stockDB:
        price = stockDB.get_value('bidPrice','stockTbl','stockSymbol=?',(stock_symbol,))[0][0]

      #Updates the database based on the volume of shares the user would like to sell
      bid = float(price)
      with DBmanager('userDB.db') as userDB:

        #Updates the amount of shares owned
        userDB.update('sharesOwned=?','ownershipTbl','userID=? AND stockID=?',(shares_owned-shares,session['User ID'],stockID))

        #Removes record if no shares are owned
        if shares_owned-shares==0:
          userDB.delete('ownershipTbl','userID=? AND stockID=?',(session['User ID'],stockID))

        #Updates user's balance
        userDB.update('money=?','userTbl','userID=?',(balance+(bid*shares),session['User ID']))

        #Inserts the new trade into the trade table
        userDB.insert('tradeTbl(userID,stockID,sharesPurchased,tradePrice)','VALUES(?,?,?,?)',(session['User ID'],stockID,-shares,-shares*bid))

      session['Recent Action'] = 'SHARES SOLD'
      session['Recency Ticker'] = 0
      return redirect(url_for('home'))
    else:
      shares = int(shares)
      update_stock.update(stock_symbol)

      #Gets the ask price for the stock
      with DBmanager('stockDB.db') as stockDB:
        price = stockDB.get_value('askPrice','stockTbl','stockSymbol=?',(stock_symbol,))[0][0]

      ask = float(price)
      if ask*shares > balance:
        #Returns error as user does not own have enough money in their balance
        return redirect(url_for('define_purchase', stock_symbol=stock_symbol, error_type='r'))

      #Grabs stockID
      stockID = get_stockID(stock_symbol)

      with DBmanager('userDB.db') as userDB:
        #Inserts the trade into the history of the trades performed on the site
        userDB.insert('tradeTbl(userID,stockID,sharesPurchased,tradePrice)','VALUES(?,?,?,?)',(session['User ID'],stockID,shares,shares*ask))

        #Gets the amount of shares the user owns
        shares_owned = userDB.get_value('sharesOwned','ownershipTbl','userID=? AND stockID=?',(session['User ID'],stockID))[0][0]

        #Sets user's balance to the correct amount after purchase
        userDB.update('money=?','userTbl','userID=?',(balance-(ask*shares),session['User ID']))

        #Checks whether the user owns shares
        if shares_owned != 0:

          #Updates database if they do
          userDB.update('sharesOwned=sharesOwned+?','ownershipTbl','userID=? AND stockID=?',(shares,session['User ID'],stockID))
        else:

          #Inserts new record if they don't
          userDB.insert('ownershipTbl(userID,stockID,sharesOwned)','VALUES(?,?,?)',(session['User ID'],stockID,shares))

      session['Recency Ticker'] = 0
      session['Recent Action'] = 'SHARES PURCHASED'

      #Redirects to home page
      return redirect(url_for('home'))
    
  def register(self):
    #Retrieve form data
    username = self.form['username']
    recovery_email = self.form['email']
    password = self.form['password']
    hashed = encrypt.encrypt_password(password)
    del password

    with DBmanager('userDB.db') as userDB:
      #Checks whether the username is already used
      if userDB.get_value('username','userTbl','username=?',(username,))[0][0] != 0:
        #Returns them to registry if it is
        return render_template('newregister.html', user = username)

      print(username,'being added to registered users')
      userDB.insert('userTbl(username,email,password,points,money)','VALUES(?,?,?,?,?)',(username,recovery_email,hashed,0,10000))

      session['User ID'] = userDB.get_value('userID','userTbl','username=?',(username,))[0][0]
      session['Username'] = username
    session['Recent Action'] = ''
    session['Recency Ticker'] = 0  
    return redirect(url_for('preferences'))

  def login(self):
    print('user logging in...')

    #retrieving form data
    username = self.form['username']
    password = self.form['password']

    with DBmanager('userDB.db') as userDB:
      hashed = userDB.get_value('password','userTbl','username=?',(username,))[0][0]
      #Checks whether the username exists
      if hashed == 0:
        #Returns to login if it doesn't
        return render_template('login.html', login_failed = True)
      #Checks whether password matches
      if encrypt.verify_password(password,hashed):
        #Logs in if it does
        session['Username'] = username
        print(session['Username'],'logging in')
        session['User ID'] = get_userID(username)
        session['Recency Ticker'] = 0
        session['Recent Action'] = ''
        return redirect(url_for('preferences'))
      #Returns to login if it doesn't
      print('login failed')
      return render_template('login.html', login_failed = True)
  
  def search(self,column,table):

    search = self.form['search']
    print(search)
    with DBmanager('userDB.db') as userDB:
      values = userDB.like_search(column,table,column,search+'%')
    return values
        

#Creates app object
app = Flask(__name__)

app.secret_key = b'\x89--\xdb\xdb\xb0g\xb6js-\x8d\x93\xabo\xc8' #secret_key to add extra data protection

##USER TREATMENT##
#Index
@app.route('/')
def index():
  try:
    if session['Username']: #Check if user has an account
      return redirect(url_for('home'))
  except:
    pass
  return render_template('newindex.html')

#Home
@app.route('/home')
def home():
  try :
    session['Username']
  except:
    return redirect(url_for('index'))
  #Upper procedure checks whether the recent action is new or old
  if session['Recency Ticker'] == 1:
    session['Recent Action'] = ''
    session['Recency Ticker'] = 0
  elif session['Recent Action'] != '':
    session['Recency Ticker'] = 1

  boards = []
  with DBmanager("stockDB.db") as stockDB:
    if session['High Capitalization']:
      boards.append({'List':stockDB.get_leaders('capitalization',True),'Param':'High Capitalization'})
    if session['High Beta']:
      boards.append({'List':stockDB.get_leaders('beta',True),'Param':'High Beta'})
    if session['Low Beta']:
      boards.append({'List':stockDB.get_leaders('beta',False),'Param':'Low Beta'})
    if session['High EPS']:
      boards.append({'List':stockDB.get_leaders('trailingEPS',True),'Param':'High EPS'})
    if session['High FEPS']:
      boards.append({'List':stockDB.get_leaders('forwardEPS',True),'Param':'High Forward EPS'})
    if session['High PE']:
      boards.append({'List':stockDB.get_leaders('trailingPE',True),'Param':'High PE'})
    if session['High FPE']:
      boards.append({'List':stockDB.get_leaders('forwardPE',True),'Param':'High Forward PE'})
  return render_template('home.html', user = session, boards=boards)

#Page for users to select which types of stocks 
@app.route('/register/preferences', methods=['POST','GET'])
def preferences():
  #If they aren't returning preferences
  if request.method != 'POST':
    return render_template('preferences.html', user=session)
  #If they are returning preferences
  form = Bespoke_Form(request.form)
  session['High Beta'] =  form.check_form('high_beta')
  session['High EPS'] = form.check_form('high_eps')
  session['Low Beta'] = form.check_form('low_beta')
  session['High Capitalization'] = form.check_form('high_cap')
  session['High PE'] = form.check_form('high_pe')
  session['High FEPS'] = form.check_form('high_feps')
  session['High FPE'] = form.check_form('high_fpe')
  return redirect(url_for('home'))

#Register page
@app.route('/register', methods=['POST','GET'])
def register():
  if request.method == 'POST':
    print('user attempting registry')
    
    form = Bespoke_Form(request.form)
    return form.register()
  else:
    return render_template('newregister.html')

#Login page
@app.route('/login', methods=['POST', 'GET'])
def login():
  if request.method == 'POST':
    form = Bespoke_Form(request.form)
    return form.login()
  else:
    return render_template('login.html', login_failed = False)


##FRIENDS AND LEAGUES##
#Friends page
@app.route('/friends', methods = ['POST', 'GET'])
def friends():
  with DBmanager('userDB.db') as userDB:
    usernames = []
    if request.method == 'POST':
      form = Bespoke_Form(request.form)
      usernames = form.search('username','userTbl')

    userIDs = userDB.get_value('userID','friendshipTbl','friendID=?',(session['User ID'],))[1]
    userIDs = clean_list_tuples(userIDs)

    pending_requestIDs = userDB.get_value('requesterID','friendRequestTbl','requesteeID=?',(session['User ID'],))[1]
    pending_requestIDs = clean_list_tuples(pending_requestIDs)

  for i in range(len(userIDs)):
    if userIDs[i] == session['User ID']:
        userIDs.pop(i)

  friends = []
  for user in userIDs:
    friends.append({'Username':get_username(user),'Balance':get_balance(get_username(user))})

  pending_requests = []
  for pending_requestID in pending_requestIDs:
    pending_requests.append(get_username(pending_requestID))

  return render_template('friends.html',user = session, friends = friends, usernames = usernames, pending_requests=pending_requests)

@app.route('/friends/<username>/accept')
def accept_friend(username):
  with DBmanager('userDB.db') as userDB:
    userDB.insert('friendshipTbl(friendID,userID)','VALUES(?,?)',(session['User ID'],get_userID(username)))
    userDB.insert('friendshipTbl(friendID,userID)','VALUES(?,?)',(get_userID(username),session['User ID']))
    userDB.delete('friendRequestTbl','requesterID=? AND requesteeID=?',(get_userID(username),session['User ID']))
  return redirect(url_for('friends'))
    
@app.route('/friends/<username>/request')
def friend_request(username):
  with DBmanager('userDB.db') as userDB:
    if not userDB.get_value('requesterID','friendRequestTbl','requesterID=? AND requesteeID=?',(session['User ID'],get_userID(username)))[0][0]:
      userDB.insert('friendRequestTbl(requesterID,requesteeID)','VALUES(?,?)',(session['User ID'],get_userID(username)))
  return redirect(url_for('friends'))

@app.route('/leagues', methods = ['POST','GET'])
def leagues():
  try:
    userDB = sqlite.connect('userDB.db')
    db = userDB.cursor()
    leagues_found = []
    if request.method == 'POST':
      search = request.form['search']
      for league_found_tuple in db.execute('SELECT leagueName, userID FROM leagueTbl WHERE leagueName LIKE(?)',(search+'%',)):
        league_found = {}
        league_found['League Name'] = league_found_tuple[0]
        league_found['Username'] = get_username(league_found_tuple[1])
        leagues_found.append(league_found)
    
    leagues = []
    for league_tuple in db.execute('SELECT leagueName,userID FROM leagueTbl WHERE leagueID=(SELECT leagueID FROM leagueIDTbl WHERE userID=?)',(session['User ID'],)):
      league = {}
      league['League Name'] = league_tuple[0]
      league['Username'] = get_username(league_tuple[0])

    pending_requests = []
    for request_tuple in db.execute('SELECT username FROM userTbl WHERE userID=(SELECT requesterID FROM leagueRequestTbl WHERE leagueID=(SELECT leagueID FROM leagueTbl WHERE userID=?))',(session['User ID'],)):
      pending_requests.append(request_tuple[0])
    
    user_league = []
    exists = False
    for user_league_tuple in db.execute('SELECT leagueName FROM leagueTbl WHERE userID=?',(session['User ID'],)):
      exists = True
      user_league.append(user_league_tuple[0])
  finally:
    userDB.close()
  return render_template('leagues.html', user=session, leagues_found = leagues_found, leagues = leagues, pending_requests=pending_requests, user_league = user_league, exists=exists)

@app.route('/leagues/<league>')
def league(league):
  with DBmanager('userDB.db') as userDB:
    leagueID = userDB.get_value('leagueID','leagueTbl','leagueName=?',(league,))[0][0]
    userIDs = userDB.get_value('userID','leagueIDTbl','leagueID=?',(leagueID,))[1]
    userIDs = clean_list_tuples(userIDs)
    users = []
  for userID in userIDs:
    user = {}
    user['Username'] = get_username(userID)
    user['Balance'] = get_balance(get_username(userID))
    users.append(user)
  users = sorted(users, key = lambda k: k['Balance'],reverse=True)
  return render_template('league.html',league=league,users=users)

@app.route('/leagues/<username>/accept')
def accept_leaguee(username):
  with DBmanager('userDB.db') as userDB:
    leagueID = userDB.get_value('leagueID','leagueTbl','userID=?',(session['User ID'],))[0][0]
    userDB.insert('leagueIDTbl(userID,leagueID)','VALUES(?,?)',(get_userID(username),leagueID))
    userDB.delete('leagueRequestTbl','requesterID=? AND leagueID=?',(get_userID(username),leagueID))

  return redirect(url_for('leagues'))

@app.route('/leagues/<league>/request')
def league_request(league):
  with DBmanager('userDB.db') as userDB:
    leagueID = userDB.get_value('leagueID','leagueTbl','leagueName=?',(league,))[0][0]
    #Checks if request already exists
    if not userDB.get_value('leagueID','leagueRequestTbl','leagueID=? AND requesterID=?',(leagueID,session['User ID']))[0][0]:
      userDB.insert('leagueRequestTbl(leagueID,requesterID)','VALUES(?,?)',(leagueID,session['User ID']))

  return redirect(url_for('leagues'))

@app.route('/leagues/create', methods = ['POST','GET'])
def create_league():
  league = request.form['name']
  userDB = sqlite.connect('userDB.db')
  db = userDB.cursor()

  try:
    league_exists = False
    for check in db.execute('SELECT leagueID FROM leagueTbl WHERE userID=?',(session['User ID'],)):
      league_exists = True

    if not league_exists:
      db.execute('INSERT INTO leagueTbl(leagueName,userID) VALUES(?,?)',(league,session['User ID']))
      userDB.commit()
  finally:
    userDB.close()
  return redirect(url_for('leagues'))


  
##STOCKS && PURCHASING##
#Stocks
@app.route('/stocks', methods=['POST','GET'])
def stocks():
  names = {'capitalization':'Capitalization','beta':'Beta','trailingEPS':'EPS','trailingPE':'PE'}
  if request.method != 'POST':
    with DBmanager('stockDB.db') as stockDB:
      stocks = stockDB.get_stocks_in_range(0,50,'stockName',False,'')
    return render_template('stocks.html', stocks = stocks, user = session, start = 0, end = 50, param = 'stockName', high = False,names=names)
  form = Bespoke_Form(request.form)
  with DBmanager('stockDB.db') as stockDB:
    high = form.check_form('high')
    if form.check_form('param'):
      stocks = stockDB.get_stocks_in_range(int(request.form['start']),int(request.form['end']),request.form['param'],high,request.form['search'])
      return render_template('stocks.html', stocks = stocks, user = session, start = int(request.form['start']), end = int(request.form['end']), param = request.form['param'], high = request.form['high'], search=request.form['search'],names=names)
    else:
      stocks = stockDB.get_stocks_in_range(int(request.form['start']),int(request.form['end']),'stockName',high,request.form['search'])
      return render_template('stocks.html', stocks = stocks, user = session, start = int(request.form['start']), end = int(request.form['end']), param = 'stockName', high = request.form['high'], search=request.form['search'],names=names)

#Individual stock page
@app.route('/stocks/<stock_symbol>')
def stock(stock_symbol):
  #Updates stock data
  update_stock.update(stock_symbol)

  #Attain data for stock page
  with sqlite.connect('stockDB.db') as stockDB:
    db = stockDB.cursor()

    #Gets stock data from database
    for stock_data in db.execute('SELECT * FROM stockTbl WHERE stockSymbol=?', (stock_symbol,)):
      stock = {}
      stock['Stock Name'] = stock_data[0]
      stock['Stock Symbol'] = stock_data[1]
      stock['ID'] = stock_data[2]
      stock['Summary'] = stock_data[3]
      stock['Website'] = stock_data[4]
      if stock['Website'] is None:
        stock['Website'] = False
      stock['Logo'] = stock_data[5]
      stock['Ask Price'] = stock_data[6]
      stock['Bid Price'] = stock_data[7]
      stock['Open Price'] = stock_data[8]
      if stock['Ask Price'] == 0:
        stock['Ask Price'] = stock['Bid Price']
        with DBmanager('stockDB.db') as sDB:
          sDB.update('bidPrice=?','stockTbl','stockSymbol=?',(stock['Bid Price'],stock['Stock Symbol']))
      stock['Previous Close'] = stock_data[9]
      stock['Daily Low'] = stock_data[10]
      stock['Daily High'] = stock_data[11]
      stock['52 Week Low'] = stock_data[12]
      stock['52 Week High'] = stock_data[13]
      try:
        stock['Capitalization'] = int(stock_data[14])
      except:
        stock['Capitalization'] = 'N/A'
      try:
        stock['Volume'] = int(stock_data[15])
      except:
        stock['Volume'] = 'N/A'
      try:
        stock['Avg Volume'] = int(stock_data[16])
      except:
        stock['Avg Volume'] = 'N/A'
      stock['Dividend'] = stock_data[18]
      stock['5 Yr Dividend'] = stock_data[19]
      stock['Beta'] = stock_data[20]
      stock['Trailing EPS'] = stock_data[21]
      stock['Forward EPS'] = stock_data[22]
      stock['Trailing PE'] = stock_data[23]
      stock['Forward PE'] = stock_data[24]
      stock['Consensus Rating'] = stock_data[25]
      stock['Consensus Rating Score'] = stock_data[26]
      stock['Consensus Price Target'] = stock_data[27]
      stock['Price Target Upside'] = stock_data[28]
      stock['Last Updated'] = stock_data[29]

    #Redirecting through ID tables
    for sector_id_tuple in db.execute('SELECT sectorID FROM sectorIDTbl WHERE stockID=?', (stock['ID'],)):
      sector_id = sector_id_tuple[0]

    #Gets sectors
    sectors = []
    for sector_name_tuple in db.execute('SELECT sectorName FROM sectorTbl WHERE sectorID=?', (sector_id,)):
        sectors.append(sector_name_tuple[0])
    stock['Sectors'] = sectors

    db.execute('SELECT AVG(trailingPE) FROM stockTbl WHERE stockID=(SELECT stockID FROM sectorIDTbl WHERE sectorID=?)',(sector_id,))
    avg_pe = db.fetchone()[0]
    db.execute('SELECT AVG(forwardPE) FROM stockTbl WHERE stockID=(SELECT stockID FROM sectorIDTbl WHERE sectorID=?)',(sector_id,))
    avg_fpe = db.fetchone()[0]

    #Standard Deviation calculations
    sPEsq = 0
    sFPEsq = 0
    sPEsq_counter = 0
    sFPEsq_counter = 0
    for values in db.execute('SELECT trailingPE,forwardPE FROM stockTbl WHERE stockID=(SELECT stockID FROM sectorIDTbl WHERE sectorID=?)',(sector_id,)):
      if values[0] != None:
        sPEsq += float(values[0])**2
        sPEsq_counter += 1
      if values[1] != None:
        sFPEsq += float(values[1])**2
        sFPEsq_counter += 1
    sdPE = 0
    sdFPE = 0
    if sPEsq_counter != 0:
      sdPE = ((sPEsq/sPEsq_counter)-((avg_pe)**2))**0.5
    if sFPEsq_counter != 0:
      sdFPE = ((sFPEsq/sFPEsq_counter)-((avg_fpe)**2))**0.5
    if stock['Trailing PE'] != None and sdPE != 0:
      sdsPE = (stock['Trailing PE']-avg_pe)/sdPE
    else:
      sdsPE = None
    if stock['Forward PE'] != None and sdFPE != 0:
      sdsFPE = (stock['Forward PE']-avg_fpe)/sdFPE
    else:
      sdsFPE = None

  return render_template('stock.html', stock = stock, user = session, sdsPE=sdsPE,sdsFPE=sdsFPE)

#Tracks stock
@app.route('/stocks/<stock_symbol>/track')
def track(stock_symbol):
  #Checks if user is logged in
  try:
    session['Username']
  except:
    return render_template('account_needed.html')

  #Gets stock ID
  stockID = get_stockID(stock_symbol)

  #Checks if user already has stock in their tracking database
  with sqlite.connect('userDB.db') as userDB:
    db = userDB.cursor()
    for stock in db.execute('SELECT stockID FROM trackingTbl WHERE userID=? AND stockID=?',(session['User ID'],stockID)):
      return redirect(url_for('stock', stock_symbol=stock_symbol))

    #Inserts stock into users tracked stocks in database if not already tracked
    db.execute('INSERT INTO trackingTbl(userID,stockID) VALUES(?,?)',(session['User ID'],stockID))
  return redirect(url_for('stock',stock_symbol=stock_symbol))

#Purchase stock
@app.route('/purchase/<stock_symbol>/<error_type>')
def define_purchase(stock_symbol, error_type):
  #Checks if user is logged in
  try:
    session['Username']
  except:
    return render_template('account_needed.html')

  #If user is logged in
  if error_type == 'b':
    error_statement = ''
  elif error_type == 'q':
    error_statement = 'Must be integer value'
  else:
    error_statement = 'Balance too low'
  #^Checks if there is an error, and the type

  #Updates stock data for latest time
  update_stock.update(stock_symbol)

  #Gets stock symbol and ask price for page
  with sqlite.connect('stockDB.db') as stockDB:
    db = stockDB.cursor()
    for ask_price_tuple in db.execute('SELECT askPrice FROM stockTbl WHERE stockSymbol=?', (stock_symbol,)):
      stock = {}
      stock['Stock Symbol'] = stock_symbol
      stock['Ask Price'] = ask_price_tuple[0]
  
  #Gets the user's balance
  balance = get_balance(session['Username'])
  return render_template('purchase.html', stock = stock, balance = balance, error_statement = error_statement)

#Verify purchase
@app.route('/purchase/<stock_symbol>/<balance>/<ask>', methods = ['POST'])
def check_purchase(stock_symbol, balance, ask):
  #Gets the amount of shares the user would like to purchase
  shares = request.form['shares']
  form = Bespoke_Form(request.form)
  return(form.process_transaction(stock_symbol,True))
  


##PORTFOLIO && SELLING##
#Portfolio
@app.route('/portfolio')
def portfolio():
  #Checks the user has an account
  try:
    session['Username']
  except:
    return render_template('account_needed.html')

  with sqlite.connect('userDB.db') as userDB:
    db = userDB.cursor()
    stockIDs = []
    shares = []
    #Retrieves the stocks the user owns shares in
    for stockID_tuple in db.execute('SELECT stockID, sharesOwned FROM ownershipTbl WHERE userID=?',(session['User ID'],)):
      stockIDs.append(stockID_tuple[0])
      shares.append(stockID_tuple[1])

    #Retrieves the user's balance
    balance = get_balance(session['Username'])

  with sqlite.connect('stockDB.db') as stockDB:
    db = stockDB.cursor()
    stocks = []

    #Retrieves data for each stock the user owns shares in
    for i in range(len(stockIDs)):
      for stock_data_tuple in db.execute('SELECT stockName, askPrice, bidPrice, stockSymbol FROM stockTbl WHERE stockID=?',(stockIDs[i],)):
        stock = {}
        stock['Name'] = stock_data_tuple[0]
        stock['Ask'] = stock_data_tuple[1]
        stock['Bid'] = stock_data_tuple[2]
        stock['Symbol'] = stock_data_tuple[3]
        stock['Shares'] = shares[i]
        stocks.append(stock)
  return render_template('portfolio.html', stocks=stocks, balance=balance, user=session)

#Tracking
@app.route('/tracking')
def tracking():
  #Retrieve stocks the user is tracking
  with sqlite.connect('userDB.db') as userDB:
    udb = userDB.cursor()

    #Get stock IDs for stocks user tracks
    stockIDs = []
    for stockID_tuple in udb.execute('SELECT stockID FROM trackingTbl WHERE userID=?',(session['User ID'],)):
      stockIDs.append(stockID_tuple[0])

  balance = get_balance(session['Username'])
  with sqlite.connect('stockDB.db') as stockDB:
    db = stockDB.cursor()

    #Get data for each stock
    stocks = []
    for i in range(len(stockIDs)):
      for stock_data in db.execute('SELECT stockName, forwardEPS, trailingEPS, bidPrice, askPrice, stockSymbol FROM stockTbl WHERE stockID=?',(stockIDs[i],)):
        stock = {}
        stock['Stock Symbol'] = stock_data[5]
        stock['Stock Name'] = stock_data[0]
        stock['Forward EPS'] = stock_data[1]
        stock['Trailing EPS'] = stock_data[2]
        stock['Bid Price'] = stock_data[3]
        stock['Ask Price'] = stock_data[4]
        stocks.append(stock)
  return render_template('tracking.html', balance=balance, stocks=stocks, user=session)

#Untracking
@app.route('/tracking/untrack/<stock_symbol>')
def untrack(stock_symbol):
  stockID = get_stockID(stock_symbol)
  with DBmanager('userDB.db') as userDB:
    userDB.delete('trackingTbl','stockID=? AND userID=?',(stockID,session['User ID']))
  return redirect(url_for('tracking'))

#Selling
@app.route('/sell/<stock_symbol>/<error_type>')
def sell(stock_symbol,error_type):
  #Checks whether there's an error, and if so its type
  if error_type == 'b':
    error = ''
  elif error_type == 'q':
    error = "You don't own enough shares to sell this value"
  else:
    error = 'This must be an integer value'

  #Updates stock data
  update_stock.update(stock_symbol)
  
  #Get user's balance
  balance = get_balance(session['Username'])

  #Gets relevant stock data
  with sqlite.connect('stockDB.db') as stockDB:
    db = stockDB.cursor()
    stock = {}
    for stock_data_tuple in db.execute('SELECT stockName, askPrice, bidPrice, lastUpdated FROM stockTbl WHERE stockSymbol=?',(stock_symbol,)):
      stock['Stock Symbol'] = stock_symbol
      stock['Name'] = stock_data_tuple[0]
      stock['Ask Price'] = stock_data_tuple[1]
      stock['Bid Price'] = stock_data_tuple[2]
      stock['Last Updated'] = stock_data_tuple[3]
  return render_template('sell.html', stock=stock, balance=balance, user=session, error=error)

#Verify sell
@app.route('/sell/<stock_symbol>/<balance>/<bid>', methods = ['POST'])
def check_sell(stock_symbol, balance, bid):
  #Requests the quantity of shares the user would like to sell
  form = Bespoke_Form(request.form)
  return(form.process_transaction(stock_symbol,False))


app.run(host='0.0.0.0', port=8080)