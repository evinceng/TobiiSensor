# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 17:19:46 2016

@author: markome
"""

# -*- coding: utf-8 -*-x
"""
Created on Tue Feb 16 10:02:19 2016
Facereader and Tobii eye tracker and AndroidWear 2 JS - python app. Creates 2 sockets for incomming dotNET app (from tobii and noldus) messages and forwards them on http as .json objects.
All received events (from tobi and noldus) are stored into buffer and send as vector upon http request. When data is sent, buffer is cleared.
For developmnet purposes, until no data is received from noldus and tobii the app is sending "placeholder" data repeatedly. Placeholder data is in format of actual data.
For ports and addresses and paths please see configuration variables.

call of http://localhost:8080/emptyData clears all data buffers.

!! Code requires bottle package.
Install python package bottle by issuing following command from cmd window:
pip install bottle

Code snippets were stollen from various sources:

Working solution from for CORS using bottle (Allow get requests from another server than JavaScript application is originating from):
http://stackoverflow.com/questions/17262170/bottle-py-enabling-cors-for-jquery-ajax-requests

Creation of json:
http://stackoverflow.com/questions/23110383/how-to-dynamically-build-a-json-object-with-python

Threading:
http://stackoverflow.com/questions/2846653/python-multithreading-for-dummies

"""


import socket
import threading
import bottle
import ConfigParser


from bottle import response
import Sensor
import DataParsedSensor

############################################################################
           
# In order to enable CORS - .JS getting data from another web address
# sourced from: http://stackoverflow.com/questions/17262170/bottle-py-enabling-cors-for-jquery-ajax-requests
class EnableCors(object):
    name = 'enable_cors'
    api = 2

    def apply(self, fn, context):
        def _enable_cors(*args, **kwargs):
            # set CORS headers
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

            if bottle.request.method != 'OPTIONS':
                # actual request; reply with the actual response
                return fn(*args, **kwargs)
        return _enable_cors


app = bottle.app()


#sensorList = []

config = ConfigParser.ConfigParser()
config.read('config.ini')

tobii = Sensor.Sensor('TOBII')
#tobii = DataParsedSensor.DataParsedSensor('DATAPS')
# start listening socket in thread
# About threads:  http://docs.python.org/2/library/threading.html#thread-objects
listeningTobiiSocketThread = threading.Thread(target=tobii.listenSocketFromDotNET , args=())

#print 'SOCKET SERVER NOT STARTED!!!!! Uncomment to start.'
listeningTobiiSocketThread.start()

__tobiiEyeTrackerServerHostRoute = config.get('TOBII', 'HostRoute')
#__tobiiEyeTrackerServerHostRoute = config.get('DATAPS', 'HostRoute')
#@app.route('/cors', method=['OPTIONS', 'GET'])
@app.route(__tobiiEyeTrackerServerHostRoute, method=['OPTIONS', 'GET'])
def tobiiEyeTrackerResponder():
    return tobii.respondTracker()
  
#__dpServerHostRoute = config.get('DATAPS', 'HostRoute')
##@app.route('/cors', method=['OPTIONS', 'GET'])
#@app.route(__dpServerHostRoute, method=['OPTIONS', 'GET'])
#def ddatasResponder():
#    return dpsensor.respondTracker()
    
app.install(EnableCors())

__serverHostIP = config.get('SERVER', 'IP')
__serverHostPort = config.getint('SERVER', 'Port')
print 'Starting http server on http://',__serverHostIP,':',__serverHostPort, __tobiiEyeTrackerServerHostRoute #__dpServerHostRoute#
app.run(host=__serverHostIP, port=__serverHostPort)    

print 'Cleanup: http server stopped.'
print 'Cleanup: Stopping incomming tobii data socket ser*ver.'
config.set('DATAPS', 'IsSocketRunning', False)
config.set('TOBII', 'IsSocketRunning', False)
#send one last message to socket thread to disconnect. Ugly hack. Not working until other side client is connected.
tobiiClientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tobiiServer_address = (config.get('TOBII', 'Url'), config.getint('TOBII', 'Port'))
tobiiClientSock.connect(tobiiServer_address)  
tobiiClientSock.sendall('Die!')
tobiiClientSock.close()

    
# this should finish the program. Currently does not work, since socket does not disconnect.
listeningTobiiSocketThread.join()

#listeningdpsensor.join()