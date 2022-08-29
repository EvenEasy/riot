import sqlite3

class basedata:

    def __init__(self, file_name):
        self.connection = sqlite3.connect(file_name)
        self.cursor = self.connection.cursor()

    def registration_user(self,user_id, username, user_lol_id, region):
        with self.connection:
            return self.cursor.execute(f"INSERT INTO Users VALUES ({user_id}, '{username}', '{user_lol_id}', '{region}', 0, 0, 0, 1, 0, 0)")
    def get_lol_id(self, user_id):
        with self.connection:
            try:
                return self.cursor.execute(f"SELECT user_lol_id, region FROM Users WHERE user_id = {user_id}").fetchmany(1)[0]
            except IndexError:
                return "error"
    def get_balance(self, user_id):
        with self.connection:
            try:
                return self.cursor.execute(f"SELECT gold, cristal, trunks, sphere FROM Users WHERE user_id = {user_id}").fetchmany(1)[0]
            except IndexError:
                return "error"
                
    def update_balance(self, user_id,gold, crystal):
        with self.connection:
            try:
                return self.cursor.execute(f"UPDATE Users SET gold={gold}, cristal={crystal} WHERE user_id = {user_id}")
            except IndexError:
                return "error"
    def sqlite(self, sqlcode : str):
        try:
            with self.connection:
                return (self.cursor.execute(sqlcode).fetchall())
        except Exception as E:
            print(f"ERROR - {E}")
            return f"Error - {E}"

    def isReg(self, user_id):
        with self.connection:
            try:
                return self.cursor.execute(f"SELECT user_id FROM Users WHERE user_id = {user_id}").fetchmany(1) != []
            except IndexError:
                return "error"


    def readQueue(self):
        with open("queue_game.txt", 'r') as file:
            return [tuple(line.replace("\n", "").split(" ")) for line in file.readlines()]
    def readQueueByGameType(self, type_game):
        with open("queue_game.txt", 'r') as file:
            return [tuple(line.replace("\n", "").split(" ")) for line in file.readlines() if type_game in line.replace("\n", "")]

    def del_user_from_queue(self, user_id_list : list):
        with open("queue_game.txt", 'r+') as file:
            fp = file.readlines()
            file.seek(0)
            file.truncate()
            for line in fp:
                user = line.replace("\n", "").split(" ")[0]
                print(str(user), str(user) not in user_id_list, user_id_list)
                if str(user) not in user_id_list:
                    file.write(line)

    def isInQueue(self, user_id):
        with open("queue_game.txt", 'r') as file:
            return str(user_id) in file.read()
    def addToQueue(self, user_id, type, team_size = 5):
        with open("queue_game.txt", 'a') as file:
            return file.write(f"{user_id} {type} {team_size}\n")