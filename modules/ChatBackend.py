from objects.MyMessage import MyMessage as MyMsg
from objects.Client import Client
from modules.GenerateID import GenerateUniqueID
import logging
import json
import datetime
import sqlite3
import base64
logging.basicConfig(filename='chat_activity.log', level=logging.INFO,
                        format='[%(asctime)s]:[%(levelname)s]:[%(message)s]')

clients = {} #:(websocket:name)
clientsNotification = [] #istemciye gönderilecek liste
activeClientsList = []

#--------------------------------------------CHAT OPERATIONS---------------------------------------------------------------
async def start_chat(websocket,name):

    print("Chat başlangıç")
    # chat başlangıç.
    await sayClientWelcome(websocket, name)

    _client = Client(name, "{}".format(GenerateUniqueID()), "online", True, websocket)
    activeClientsList.append(_client)
    clients[websocket] = {"name": name, "user_ID": _client.userID}
    clientsNotification.append({"username": name, "user_ID": "{}".format(_client.userID), "status": _client.status})
    print('({} existing clients)'.format(len(clients)))
    print("[LAST CONNECTED]")
    _client.showInfo()  # Dahil olan istemcinin bilgileri ekrana yazdırılıyor.
    logging.basicConfig(filename='chat_activity.log', level=logging.INFO,
                        format='[%(asctime)s]:[%(levelname)s]:[%(message)s]')
    logging.info('Client connected the chat room : [{}] - [{}] - [{}] - [{}] - [{}] '.format(_client.username,_client.userID,_client.status,_client.connected,_client.relatedSocket))
    print("--------------------------------------------")
    await notify_usersInfo(activeClientsList,
                           clientsNotification,
                           _client)  # Odada bulunan kullanıcıların isim ve id bilgileri.
    await notify_usersNumber(activeClientsList,
                             websocket)  # Odada bulunan kullanıcıların sayısı(Keyfi bir bildirim,olmasa da olur.)
    print("Connection added:{}".format(clients[websocket]))
    print("--------------------------------------------")
    showClients(clients)
    print("--------------------------------------------")
    await notify_New_User(activeClientsList, _client)
    await sendLastData(websocket, name, "group_message")
    while True:
        incoming_data = await websocket.recv()  # Mesajlaşmanın başladığı yer.
        incoming_data_json = json.loads(incoming_data)  # C#'tan gelen Message sınıfı parse ediliyor.
        print("{}".format(incoming_data_json))
        message = incoming_data_json['message']  # Gelen veriden mesaj bilgisi ayrılıyor.
        message_type = incoming_data_json['message_type']
        _from = incoming_data_json['_from']
        _to = incoming_data_json['_to']

        if (message_type == "exit"):
            print('Client closed connection:[{}]'.format(name))
            print("[DISCONNECTED]")
            _client.showInfo()
            print("-------------------------------------------------------------------")
            del clients[websocket]
            clientsNotification.remove(
                {"username": name, "user_ID": "{}".format(_client.userID), "status": _client.status})
            activeClientsList.remove(_client)
            _client.status = "offline"
            logging.info('Client closed connection : [{}] - [{}] - [{}] - [{}] - [{}] '.format(_client.username, _client.userID,
                                                                                     _client.status, _client.connected,
                                                                                     _client.relatedSocket))
            await notify_Leaving_User(activeClientsList, _client)

            await notify_usersInfo(activeClientsList, clientsNotification,
                                   _client)  # Odada bulunan kullanıcıların isim ve id bilgileri.
            await websocket.close()
            return -1
        elif (message_type == "directed-message"):
            directedMessage = MyMsg(message_type,
                                    "{},{},{}".format(name, _client.userID, _client.status),
                                    _to,
                                    "{}:{}".format(name, message),
                                    datetime.datetime.utcnow().isoformat() + "Z")
            directedMessage_JSON = json.loads(json.dumps(directedMessage.__dict__))
            for client in activeClientsList:
                print("Target client:")
                if (_to == client.userID):
                    print("Target client's uid:{}".format(client.userID))
                    await client.relatedSocket.send("{}".format(directedMessage_JSON))
                    print("FROM : [{}] TO : [{}] MESSAGE : [{}] MESSAGE_TYPE : [{}]".format(name, _to, message, message_type))
                    logging.info('FROM : [{}] TO : [{}] MESSAGE : [{}] MESSAGE_TYPE : [{}]'.format(name, _to, message, message_type))
                else:
                    continue

        elif (message_type == "broadcast"):

            for client, _ in clients.items():
                if client != _client:
                    messageToAllUsers = MyMsg("broadcast",
                                              "server",
                                              "everyone",
                                              "{}: {}".format(_client.username, message),
                                              datetime.datetime.utcnow().isoformat() + "Z")
                    messageToAllUsers_JSON = json.loads(json.dumps(messageToAllUsers.__dict__))
                    await client.send("{}".format(messageToAllUsers_JSON))

                    await logMessageDatabase("group_message",_client.username,message)

                    logging.info('FROM : {} TO : {} MESSAGE : {} MESSAGE_TYPE : {}'.format(_client.username,
                                                                                           messageToAllUsers._to,
                                                                                           message,
                                                                                           message_type))
                    print('FROM : {} TO : {} MESSAGE : {} MESSAGE_TYPE : {}'.format(_client.username,
                                                                                           messageToAllUsers._to,
                                                                                           message,
                                                                                           message_type))
                # await client.send("{}: {}".format(_client.username, incoming_data_json['message']))

        # if message is None:
        # their_name = clients[websocket]
        # del clients[websocket]
        # print('Client closed connection:', websocket)
        # for client, _ in clients.items():
        # await client.send(their_name + 'has left the chat')
        # break

        # Send message to all clients
        # for client, _ in clients.items():
        # await client.send("{}: {}".format(name,message))

    else:
        logging.error('Değerlendirmeye açık olmayan bir mesaj geldi:{}'.format(incoming_data_json))
        print("Gelen mesajı değerlendirme özelliği yok.")
#--------------------------------------------------CHAT OPERATONS-----------------------------------------------------------------





async def logMessageDatabase(type,nick,message):
    con = sqlite3.connect("websocketchat.db")
    cursor = con.cursor()
    sqlCreate = "CREATE TABLE IF NOT EXISTS lastData (type TEXT, data TEXT)"
    cursor.execute(sqlCreate)
    #con.commit()
    sqlPop = "SELECT * FROM lastData WHERE type = '{}'".format(type)
    cursor.execute(sqlPop)
    result = cursor.fetchall()
    print("[logMessageDatabase]:{}".format(result[0][1]))
    lastData = result[0][1] + "{}:{}\n".format(nick, message)
    sqlPush = "UPDATE lastData SET data = '{}' WHERE type='{}'".format(lastData,type)
    cursor.execute(sqlPush)
    con.commit()
    con.close()
    #pass



#---------------------------------------NOTIFY OPERATIONS------------------------------------------------------

def showClients(clients):
    if(clients):
        print("Active Users:")
        for client, _ in clients.items():
            print("-->", clients[client])

async def sayClientWelcome(websocket,name):
    welcomeMsg = "Welcome to chatroom, {}".format(name)
    connectionEstablishedMsg = MyMsg("welcome-message",
                                     "server",
                                     name,
                                     welcomeMsg,
                                     datetime.datetime.utcnow().isoformat() + "Z")
    connectionEstablishedMsg_JSON = json.loads(json.dumps(connectionEstablishedMsg.__dict__))
    await websocket.send("{}".format(connectionEstablishedMsg_JSON))


async def notify_usersInfo(activeClientsList,clientsNotificationList,_client):
    if clientsNotificationList:
        onlineClientsMsg = MyMsg("online-clients",
                             "server",
                             _client.username,
                             format(clientsNotificationList),  # çevrimiçi kullanıcılar koyulacak.
                             datetime.datetime.utcnow().isoformat() + "Z")
        onlineClientsMsg_JSON = json.loads(json.dumps(onlineClientsMsg.__dict__))
    for client in activeClientsList:
        await client.relatedSocket.send("{}".format(onlineClientsMsg_JSON))  # Online kullanıcılar bildiriliyor.


async def notify_usersNumber(activeClientsList,websocket):
    if (len(activeClientsList) != 0):  # Son bağlanan kullanıcıdan başka kullanıcı varsa
        notificationConnectedUsers = MyMsg("directed-message",
                                           "server",
                                           "everyone",
                                           'There are {} other users connected.'.format(len(activeClientsList) - 1),
                                           datetime.datetime.utcnow().isoformat() + "Z")
        notificationConnectedUsers_JSON = json.loads(json.dumps(notificationConnectedUsers.__dict__))

        await websocket.send(
            "{}".format(notificationConnectedUsers_JSON))  # Çevrimiçi kullanıcı yoksa mesaj olarak bildiriliyor.


async def sendLastData(websocket,username, message_type):
    con = sqlite3.connect("websocketchat.db")
    cursor = con.cursor()
    sql = "SELECT * FROM lastData WHERE type = '{}'".format("group_message")
    cursor.execute(sql)
    result = cursor.fetchall()
    print("[sendLastData]:The result is : {}".format(result))
    msgLastData = MyMsg("last-data",
                        "server",
                        "{}".format(username),
                        "{}".format(result[0][1]),
                        datetime.datetime.utcnow().isoformat() + "Z")
    msgLastData_JSON = json.loads(json.dumps(msgLastData.__dict__))
    await websocket.send("{}".format(msgLastData_JSON))



async def notify_New_User(activeClientsList,_client):
    for client in activeClientsList:
        notificationConnected = MyMsg("broadcast",
                      "server",
                      "everyone",
                      _client.username + ' has joined the chat',
                      datetime.datetime.utcnow().isoformat() + "Z")
        notificationConnected_JSON = json.loads(json.dumps(notificationConnected.__dict__))
        await client.relatedSocket.send("{}".format(notificationConnected_JSON))



async def notify_Leaving_User(activeClientsList,_client):
    for client in activeClientsList:
        notificationLeaving = MyMsg("broadcast",
                                    "server",
                                    "everyone",
                                    _client.username + ' has lefted from chat.',
                                    datetime.datetime.utcnow().isoformat() + "Z")
        notificationLeaving_JSON = json.loads(json.dumps(notificationLeaving.__dict__))
        await client.relatedSocket.send("{}".format(notificationLeaving_JSON))



#-----------------------------------------------LOGIN OPERATIONS------------------------------------------------------------
def verify_chatroom_key(username,chatRoomKey,tableName):
    con = sqlite3.connect("websocketchat.db")
    cursor = con.cursor()
    sql = "SELECT * FROM {} WHERE nick = '{}' AND chatRoomKey = '{}'".format(tableName,username,chatRoomKey)
    cursor.execute(sql)
    results = cursor.fetchall()
    if results:
        print("Chat room key verified:{}".format(chatRoomKey))
        response = MyMsg("login-success",
                              "server",
                              "user",
                              "Chatroom key verified.",
                              datetime.datetime.utcnow().isoformat() + "Z")
        response_JSON = json.loads(json.dumps(response.__dict__))
        return (True,response_JSON)
    else:
        response = MyMsg("chatroom-key-failed",
                         "server",
                         "user",
                         "Chatroom key does'nt verified.",
                         datetime.datetime.utcnow().isoformat() + "Z")
        response_JSON = json.loads(json.dumps(response.__dict__))
        return (False,response_JSON)

#login_success
def login_success(username):
    username_bytes = username.encode('ascii')
    base64_bytes = base64.b64encode(username_bytes)
    base64_message = base64_bytes.decode('ascii')
    chatRoomKey = base64_message
    print("Chat room key for {} : {}".format(username,chatRoomKey))
    loginResponse = MyMsg("login-success",
                           "server",
                           "user",
                           "Giriş başarılı.,{}".format(chatRoomKey),
                                                datetime.datetime.utcnow().isoformat() + "Z")
    loginResponse_JSON = json.loads(json.dumps(loginResponse.__dict__))
    return loginResponse_JSON

    pass
#loginFailed
def login_failed():
    loginResponse = MyMsg("login-fail",
                          "server",
                          "user",
                          "Yanlış kullanıcı adı veya şifre.",
                                                datetime.datetime.utcnow().isoformat() + "Z")
    loginResponse_JSON = json.loads(json.dumps(loginResponse.__dict__))
    return loginResponse_JSON


#loginVerification
def login_verification(userData,tableName):
    con = sqlite3.connect("websocketchat.db")
    cursor = con.cursor()
    logging.basicConfig(filename='chat_activity.log', level=logging.INFO,
                        format='[%(asctime)s]:[%(levelname)s]:[%(message)s]')
    username = userData[2]
    password = userData[4]
    sql = "SELECT * FROM {} WHERE nick = '{}' AND sifre = '{}'".format(tableName,username,password)
    cursor.execute(sql)
    results = cursor.fetchall()
    if results:
        loginResponse = login_success(username)
        logging.info('Login success.USERNAME : {}'.format(username))
        return (True,loginResponse)
    else:
        loginResponse = login_failed()
        logging.error('Login failed.USERNAME : {}'.format(username))
        return (False,loginResponse)





def addUserToDatabase(userData,tableName):
    con = sqlite3.connect("websocketchat.db")
    cursor = con.cursor()
    createTable(tableName,con,cursor)
    name = userData[0]
    surname = userData[1]
    username = userData[2] #dikkat
    mail = userData[3] #dikkat
    password = userData[4]
    gender = userData[5]
    username_bytes = username.encode('ascii')
    base64_bytes = base64.b64encode(username_bytes)
    chatRoomKey = base64_bytes.decode('ascii') #kullanıcı sohbet odasına girerken veritabanındaki bu bilgi kontrol edilecek.yani chat başlangıç yeri
    # birthday = userData[6]
    sqlMailControl = "SELECT * FROM {} WHERE mail = '{}' ".format(tableName,mail)
    sqlUserNameControl = "SELECT * FROM {} WHERE nick = '{}' ".format(tableName,username)
    cursor.execute(sqlMailControl)
    resultMail = cursor.fetchall()
    cursor.execute(sqlUserNameControl)
    resultUserName = cursor.fetchall()
    logging.basicConfig(filename='chat_activity.log', level=logging.INFO,
                        format='[%(asctime)s]:[%(levelname)s]:[%(message)s]')
    logging.info('Received sign-up request : NAME:{} SURNAME:{} USERNAME:{} '
                 'MAIL:{} PASSWORD:{} GENDER:{}'.format(name,surname,username,mail,password,gender))
    if(resultUserName):
        signUpResponse = MyMsg("fail-username",
                                      "server",
                                      "new-user",
                                      "Kullanıcı adı uygun değil.",
                                      datetime.datetime.utcnow().isoformat() + "Z")
        signUpResponse_JSON = json.loads(json.dumps(signUpResponse.__dict__))
        logging.error('Invalid username for:{}. Request denied.'.format(username))
        return signUpResponse_JSON
    elif(resultMail):
        signUpResponse = MyMsg("fail-mailadress",
                               "server",
                               "new-user",
                               "Mail adresi uygun değil.",
                               datetime.datetime.utcnow().isoformat() + "Z")
        signUpResponse_JSON = json.loads(json.dumps(signUpResponse.__dict__))
        logging.error('Invalid mail adress for:{}. Request denied.'.format(mail))
        return signUpResponse_JSON
    else:
        sql = "INSERT INTO {} VALUES ('{}','{}','{}','{}','{}','{}', '{}')".format(tableName,name,surname,username,mail,password,gender,chatRoomKey)
        cursor.execute(sql)
        con.commit()
        signUpResponse = MyMsg("sign-up-success",
                               "server",
                               "new-user",
                               "Kayıt işlemi başarılı.",
                               datetime.datetime.utcnow().isoformat() + "Z")
        signUpResponse_JSON = json.loads(json.dumps(signUpResponse.__dict__))
        logging.info('Sign up success.New user added to database.USERNAME : {} MAIL : {}'.format(username,mail))
        return signUpResponse_JSON
        con.close()



def createTable(tableName,con,cursor):
    cursor.execute("CREATE TABLE IF NOT EXISTS {} (ad TEXT,soyad TEXT,nick TEXT,mail TEXT,sifre TEXT,cinsiyet TEXT,chatRoomKey TEXT)".format(tableName))
    con.commit()

