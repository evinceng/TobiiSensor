import ConfigParser
import datetime
import time
import socket
import sys
import json
from bottle import response

class Sensor():
    '''
    If create an instance of a sensor please provide the configurations first in config.ini file
    
    
    '''
    
    config = ConfigParser.ConfigParser()
    
    
    receivedTobiiMessage=[]
    receivedTobiiMessage.append(json.loads('{"tobiiEyeTracker":{"timeStamp":"30.12.2015 14:06:20.2412","leftPos":{"x":"-0,228793755914194","y":"11,5027813555582","z":"60,912982163767"},"rightPos":{"x":"5,89524352818696","y":"11,2245013358383","z":"61,0730322352786"},"leftGaze":{"x":"3,15812377150551","y":"17,3247499470179","z":"4,61986983600664"},"rightGaze":{"x":"-2,49937069615642","y":"17,3932511520527","z":"4,64480229580618"},"leftPupilDiameter":"2,645874","rightPupilDiameter":"2,622345"}}'))
    receivedTobiiMessage.append(json.loads('{"tobiiEyeTracker":{"timeStamp":"30.12.2015 14:06:20.2442","leftPos":{"x":"-0,258863875351471","y":"11,5149518687205","z":"60,9095247803002"},"rightPos":{"x":"5,88168331298095","y":"11,2362714331765","z":"61,0613078775579"},"leftGaze":{"x":"2,38144559635971","y":"16,7283881083418","z":"4,40281135417063"},"rightGaze":{"x":"-3,55454772939922","y":"17,2529816540119","z":"4,59374825056375"},"leftPupilDiameter":"2,642151","rightPupilDiameter":"2,673187"}}'))


    def __init__(self, configSectionName, isLocalFileLogging = True):
        self.config.read('config.ini')
        self.configSectionName = configSectionName
        self.config.set(configSectionName, 'TimeStamp', datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H%M%S'))
        
        if isLocalFileLogging:
            self.config.set(configSectionName, 'IsLocalFileLogging', str(isLocalFileLogging))
            logFileName =  configSectionName + 'Log_' + self.config.get(configSectionName, 'TimeStamp') + '.log'
            self.config.set(configSectionName, 'LocalLoggingFileName', logFileName)
        
        print 'LUCAMI gateway ', configSectionName, ' module starting.'
        
        
    def __writeToFile(self, data, mode):
        """ 
        Opens the file named sectionName+LocalLoggingFileName in the specified @mode and writes the
        @data to it and closes the file.
    
        @param data (string): The data that will be written to the file
        @param mode (char): The mode to open the file
        """
        __fileName = self.config.get(self.configSectionName, 'LocalLoggingFileName')
        try:
            f = open(__fileName, mode)                        
            f.write(data)
        except IOError:
            print("Error while writing to file: ")
        finally:
            f.close()
            
            
    def __initSocket(self):
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
        # Bind the socket to the port
        server_address = (self.config.get(self.configSectionName, 'Url'), self.config.getint(self.configSectionName, 'Port'))    
        print >>sys.stderr, 'Server socket for incomming ', self.configSectionName, ' data: starting up on %s port %s' % server_address
        sock.bind(server_address)    
        # Listen for incoming connections
        sock.listen(1)
        return sock
    
    def __incrementReceivedEventCounter(self):
        __receivedEventCount = self.config.getint(self.configSectionName, 'ReceivedEventCount')
        __receivedEventCount += 1
        self.config.set(self.configSectionName, 'ReceivedEventCount', str(__receivedEventCount))
    
    # Establiehses server socket for incomming connections from .net application.            
    def listenSocketFromDotNET(self):
        __jsonExceptionStr = 'Exception while parsing received JSON  message:'
        __parsedData = None
        
        sock = self.__initSocket()  
        
        while self.config.get(self.configSectionName, 'IsSocketRunning'):
            # Wait for a connection
            print >>sys.stderr, 'Server socket for incomming ', self.configSectionName, ' data: waiting for a connection'
            connection, client_address = sock.accept()
        
            try:
                print >>sys.stderr, 'Server socket for incomming ', self.configSectionName, ' data: connection from', client_address
    
                # Receive the data in small chunks and retransmit it
                while self.config.get(self.configSectionName, 'IsSocketRunning'):
                    
                    self.__incrementReceivedEventCounter()
                    data = connection.recv(10000) # kinda ugly hack. If incomming message will be longer this will spill.
                    #receivedTobiiMessage = data
                    if(not self.config.getboolean(self.configSectionName, 'IsDataReceivedFromSender')): #clear data
                        print 'Got first message from ', self.configSectionName, '. Switching to real data mode.'
                        self.config.set(self.configSectionName, 'IsDataReceivedFromSender', 'True')
                        self.receivedTobiiMessage=[]     
                    
                    if self.config.getboolean(self.configSectionName, 'IsLocalFileLogging'): 
                        print(self.config.getboolean(self.configSectionName, 'IsDataHasToBeParsed'))
                        
                        try:
                            if self.config.getboolean(self.configSectionName, 'IsDataHasToBeParsed'):
                                __parsedData = self.parseData(self, data)
                                data = __parsedData
                            self.receivedTobiiMessage.append(json.loads(data))
                            self.__writeToFile(data, 'a')
                        except:
                            print 'Exception while parsing received JSON  message from ', self.configSectionName
                            self.__writeToFile(__jsonExceptionStr + data, 'a')
                            #receivedTobiiMessage.append(data)
                            #print >>sys.stderr, 'received "%s"' % data
                    if data:
                        print >>sys.stderr, 'Server socket for incomming ', self.configSectionName, ' data: sending data back to the client'
                        connection.sendall(data)
                    else:
                        print >>sys.stderr, 'Server socket for incomming ', self.configSectionName, ' data: no more data from', client_address
                        break
               
            finally:
                # Clean up the connection
                connection.shutdown(1);
                connection.close()
                print 'Closing incomming ', self.configSectionName, ' data socket connection.'
        print 'Finished server socket for incomming ', self.configSectionName, ' data thread'
        
    def respondTracker(self):
        response.headers['Content-type'] = 'application/json'
        dataLogFileName = self.configSectionName+'DetailedLog'
        #i=i+1
        data = {}
        #data['mykey']='myvalue'
        data['receivedEventCounter']=self.config.getint(self.configSectionName, 'ReceivedEventCount')
        
        if self.config.getboolean(self.configSectionName, 'IsDataHasToBeParsed'): 
            data[dataLogFileName] = self.parseData(self.receivedTobiiMessage)
        else:
            data[dataLogFileName] = self.receivedTobiiMessage
        
        json_data = json.dumps(data)
        #clear message buffer
        if self.config.getboolean(self.configSectionName, 'IsDataReceivedFromSender'):
            self.receivedTobiiMessage=[]
        else:
            print 'Sending emulated response for ', self.configSectionName, ', since no data arrived jet from ', self.configSectionName
        return json_data
        
    def parseData(self, data):
        if self.config.getboolean(self.configSectionName, 'IsDataHasToBeParsed'): 
            raise NotImplementedError('It seems that the data has to be parsed. Please override and implement parseData method!')
        else:
            raise NotImplementedError('It is declared that the data don\'t need to be parsed. Please check __init__!')