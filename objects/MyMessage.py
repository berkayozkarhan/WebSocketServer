import datetime
import json #sonradan kaldır.
class MyMessage:
    def __init__(self,message_type,_from,_to,message,date):
        self.message_type = message_type  #welcome-message,online-clients,directed-message,notification,broadcast
        self._from = _from     #server,uid
        self._to = _to       #(username,userid)
        self.message = message            #message data
        self.date = date                  #now

    def showMessageInformation(self):
        print("Message type:",self.message_type)
        print("From:",self._from)
        print("To:",self._to)
        print("Message:",self.message)
        print("Date:",self.date)
    def logMessage(self):
        pass



