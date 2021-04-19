import logging

class Client:
    def __init__(self,username,userID,status,connected,relatedSocket):
        self.username = username
        self.userID = userID
        self.status = status
        self.connected = connected
        self.relatedSocket = relatedSocket
    def showInfo(self):
        print("Username :",self.username)
        print("User ID :",self.userID)
        print("Status: ",self.status)
        print("Connected :",self.connected)
        print("Related Socket :",self.relatedSocket)
    def logInfo(self,logFile):#sohbete katılan kullanıcının bilgisini loglamak için
        #logFile.info('Client connected the chat room : {} - {} - {} - {} - {} '.format(self.username,self.userID,self.status,self.connected,self.relatedSocket))
        pass


