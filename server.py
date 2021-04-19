from modules.ChatBackend import *
from modules.GenerateID import GenerateUniqueID
from objects.MyMessage import MyMessage as MyMsg
from objects.Client import Client
import datetime
import asyncio


#Geliştiriciye öneri:Mesajları her zaman oluşturduğum MyMessage classını referans alarak gönder.
#Çünkü C# tarafında da aynı niteliklere sahip class var.aksi halde json parse işleminde sıkıntı oluyor.
#-Berkay Özkarhan


#The set of clients connected to this server.It is used to distribute messages


@asyncio.coroutine
async def client_handler(websocket,path):
    #_server = Client("server",1, "online", True,websocket)
    print("New Client ",websocket)
    print('({} existing clients)'.format(len(clients)))
    #İstemciden gelen ilk data ismi olarak belirlendi.
    first_data = await websocket.recv() #ilk mesajın geleceği yer istemcideki FirstMessage sınıfı
    first_data_json = json.loads(first_data) #JSON verisi-->Python verisi
    if(first_data_json['message_type'] == "sign-up"):
        #print("{}".format(first_data))
        new_user_Data = first_data_json['message'].split(",")
        signupResponse = addUserToDatabase(new_user_Data,"kullanıcılar")
        await websocket.send("{}".format(signupResponse))
        #await websocket.close()
        return -1

    elif(first_data_json['message_type'] == "login"):
        userData = first_data_json['message'].split(",") #userData[2]:nickname,userData[4]:password
        verification = login_verification(userData, "kullanıcılar")
        if(verification[0]):
            print("Giriş Başarılı.({})".format(verification[0]))
            loginSucceedResponse = verification[1]
            await websocket.send("{}".format(loginSucceedResponse))
            #await websocket.close_connection()
            return -1
        else:
            print("Giriş Başarısız.Yanlış Kullanıcı adı veya şfire.({})".format(verification[0]))
            loginFailedResponse = verification[1]
            await websocket.send("{}".format(loginFailedResponse))
            #await websocket.close_connection()
            return -1
    elif(first_data_json['message_type'] == "chat"):
        username = first_data_json['user_name']
        chatRoomKey = first_data_json['message']
        chatRoomKey_Response = verify_chatroom_key(username,chatRoomKey,"kullanıcılar")
        control = chatRoomKey_Response[0]
        responseMessage_JSON = chatRoomKey_Response[1]
        if(control):#control[0] değişkeni chat odasına girişin başarılı olup olmadığı dönüşünü yapıyor.
            print("Sohbet odasına giriş başarılı.Control = {}".format(control))
            await websocket.send("{}".format(responseMessage_JSON))
            await start_chat(websocket,username)
        else:
            await websocket.send("{}".format(responseMessage_JSON))
            #await websocket.close()
            return -1




