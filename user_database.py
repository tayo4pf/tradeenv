import sqlite3 as sqlite
#//USERDATA//
#Constructing the database
userDB = sqlite.connect('userDB.db')
db = userDB.cursor()

commands = []
#Constructs user table
commands.append("""
  PRAGMA foreign_keys = ON;
  CREATE TABLE IF NOT EXISTS userTbl
  (
    username TEXT NOT NULL,
    userID INTEGER PRIMARY KEY NOT NULL,
    email TEXT,
    password VARBINARY NOT NULL,
    money FLOAT NOT NULL,
    buddyName TEXT,
    buddyID INTEGER
  );
""")

#Constructs league table
commands.append("""
  PRAGMA foreign_keys = ON;
  CREATE TABLE IF NOT EXISTS leagueTbl
  (
    leagueName TEXT NOT NULL,
    userID INTEGER NOT NULL,
    leagueID INTEGER PRIMARY KEY NOT NULL,
    FOREIGN KEY(userID) REFERENCES userTbl(userID)
  );
""")

#Constructs leagueIDTbl
commands.append("""
  PRAGMA foreign_keys = ON;
  CREATE TABLE IF NOT EXISTS leagueIDTbl
  (
    leagueID INTEGER NOT NULL,
    userID INTEGER NOT NULL,
    primary key(userID, leagueID),
    FOREIGN KEY(leagueID) REFERENCES leagueTbl(leagueID),
    FOREIGN KEY(userID) REFERENCES userTbl(userID)
  )
""")

#Constructs trade table
commands.append("""
  PRAGMA foreign_keys = ON;
  CREATE TABLE IF NOT EXISTS tradeTbl
  (
    tradeID INTEGER PRIMARY KEY,
    userID INTEGER NOT NULL,
    stockID INTEGER NOT NULL,
    sharesPurchased INTEGER NOT NULL,
    tradePrice FLOAT NOT NULL,
    dateMade TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY(userID) REFERENCES userTbl(userID)
  )
""")

#Constructs ownership table
commands.append("""
  PRAGMA foreign_keys = ON;
  CREATE TABLE IF NOT EXISTS ownershipTbl
  (
    userID INTEGER NOT NULL,
    stockID INTEGER NOT NULL,
    sharesOwned INTEGER NOT NULL,
    primary key(userID, stockID),
    FOREIGN KEY(userID) REFERENCES userTbl(userID)
  )
""")

#Constructs tracking table
commands.append("""
  PRAGMA foreign_keys = ON;
  CREATE TABLE IF NOT EXISTS trackingTbl
  (
    userID INTEGER NOT NULL,
    stockID INTEGER NOT NULL,
    primary key(userID, stockID),
    FOREIGN KEY(userID) REFERENCES userTbl(userID)
  )
""")

#Constructs friendship table
commands.append("""
  PRAGMA foreign_keys = ON;
  CREATE TABLE IF NOT EXISTS friendshipTbl
  (
    userID INTEGER NOT NULL,
    friendID INTEGER NOT NULL,
    primary key(userID, friendID),
    FOREIGN KEY(userID) REFERENCES userTbl(userID),
    FOREIGN KEY(friendID) REFERENCES userTbl(userID)
  )
""")

#Constructs friend request table
commands.append("""
  PRAGMA foreign_keys = ON;
  CREATE TABLE IF NOT EXISTS friendRequestTbl
  (
    requesterID INTEGER NOT NULL,
    requesteeID INTEGER NOT NULL,
    primary key(requesterID, requesteeID),
    FOREIGN KEY(requesterID) REFERENCES userTbl(userID),
    FOREIGN KEY(requesteeID) REFERENCES userTbl(userID)
  )
""")

#Constructs league request table
commands.append("""
  PRAGMA foreign_keys = ON;
  CREATE TABLE IF NOT EXISTS leagueRequestTbl
  (
    requesterID INTEGER NOT NULL,
    leagueID INTEGER NOT NULL,
    FOREIGN KEY(requesterID) REFERENCES userTbl(userID),
    FOREIGN KEY(leagueID) REFERENCES leagueTbl(leagueID)
  )
""")
print('Constructing...')
for command in commands:
  userDB.executescript(command)
  userDB.commit()

userDB.close()
print("Tables constructed")