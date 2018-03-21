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
conda install -c anaconda anaconda-navigator 
(I had to install )
conda install -c conda-forge bottle #pip install bottle breaks the installation if you use anaconda navigator

Code snippets were stollen from various sources:

Working solution from for CORS using bottle (Allow get requests from another server than JavaScript application is originating from):
http://stackoverflow.com/questions/17262170/bottle-py-enabling-cors-for-jquery-ajax-requests

Creation of json:
http://stackoverflow.com/questions/23110383/how-to-dynamically-build-a-json-object-with-python

Threading:
http://stackoverflow.com/questions/2846653/python-multithreading-for-dummies



My comments:
    -15 pomeni dodano shranjevanje v bazo multiluxa
    -dodal import pymongo!
    -na bazo se bom povezoval na samem začtku, shranjeval bom pa ob socketu, ko vsakega od sporočil prejmem
    ga bom poslal kar naprej!
    - shranjevanje v bazo deluje vredu! problem je bil ker nisem shranjeval jsona!
    deluje tako za GSR kot za Accel

    - socket za Noldus in wear različno sprejemata podatke, wear že pričakuje json objekt, noldus ga pa kasneje
    na nek način parsa. Moji dve funkciji sta sedaj imlemenitrani z json.loads(), ki pričakuje json objekt!
    zaradi tega lahko vidimo pri noldusu implementacijo s tem da mi kreiramo nek podatkovni 
    objekt, kar se nam pa pri wear, s tem ko preberemo json opravi samo in naloži v received spremenljivko
    -ugašanje socketa na tej strani še mogoče s shutdown() nadgradit.
    - bil je problem izpada povezave pri Accel in GSR zaradi tega ker smo po socketu pošiljali responde
    ki pa jih nismo potrebovali in je to zapolnilo socket ter je vse skup padlo po 2000 meritvah
@author: markome, marko.meza@fe.uni-lj.si
"""




import threading
import socket
import sys
import bottle
from bottle import response
import json
import time
import datetime
import requests



import re
























# Konfiguracija spremenljivk za socket za tobii

runTimestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H%M%S')


# @Primoz Kocevar
###########################################################

# addres for php server saving to mongoDB
global phpGSR
phpGSR="http://nacomnet.lucami.org/expapp/typingtutor_3/php/post_GSR_test.php"
global phpAccel
phpAccel="http://nacomnet.lucami.org/expapp/typingtutor_3/php/post_multilux_Accel_test.php"

# variables for sockets
global multiLuxAccelAddress
multiLuxAccelAddress = 'localhost'
global multiLuxAccelPort
multiLuxAccelPort = 10006

multiLuxAccelHostRoute = '/multiLuxAccel'

global multiLuxAccelReceivedEventCounter
multiLuxAccelReceivedEventCounter=0

global receivedMultiLuxAccel

receivedMultiLuxAccel=[] # ustvarš json listo in ji appendaš potem meritve
receivedMultiLuxAccel.append(json.loads('{"multiLuxAccel":{"timestamp":"30.12.2015 14:06:20.2412","accel":{"ax":"234","ay":"23","az":"23"},"gyro":{"gx":"23","gy":"23","gz":"32"}}}'))
receivedMultiLuxAccel.append(json.loads('{"multiLuxAccel":{"timestamp":"30.12.2015 14:06:21.2412","accel":{"ax":"234","ay":"23","az":"23"},"gyro":{"gx":"23","gy":"23","gz":"32"}}}'))

global multiLuxAccelReceivedFromSender
multiLuxAccelReceivedFromSender = False

global multiLuxAccelSocketRunning
multiLuxAccelSocketRunning = True
global multiLuxAccelDataLocalFileLogging
multiLuxAccelDataLocalFileLogging = True
global multiLuxAccelDataLocalFileLoggingFileName
multiLuxAccelDataLocalFileLoggingFileName = 'multiLuxAccelLog_'+runTimestamp+'.log'


# configuration of global variables
global multiLuxGSRAddress
multiLuxGSRAddress = 'localhost'
global multiLuxGSRPort
multiLuxGSRPort = 10007
multiLuxGSRHostRoute = '/multiLuxGSR'

global multiLuxGSRReceivedEventCounter
multiLuxGSRReceivedEventCounter=0

global receivedMultiLuxGSR

receivedMultiLuxGSR=[] # ustvarš json listo in ji appendaš potem meritve
receivedMultiLuxGSR.append(json.loads('{"multiLuxGSR":{"timestamp":"30.12.2015 14:06:20.2412","resistanceOhm":{"right":"23","left":"34"}}}'))
receivedMultiLuxGSR.append(json.loads('{"multiLuxGSR":{"timestamp":"30.12.2015 14:06:20.2412","resistanceOhm":{"right":"23","left":"34"}}}'))


global multiLuxGSRReceivedFromSender
multiLuxGSRReceivedFromSender = False

global multiLuxGSRSocketRunning
multiLuxGSRSocketRunning = True
global multiLuxGSRDataLocalFileLogging
multiLuxGSRDataLocalFileLogging = True
global multiLuxGSRDataLocalFileLoggingFileName
multiLuxGSRDataLocalFileLoggingFileName = 'multiLuxGSRLog_'+runTimestamp+'.log'


#################################################################



#configuration of dotNET application communication socket - data source
global tobiiDotNetAppAddress
tobiiDotNetAddress = 'localhost'
global tobiiDotNeAppPort
tobiiDotNeAppPort=10003

tobiiEyeTrackerServerHostRoute='/tobiiEyetracker'

global tobiiEyeTrackerReceivedEventCounter
tobiiEyeTrackerReceivedEventCounter=0;

global receivedTobiiMessage
# default data sent UNTIL none is received from FaceReader
receivedTobiiMessage=[]
#receivedTobiiMessage.append(json.loads('{"tobiiEyeTracker": {"leftPos": {"y": "6,54191137932216","x": "-6,95598391113099","z": "58,852241687782"},"timeStamp": "24.12.2015 11:06:59.6288","leftGaze": {"y": "21,7719111544532","x": "0,86490466749226","z": "6,23850804784943"},"rightPos": {"y": "7,04664176343695","x": "-0,80637315236163","z": "59,3518039600174"},"rightGaze": {"y": "22,6628011052412","x": "-5,56592479836322","z": "6,56276625429384"}}}'))
#receivedTobiiMessage.append(json.loads('{"tobiiEyeTracker": {"leftPos": {"y": "6,54191137932216","x": "-6,95598391113099","z": "58,852241687782"},"timeStamp": "24.12.2015 11:06:59.6288","leftGaze": {"y": "21,7719111544532","x": "0,86490466749226","z": "6,23850804784943"},"rightPos": {"y": "7,04664176343695","x": "-0,80637315236163","z": "59,3518039600174"},"rightGaze": {"y": "22,6628011052412","x": "-5,56592479836322","z": "6,56276625429384"}}}'))
receivedTobiiMessage.append(json.loads('{"tobiiEyeTracker":{"timeStamp":"30.12.2015 14:06:20.2412","leftPos":{"x":"-0,228793755914194","y":"11,5027813555582","z":"60,912982163767"},"rightPos":{"x":"5,89524352818696","y":"11,2245013358383","z":"61,0730322352786"},"leftGaze":{"x":"3,15812377150551","y":"17,3247499470179","z":"4,61986983600664"},"rightGaze":{"x":"-2,49937069615642","y":"17,3932511520527","z":"4,64480229580618"},"leftPupilDiameter":"2,645874","rightPupilDiameter":"2,622345"}}'))
receivedTobiiMessage.append(json.loads('{"tobiiEyeTracker":{"timeStamp":"30.12.2015 14:06:20.2442","leftPos":{"x":"-0,258863875351471","y":"11,5149518687205","z":"60,9095247803002"},"rightPos":{"x":"5,88168331298095","y":"11,2362714331765","z":"61,0613078775579"},"leftGaze":{"x":"2,38144559635971","y":"16,7283881083418","z":"4,40281135417063"},"rightGaze":{"x":"-3,55454772939922","y":"17,2529816540119","z":"4,59374825056375"},"leftPupilDiameter":"2,642151","rightPupilDiameter":"2,673187"}}'))

global tobiiReceivedFromSender # this is used for debugging. Until actual data is received, fake data  is sent.
tobiiReceivedFromSender=False

global tobiiSocketRunning
tobiiSocketRunning = True
global tobiiDataLocalFileLogging
tobiiDataLocalFileLogging=True
global tobiiDataLocalFileLoggingFileName
tobiiDataLocalFileLoggingFileName='tobiiLog_'+runTimestamp+'.log'




# Konfiguracija spremenljivk za face reader socket!

global faceReaderDotNetAddress
faceReaderDotNetAddress='localhost'
global faceReaderDotNeAppPort
faceReaderDotNeAppPort=10001
#global noldusFaceReaderServerHostRoute
noldusFaceReaderServerHostRoute='/noldusFaceReader'
global noldusFaceReaderReceivedEventCounter
noldusFaceReaderReceivedEventCounter=0;
global receivedNoldusMessage
receivedNoldusMessage=[]
# default data sent UNTIL none is received from FaceReader

#parsed ok.
#receivedNoldusMessage.append('DetailedLog 18.11.2015 14:41:35.299 Neutral : 0,5704 Happy : 0,6698 Sad : 0,0013 Angry : 0,0040 Surprised : 0,0129 Scared : 0,0007 Disgusted : 0,0048 Valence : 0,6650 Arousal : 0,2297 Gender : Male Age : 20 - 30 Beard : None Moustache : None Glasses : Yes Ethnicity : Caucasian Y - Head Orientation : -1,7628 X - Head Orientation : 2,5652 Z - Head Orientation : -3,0980 Landmarks : 375,4739 - 121,6879 - 383,2627 - 113,6502 - 390,8202 - 110,3507 - 396,1021 - 109,7039 - 404,9615 - 110,9594 - 443,2603 - 108,9765 - 451,9454 - 106,7192 - 457,1207 - 106,8835 - 464,1162 - 109,5496 - 470,9659 - 116,8992 - 387,4940 - 132,0171 - 406,4031 - 130,4482 - 441,6239 - 128,6356 - 460,6862 - 128,1997 - 419,0713 - 161,6479 - 425,3519 - 155,1223 - 431,9862 - 160,6411 - 406,9320 - 190,3831 - 411,4790 - 188,7656 - 423,1751 - 185,6583 - 428,5339 - 185,6882 - 433,7802 - 184,8167 - 445,6192 - 186,3515 - 450,8424 - 187,2787 - 406,0796 - 191,1880 - 411,9287 - 193,5352 - 417,9666 - 193,6567 - 424,0851 - 193,4941 - 428,6678 - 193,5652 - 433,2172 - 192,7540 - 439,3548 - 192,0136 - 445,4181 - 191,1532 - 451,6007 - 187,9486 - 404,5193 - 190,6352 - 412,8277 - 185,4609 - 421,1355 - 181,2883 - 428,3182 - 181,1826 - 435,2024 - 180,2258 - 443,9292 - 183,2533 - 453,1117 - 187,2288 - 405,9689 - 193,2750 - 410,0249 - 199,8118 - 416,0457 - 203,0374 - 423,4839 - 204,1818 - 429,9247 - 204,2175 - 436,3620 - 203,1305 - 443,4268 - 200,9355 - 448,9572 - 197,1335 - 452,0746 - 190,0314 Quality : 0,8137 Mouth : Closed Left Eye : Open Right Eye : Open Left Eyebrow : Lowered Right Eyebrow : Lowered Identity : NO IDENTIFICATION')
receivedNoldusMessage.append('DetailedLog    24.12.2015 13:01:54.282    ')

#HUH - not parsed right. detailed log is missing.
#receivedNoldusMessage.append('DetailedLog 18.11.2015 14:41:35.299 Neutral : 0,5704 Happy : 0,6698 Sad : 0,0013 Angry : 0,0040 Surprised : 0,0129 Scared : 0,0007 Disgusted : 0,0048 Valence : 0,6650 Arousal : 0,2297 Gender : Male Age : 20 - 30 Beard : None Moustache : None Glasses : Yes Ethnicity : Caucasian Y - Head Orientation : -1,7628 X - Head Orientation : 2,5652 Z - Head Orientation : -3,0980 Landmarks : 375,4739 - 121,6879 - 383,2627 - 113,6502 - 390,8202 - 110,3507 - 396,1021 - 109,7039 - 404,9615 - 110,9594 - 443,2603 - 108,9765 - 451,9454 - 106,7192 - 457,1207 - 106,8835 - 464,1162 - 109,5496 - 470,9659 - 116,8992 - 387,4940 - 132,0171 - 406,4031 - 130,4482 - 441,6239 - 128,6356 - 460,6862 - 128,1997 - 419,0713 - 161,6479 - 425,3519 - 155,1223 - 431,9862 - 160,6411 - 406,9320 - 190,3831 - 411,4790 - 188,7656 - 423,1751 - 185,6583 - 428,5339 - 185,6882 - 433,7802 - 184,8167 - 445,6192 - 186,3515 - 450,8424 - 187,2787 - 406,0796 - 191,1880 - 411,9287 - 193,5352 - 417,9666 - 193,6567 - 424,0851 - 193,4941 - 428,6678 - 193,5652 - 433,2172 - 192,7540 - 439,3548 - 192,0136 - 445,4181 - 191,1532 - 451,6007 - 187,9486 - 404,5193 - 190,6352 - 412,8277 - 185,4609 - 421,1355 - 181,2883 - 428,3182 - 181,1826 - 435,2024 - 180,2258 - 443,9292 - 183,2533 - 453,1117 - 187,2288 - 405,9689 - 193,2750 - 410,0249 - 199,8118 - 416,0457 - 203,0374 - 423,4839 - 204,1818 - 429,9247 - 204,2175 - 436,3620 - 203,1305 - 443,4268 - 200,9355 - 448,9572 - 197,1335 - 452,0746 - 190,0314 Quality : 0,8137 Mouth : Closed Left Eye : Open Right Eye : Open Left Eyebrow : Lowered Right Eyebrow : Lowered Identity : NO IDENTIFICATION')
#receivedNoldusMessage.append('DetailedLog 23.3.2016 12:38:26.842    Neutral : 0,1793    Happy : 0,0042    Sad : 0,0075    Angry : 0,3749    Surprised : 0,0025    Scared : 0,0006    Disgusted : 0,0131    Valence : -0,3707    Arousal : 0,6455    Gender : Male    Age : 15 - 25    Beard : None    Moustache : None    Glasses : Yes    Ethnicity : Caucasian    Y - Head Orientation : -0,9125    X - Head Orientation : 5,8517    Z - Head Orientation : 0,0175    Landmarks : 311,4145 - 213,7986 - 318,6623 - 207,6854 - 327,5864 - 205,5820 - 335,3559 - 206,4292 - 344,1902 - 207,7700 - 380,6983 - 207,2488 - 389,8992 - 205,6435 - 398,4917 - 204,6727 - 408,4374 - 206,6562 - 416,6983 - 212,8398 - 323,9193 - 225,7345 - 344,7270 - 225,7050 - 383,2826 - 225,2818 - 405,0711 - 224,9512 - 353,8427 - 263,7656 - 360,7225 - 259,2176 - 369,0743 - 263,7220 - 343,2064 - 299,5742 - 346,6842 - 296,1347 - 355,3814 - 291,8626 - 361,7963 - 291,4087 - 368,3246 - 291,9060 - 378,0664 - 296,3725 - 382,3956 - 299,8943 - 343,8093 - 299,5201 - 348,0703 - 301,0596 - 352,0848 - 301,0907 - 357,6157 - 301,8916 - 362,0904 - 302,3653 - 366,5635 - 301,9263 - 372,4471 - 301,2214 - 376,9265 - 301,3126 - 381,7018 - 299,8272 - 342,2394 - 299,6492 - 347,9221 - 293,0683 - 353,1402 - 286,6745 - 361,5580 - 285,9843 - 370,2161 - 286,7126 - 376,4315 - 293,2307 - 383,3795 - 300,0077 - 342,8300 - 302,2052 - 346,1582 - 307,2395 - 349,0222 - 310,9710 - 355,8743 - 312,4983 - 362,0354 - 312,9872 - 368,2486 - 312,5931 - 375,4057 - 311,2328 - 378,6325 - 307,5786 - 382,6278 - 302,5534    Quality : 0,8039    Mouth : Closed    Left Eye : Open    Right Eye : Open    Left Eyebrow : Lowered    Right Eyebrow : Neutral    Identity : NO IDENTIFICATION')
receivedNoldusMessage.append('DetailedLog    23.3.2016 12:38:27.138    Neutral : 0,2705    Happy : 0,0028    Sad : 0,0176    Angry : 0,2058    Surprised : 0,0027    Scared : 0,0010    Disgusted : 0,0090    Valence : -0,2030    Arousal : 0,6857    Gender : Male    Age : 15 - 25    Beard : None    Moustache : None    Glasses : Yes    Ethnicity : Caucasian    Y - Head Orientation : -0,6889    X - Head Orientation : 4,3651    Z - Head Orientation : -0,0234    Landmarks : 310,7171 - 212,1067 - 318,5532 - 206,0340 - 327,7380 - 204,1013 - 335,4113 - 204,9887 - 344,2658 - 206,3714 - 380,3481 - 206,0415 - 389,3315 - 204,5061 - 397,8604 - 203,6755 - 407,4076 - 205,5042 - 415,1564 - 211,6094 - 323,0402 - 223,9535 - 344,0394 - 224,2175 - 381,3725 - 224,0762 - 403,2078 - 223,5444 - 352,9612 - 264,1343 - 359,9450 - 259,6382 - 368,2259 - 264,0295 - 342,5881 - 299,7938 - 346,3780 - 296,7481 - 355,1073 - 292,6639 - 361,4304 - 292,1327 - 367,8818 - 292,5529 - 377,6498 - 296,6849 - 382,2748 - 299,6749 - 343,2721 - 299,3919 - 347,8906 - 300,0666 - 351,6346 - 299,6332 - 357,0821 - 300,4130 - 361,5859 - 300,7857 - 366,1521 - 300,2982 - 371,9625 - 299,5152 - 376,2759 - 300,0159 - 381,5689 - 299,2570 - 341,5972 - 299,6690 - 347,6369 - 293,9006 - 352,6677 - 287,6637 - 361,1557 - 286,9240 - 369,8073 - 287,5571 - 375,9206 - 293,7881 - 383,4036 - 299,5890 - 342,2021 - 302,0303 - 346,0248 - 306,2598 - 348,7699 - 309,4252 - 355,7914 - 310,7215 - 361,8730 - 311,1142 - 368,2041 - 310,6604 - 375,2107 - 309,3967 - 378,1558 - 306,3152 - 382,6892 - 301,9328    Quality : 0,7926    Mouth : Closed    Left Eye : Open    Right Eye : Open    Left Eyebrow : Lowered    Right Eyebrow : Neutral    Identity : NO IDENTIFICATION')

global noldusReceivedFromSender # this is used for debugging. Until actual data is received, fake data  is sent.
noldusReceivedFromSender=False
global noldusSocketRunning
noldusSocketRunning = True
global noldusDataLocalFileLogging
noldusDataLocalFileLogging=True
global noldusDataLocalFileLoggingFileName
noldusDataLocalFileLoggingFileName='noldusLog_'+runTimestamp+'.log'



global wearSocketRunning
wearSocketRunning = True
global wearSocketAddress


# !!!!!!!!!!!!!!!!!! if correct IP is obtained automatically leave like this. 
#Otherwise use commented IP hardcoding line
#wearSocketAddress="192.168.81.186"
wearSocketAddress=socket.gethostbyname(socket.gethostname())
global wearSocketPort
wearSocketPort=10005
global wearReceivedEventCounter
wearReceivedEventCounter=0
wearServerHostRoute='/wear'
global receivedWearMessage
receivedWearMessage=[]
#fake data for debugging
receivedWearMessage.append(json.loads('{"timestamp":"02.02.2016 09:36:55.0860","type":"accel","z":9.594614028930664,"y":0.1405097097158432,"x":0.07721300423145294}'))
receivedWearMessage.append(json.loads('{"timestamp":"02.02.2016 09:36:55.0930","type":"accel","z":9.592219352722168,"y":0.15487492084503174,"x":0.06763619929552078}'))

global wearReceivedFromSender # this is used for debugging. Until actual data is received, fake data  is sent.
wearReceivedFromSender=False
global wearDataLocalFileLogging
wearDataLocalFileLogging=True
global wearDataLocalFileLoggingFileName
wearDataLocalFileLoggingFileName='wearLog_'+runTimestamp+'.log'


#configuration of http server serving json
#serverHostIP = '192.168.81.76'
#serverHostIP = 'localhost'
serverHostIP = '127.0.0.1'
serverHostPort=8080

#call to this url clears all data buffers.
emptyDataServerHostRoute='/emptyData'

#global tobiiEyeTrackerServerHostRoute
#tobiiEyeTrackerServerHostRoute='/facereader'






# parses NOLDUS string to compatible JSON object (by David Brvar)

def parseNoldus(x):
    
    #markome:
    #works with: 'DetailedLog 18.11.2015 14:41:35.299 Neutral : 0,5704 Happy : 0,6698 Sad : 0,0013 Angry : 0,0040 Surprised : 0,0129 Scared : 0,0007 Disgusted : 0,0048 Valence : 0,6650 Arousal : 0,2297 Gender : Male Age : 20 - 30 Beard : None Moustache : None Glasses : Yes Ethnicity : Caucasian Y - Head Orientation : -1,7628 X - Head Orientation : 2,5652 Z - Head Orientation : -3,0980 Landmarks : 375,4739 - 121,6879 - 383,2627 - 113,6502 - 390,8202 - 110,3507 - 396,1021 - 109,7039 - 404,9615 - 110,9594 - 443,2603 - 108,9765 - 451,9454 - 106,7192 - 457,1207 - 106,8835 - 464,1162 - 109,5496 - 470,9659 - 116,8992 - 387,4940 - 132,0171 - 406,4031 - 130,4482 - 441,6239 - 128,6356 - 460,6862 - 128,1997 - 419,0713 - 161,6479 - 425,3519 - 155,1223 - 431,9862 - 160,6411 - 406,9320 - 190,3831 - 411,4790 - 188,7656 - 423,1751 - 185,6583 - 428,5339 - 185,6882 - 433,7802 - 184,8167 - 445,6192 - 186,3515 - 450,8424 - 187,2787 - 406,0796 - 191,1880 - 411,9287 - 193,5352 - 417,9666 - 193,6567 - 424,0851 - 193,4941 - 428,6678 - 193,5652 - 433,2172 - 192,7540 - 439,3548 - 192,0136 - 445,4181 - 191,1532 - 451,6007 - 187,9486 - 404,5193 - 190,6352 - 412,8277 - 185,4609 - 421,1355 - 181,2883 - 428,3182 - 181,1826 - 435,2024 - 180,2258 - 443,9292 - 183,2533 - 453,1117 - 187,2288 - 405,9689 - 193,2750 - 410,0249 - 199,8118 - 416,0457 - 203,0374 - 423,4839 - 204,1818 - 429,9247 - 204,2175 - 436,3620 - 203,1305 - 443,4268 - 200,9355 - 448,9572 - 197,1335 - 452,0746 - 190,0314 Quality : 0,8137 Mouth : Closed Left Eye : Open Right Eye : Open Left Eyebrow : Lowered Right Eyebrow : Lowered Identity : NO IDENTIFICATION'
    #does not work with: 'DetailedLog    23.3.2016 12:38:27.138    Neutral : 0,2705    Happy : 0,0028    Sad : 0,0176    Angry : 0,2058    Surprised : 0,0027    Scared : 0,0010    Disgusted : 0,0090    Valence : -0,2030    Arousal : 0,6857    Gender : Male    Age : 15 - 25    Beard : None    Moustache : None    Glasses : Yes    Ethnicity : Caucasian    Y - Head Orientation : -0,6889    X - Head Orientation : 4,3651    Z - Head Orientation : -0,0234    Landmarks : 310,7171 - 212,1067 - 318,5532 - 206,0340 - 327,7380 - 204,1013 - 335,4113 - 204,9887 - 344,2658 - 206,3714 - 380,3481 - 206,0415 - 389,3315 - 204,5061 - 397,8604 - 203,6755 - 407,4076 - 205,5042 - 415,1564 - 211,6094 - 323,0402 - 223,9535 - 344,0394 - 224,2175 - 381,3725 - 224,0762 - 403,2078 - 223,5444 - 352,9612 - 264,1343 - 359,9450 - 259,6382 - 368,2259 - 264,0295 - 342,5881 - 299,7938 - 346,3780 - 296,7481 - 355,1073 - 292,6639 - 361,4304 - 292,1327 - 367,8818 - 292,5529 - 377,6498 - 296,6849 - 382,2748 - 299,6749 - 343,2721 - 299,3919 - 347,8906 - 300,0666 - 351,6346 - 299,6332 - 357,0821 - 300,4130 - 361,5859 - 300,7857 - 366,1521 - 300,2982 - 371,9625 - 299,5152 - 376,2759 - 300,0159 - 381,5689 - 299,2570 - 341,5972 - 299,6690 - 347,6369 - 293,9006 - 352,6677 - 287,6637 - 361,1557 - 286,9240 - 369,8073 - 287,5571 - 375,9206 - 293,7881 - 383,4036 - 299,5890 - 342,2021 - 302,0303 - 346,0248 - 306,2598 - 348,7699 - 309,4252 - 355,7914 - 310,7215 - 361,8730 - 311,1142 - 368,2041 - 310,6604 - 375,2107 - 309,3967 - 378,1558 - 306,3152 - 382,6892 - 301,9328    Quality : 0,7926    Mouth : Closed    Left Eye : Open    Right Eye : Open    Left Eyebrow : Lowered    Right Eyebrow : Neutral    Identity : NO IDENTIFICATION'
    # quick fix replace 'DetailedLog    ' with 'DetailedLog '
    #x=x.replace("DetailedLog    ","DetailedLog ")
    replaceOffendingStringRegEx = re.compile('DetailedLog    ')    
    #end marko
    
    # da javasscript lahko lazje stringe spremeni v floate (rabi decimalno piko)
    zamenjajVseVejiceSPiko = re.compile('\,')    
    
    
    # compilan tu in ne v for loopu - za performance!
    parsajVJSONObjekt = re.compile(ur'(?:(DetailedLog) ([^ ]+ [^ ]+)|(\b[A-Z][A-Za-z -]+?) : ((?:(?:-?[\d.]+)(?: - -?[\d.]+)*|(?:(?:[A-Z ]+\b|[A-Za-z]+)))))(?:$| )')  
    data = []
    #result = {} #BUG!!!!
    #temp = {}  
    # obdela vsak posamezni element v listu
    for i in x:
        result = {} #should intialize this in every run!!!! to correctly process 'DetailedLog    24.12.2015 13:01:54.282    '
        #temp = {}  
        temp = zamenjajVseVejiceSPiko.sub(".", i)    
        
        #marko
        temp = replaceOffendingStringRegEx.sub("DetailedLog ",temp)
        #endMarko    

        
        # vse matche spravim v array
        temp = re.findall(parsajVJSONObjekt, temp)
        # obdela vsak match posebej, matchi so tipa <type 'tuple'>
        for match in temp:
            # sortiram glede na to, kako regex vrne matche
            if match[0]:
                result[match[0]] = match[1]
            else:
                result[match[2]] = match[3]
        data.append(result)
    return data






print 'LUCAMI gateway Noldus module starting.'
# Establiehses server socket for incomming connections from .net application.            
def listenNoldusFaceReaderSocketFromDotNET():
    #will run util this is True    
    global noldusSocketRunning    
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
    # Bind the socket to the port
    global faceReaderDotNetAddress
    global faceReaderDotNeAppPort
    server_address = (faceReaderDotNetAddress, faceReaderDotNeAppPort)
    print >>sys.stderr, 'Server socket for incomming data: starting up on %s port %s' % server_address
    sock.bind(server_address)
    
    global noldusDataLocalFileLogging
    #noldusDataLocalFileLogging=True
    global noldusDataLocalFileLoggingFileName
    #noldusDataLocalFileLoggingFileName='noldusLog_'+runTimestamp+'.log'
    
    # Listen for incoming connections
    sock.listen(1)
    
    while noldusSocketRunning:
        # Wait for a connection
        print >>sys.stderr, 'Server socket for incomming data: waiting for a connection'
        connection, client_address = sock.accept()
        
        try:
            print >>sys.stderr, 'Server socket for incomming data: connection from', client_address
    
            # Receive the data in small chunks and retransmit it
            while noldusSocketRunning:
                global noldusFaceReaderReceivedEventCounter
                noldusFaceReaderReceivedEventCounter = noldusFaceReaderReceivedEventCounter + 1
                global receivedNoldusMessage
                global noldusReceivedFromSender
                data = connection.recv(10000) # kinda ugly hack. If incomming message will be longer this will spill.
                #receivedNoldusMessage = data
                
                if (not noldusReceivedFromSender): #clear data
                    print 'Got first message from Tobii. Switching to real data mode.'
                    noldusReceivedFromSender = True
                    receivedNoldusMessage=[]
                    
                receivedNoldusMessage.append(data)
                if noldusDataLocalFileLogging:
                    f = open(noldusDataLocalFileLoggingFileName, 'a')                        
                    f.write(data)
                    f.write('\n')
                    f.close()
                #print >>sys.stderr, 'received "%s"' % data
                if data:
                    print >>sys.stderr, 'Server socket for incomming data: sending data back to the client'
                    connection.sendall(data)
                else:
                    print >>sys.stderr, 'Server socket for incomming data: no more data from', client_address
                    break
                
        finally:
            # Clean up the connection
            connection.shutdown(1);
            connection.close()
            print 'Closing incomming data socket connection.'
    print 'Finished server socket for incomming data thread'
# start listening socket in thread
# About threads:  http://docs.python.org/2/library/threading.html#thread-objects
listeningNoldusSocketThread = threading.Thread(target=listenNoldusFaceReaderSocketFromDotNET, args=())
listeningNoldusSocketThread.start()





print 'LUCAMI gateway Tobii module starting.'

# Establiehses server socket for incomming connections from .net application.            
def listenTobiiSocketFromDotNET():
    #will run util this is True    
    global tobiiSocketRunning    
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
    # Bind the socket to the port
    global tobiiDotNetAddress
    global tobiiDotNeAppPort
    server_address = (tobiiDotNetAddress, tobiiDotNeAppPort)
    print >>sys.stderr, 'Server socket for incomming tobii data: starting up on %s port %s' % server_address
    sock.bind(server_address)
    
    global tobiiDataLocalFileLogging
    #tobiiDataLocalFileLogging=True
    global tobiiDataLocalFileLoggingFileName
    #tobiiDataLocalFileLoggingFileName='tobiiLog_'+runTimestamp+'.log'
    
    # Listen for incoming connections
    sock.listen(1)
    
    while tobiiSocketRunning:
        # Wait for a connection
        print >>sys.stderr, 'Server socket for incomming tobii data: waiting for a connection'
        connection, client_address = sock.accept()
        
        try:
            print >>sys.stderr, 'Server socket for incomming tobii data: connection from', client_address
    
            # Receive the data in small chunks and retransmit it
            while tobiiSocketRunning:
                global receivedTobiiMessage
                global tobiiEyeTrackerReceivedEventCounter
                tobiiEyeTrackerReceivedEventCounter=tobiiEyeTrackerReceivedEventCounter+1
                data = connection.recv(10000) # kinda ugly hack. If incomming message will be longer this will spill.
                #receivedTobiiMessage = data
                global tobiiReceivedFromSender
                if(not tobiiReceivedFromSender): #clear data
                    print 'Got first message from Tobii. Switching to real data mode.'
                    tobiiReceivedFromSender = True
                    receivedTobiiMessage=[]                
                try:
                    if tobiiDataLocalFileLogging:
                        f = open(tobiiDataLocalFileLoggingFileName, 'a')                        
                        f.write(data)
                        f.close()
                    receivedTobiiMessage.append(json.loads(data))
                except:
                    print 'Exception while parsing received JSON  message from tobii'
                    if tobiiDataLocalFileLogging:
                        f = open(tobiiDataLocalFileLoggingFileName, 'a')
                        f.write('Exception while parsing received JSON  message:')
                        f.write(data)
                        f.close()
                #receivedTobiiMessage.append(data)
                #print >>sys.stderr, 'received "%s"' % data
                if data:
                    print >>sys.stderr, 'Server socket for incomming tobii data: sending data back to the client'
                    connection.sendall(data)
                else:
                    print >>sys.stderr, 'Server socket for incomming tobii data: no more data from', client_address
                    break
               
        finally:
            # Clean up the connection
            connection.shutdown(1);
            connection.close()
            print 'Closing incomming tobii data socket connection.'
    print 'Finished server socket for incomming tobii data thread'
# start listening socket in thread
# About threads:  http://docs.python.org/2/library/threading.html#thread-objects
listeningTobiiSocketThread = threading.Thread(target=listenTobiiSocketFromDotNET, args=())

#print 'SOCKET SERVER NOT STARTED!!!!! Uncomment to start.'
listeningTobiiSocketThread.start()


print 'LUCAMI gateway Wear module starting.'

def listenWearSocket():
    #will run util this is True  
    global wearSocketRunning
     # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
    # Bind the socket to the port
    global wearSocketAddress
    global wearSocketPort
    server_address = (wearSocketAddress, wearSocketPort)
    print >>sys.stderr, 'Server socket for incomming data: starting up on %s port %s' % server_address
    print >>sys.stderr, 'If you see error creating socket please hardcode ip in wearSocketAddress variable.'
    sock.bind(server_address)
    
    global wearDataLocalFileLogging
    #wearDataLocalFileLogging=True
    global wearDataLocalFileLoggingFileName
    #wearDataLocalFileLoggingFileName='wearLog.log'    
    
    
    # Listen for incoming connections
    sock.listen(1)
    while wearSocketRunning:
        # Wait for a connection
        print >>sys.stderr, 'Server socket for incomming data: waiting for a connection'
        connection, client_address = sock.accept()
        
        try:
            print >>sys.stderr, 'Server socket for incomming data: connection from', client_address
    
            # Receive the data in small chunks and retransmit it
            while wearSocketRunning:
                global wearReceivedEventCounter
                wearReceivedEventCounter = wearReceivedEventCounter + 1
                global receivedWearMessage
                global wearReceivedFromSender
                wearReceivedFromSender=True
                data = connection.recv(10000) # kinda ugly hack. If incomming message will be longer this will spill.
                #receivedNoldusMessage = data
                
                #if (not noldusReceivedFromSender): #clear data
                #    print 'Got first message from Tobii. Switching to real data mode.'
                #    noldusReceivedFromSender = True
                #    receivedNoldusMessage=[]
                    
                #receivedWearMessage.append(data)
                if wearDataLocalFileLogging:
                    f = open(wearDataLocalFileLoggingFileName, 'a')
                    f.write(data)
                    f.close()
                #fata ='{"timestamp":1454328042855,"z":1.1598410606384277,"y":1.7661726474761963,"x":-9.566631317138672}'
                #receivedWearMessage.append(json.loads(fata))
                try:
                    recv = json.loads(data)
                    #receivedWearMessage.append(recv) // from now on received is list... 
                    receivedWearMessage = receivedWearMessage + recv
                    #receivedWearMessage.append(json.loads(data))
                except:
                    print 'Exception while parsing received JSON message from wear.'
                    if wearDataLocalFileLogging:
                        f = open(wearDataLocalFileLoggingFileName, 'a')
                        f.write('Exception while parsing received JSON message:')
                        f.write(data)
                        f.close()                        
                
                print >>sys.stderr, 'received "%s"' % data
                if data:
                    #print >>sys.stderr, 'Server socket for incomming data: sending data back to the client'
                    #connection.sendall(data)
                    print >>sys.stderr, 'Since lazy Marko did not implement it jet, NOT sending received data back to Android.'
                else:
                    print >>sys.stderr, 'Server socket for incomming data: no more data from', client_address
                    break
                
        finally:
            # Clean up the connection
            connection.shutdown(1);
            connection.close()
            print 'Closing incomming data socket connection.'
    print 'Finished server socket for incomming data thread'
# start listening socket in thread
# About threads:  http://docs.python.org/2/library/threading.html#thread-objects
listenWearSocketThread = threading.Thread(target=listenWearSocket, args=())
listenWearSocketThread.start() 

############################################################################
print "LUCAMI gateway Accel module starting."

# https://docs.python.org/2/library/socket.html
def listenAccelSocket():
    global multiLuxAccelSocketRunning
    # Create a TCP/IP socket
    sock =socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    global multiLuxAccelAddress
    global multiLuxAccelPort
    server_address = (multiLuxAccelAddress,multiLuxAccelPort)
    # a different way of writing it out without writing it to .log
    print >>sys.stderr, 'Server socket for incomming data: starting up on %s port %s' % server_address
    sock.bind(server_address)
    
    global multiLuxAccelDataLocalFileLogging
    global multiLuxAccelDataLocalFileLoggingFileName
    sock.listen(1)
    while multiLuxAccelSocketRunning:
        print >>sys.stderr, 'Server socket for incomming data: waiting for a connection'
        connection, client_address = sock.accept()
        
        
        #https://wiki.python.org/moin/HandlingExceptions
        try:
            print >>sys.stderr, 'Server socket for incomming data: connection from', client_address
            
            while multiLuxAccelSocketRunning:
                global multiLuxAccelReceivedEventCounter
                multiLuxAccelReceivedEventCounter = multiLuxAccelReceivedEventCounter + 1
                global receivedMultiLuxAccel
                global multiLuxAccelReceivedFromSender
                multiLuxAccelReceivedFromSender = True
                data = connection.recv(10000) 
                # 

                if multiLuxAccelDataLocalFileLogging:
                    # for console data logging
                    f =open(multiLuxAccelDataLocalFileLoggingFileName,'a')
                    f.write(data)
                    f.write('\n')
                    f.close()
                    
                try:
                    print data;
                    # https://docs.python.org/2/library/json.html
                    recv = json.loads(data)
                    # saving data in this variable
                    receivedMultiLuxAccel = receivedMultiLuxAccel + recv
                    # vstavimo meritev še v databazo!
                    ###########################################################
                    # mogoče ne bo hotlo vzet recv kot json? ali pa ga podamo direkt kot data?
                    # http://docs.python-requests.org/en/latest/user/quickstart/#more-complicated-post-requests
                    # r=requests.post(phpAccel, data = data)
                    # data je že v primernem json formatu (ki smo ga kreirali v demo z json.dumps) in samo naložimo!
                    
                    # print r.status_code, r.reason
                    ###########################################################
                    
                except:
                    print "Unexpected error:", sys.exc_info()
                    # print 'Exception while parsing received JSON message from Accel.'
                    if multiLuxAccelDataLocalFileLogging:
                        # for console data logging
                        f = open(multiLuxAccelDataLocalFileLoggingFileName,'a')
                        f.write('Exception while parsing received JSON message')
                        f.write(data)
                        f.close()		
                    print >>sys.stderr, 'received "%s"' % data
                    

                if data:
                    print >>sys.stderr, 'Server socket for incomming data:NOT sending data back to the client'

                else:
                    print >>sys.stderr, 'Server socket for incomming data: no more data from', client_address
                    break 
        finally:
            connection.shutdown(1)
            connection.close()
            print 'Closing incomming data socket connection.'
    print 'Finished server socket for incomming data thread'
	
listenAccelSocket = threading.Thread(target=listenAccelSocket,args=())
listenAccelSocket.start()





 

print "LUCAMI gateway GSR module starting."

# https://docs.python.org/2/library/socket.html
def listenGSRSocket():
    global multiLuxGSRSocketRunning
    # Create a TCP/IP socket
    sock =socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    global multiLuxGSRAddress
    global multiLuxGSRPort
    server_address = (multiLuxGSRAddress,multiLuxGSRPort)
    # a different way of writing it out without writing it to .log
    print >>sys.stderr, 'Server socket for incomming data: starting up on %s port %s' % server_address
    sock.bind(server_address)
    
    global multiLuxGSRDataLocalFileLogging
    global multiLuxGSRDataLocalFileLoggingFileName
    sock.listen(1)
    while multiLuxGSRSocketRunning:
        print >>sys.stderr, 'Server socket for incomming data: waiting for a connection'
        connection, client_address = sock.accept()
        
        
        #https://wiki.python.org/moin/HandlingExceptions
        try:
            print >>sys.stderr, 'Server socket for incomming data: connection from', client_address
            
            while multiLuxGSRSocketRunning:
                global multiLuxGSRReceivedEventCounter
                multiLuxGSRReceivedEventCounter = multiLuxGSRReceivedEventCounter + 1
                global receivedMultiLuxGSR
                global multiLuxGSRReceivedFromSender
                multiLuxGSRReceivedFromSender = True
                data = connection.recv(10000)			

                if multiLuxGSRDataLocalFileLogging:
                    # for console data logging
                    f =open(multiLuxGSRDataLocalFileLoggingFileName,'a')
                    f.write(data)
                    f.write('\n')
                    f.close()
                    
                try:
                    recv = json.loads(data)
                    receivedMultiLuxGSR = receivedMultiLuxGSR + recv
                    #print(recv)
                  
                   # r=requests.post(phpGSR, data = data)

                    
                except:
                    
                    print "Unexpected error:", sys.exc_info()
                    if multiLuxGSRDataLocalFileLogging:
                        # for console data logging
                        f = open(multiLuxGSRDataLocalFileLoggingFileName,'a')
                        f.write('Exception while parsing received JSON message')
                        f.write(data)
                        f.close()		
                    print >>sys.stderr, 'received "%s"' % data

                if data:
                    print >>sys.stderr, 'Server socket for incomming data: NOT sending data back to the client'
                else:
                    print >>sys.stderr, 'Server socket for incomming data: no more data from', client_address
                    break 
        finally:
            connection.shutdown(1)
            connection.close()
            print 'Closing incomming data socket connection.'
    print 'Finished server socket for incomming data thread'
	
listenGSRSocket = threading.Thread(target=listenGSRSocket,args=())
listenGSRSocket.start()

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

#@app.route('/cors', method=['OPTIONS', 'GET'])
@app.route(tobiiEyeTrackerServerHostRoute, method=['OPTIONS', 'GET'])
def tobiiEyeTrackerResponder():
    response.headers['Content-type'] = 'application/json'
    #i=i+1
    global receivedTobiiMessage
    #i=i+1
    global tobiiEyeTrackerReceivedEventCounter
    data = {}
    #data['mykey']='myvalue'
    data['receivedEventCounter']=tobiiEyeTrackerReceivedEventCounter
    data['TobiiDetailedLog'] = receivedTobiiMessage
    json_data = json.dumps(data)
    #clear message buffer
    if tobiiReceivedFromSender:
        receivedTobiiMessage=[]
    else:
        print 'Sending emulated response for Tobii, since no data arrived jet from tobii.'
            
    #return '[1]'
    
    return json_data
    


@app.route(noldusFaceReaderServerHostRoute, method=['OPTIONS', 'GET'])
def noldusFaceReaderDataResponder():
    response.headers['Content-type'] = 'application/json'
    #i=i+1
    global noldusFaceReaderReceivedEventCounter
    global receivedNoldusMessage
    data = {}
    #data['mykey']='myvalue'
    data['receivedEventCounter']=noldusFaceReaderReceivedEventCounter
    data['NoldusDetailedLog'] = parseNoldus(receivedNoldusMessage)
    
    json_data = json.dumps(data)
    
    #clear message buffer
    if noldusReceivedFromSender:
        receivedNoldusMessage=[]
    else:
        print 'Sending emulated response for Noldus, since no data arrived jet from Noldus.'
    #return '[1]'
    
    return json_data
    
    
@app.route(wearServerHostRoute, method=['OPTIONS', 'GET'])
def wearDataResponder():
    response.headers['Content-type'] = 'application/json'
    #i=i+1
    global wearReceivedEventCounter
    global receivedWearMessage
    data = {}
    #data['mykey']='myvalue'
    data['receivedEventCounter']=wearReceivedEventCounter
    data['wearLog'] = receivedWearMessage
    json_data = json.dumps(data)
    #clear message buffer
    if wearReceivedFromSender:
        receivedWearMessage=[]
    else:
        print 'Sending emulated response for Wear, since no data arrived jet from Noldus.'
    #return '[1]'
    
    return json_data   
  

# @Primoz kocevar  
# outdated and can be deleted if noone is using it
#####################################################################
@app.route(multiLuxAccelHostRoute, method=['OPTIONS', 'GET'])
def multiLuxAccelResponder():
    response.headers['Content-type'] = 'application/json'
    global receivedMultiLuxAccel
    global multiLuxAccelReceivedEventCounter
    data = {}
    data['receivedEventCounter']=multiLuxAccelReceivedEventCounter
    data['AccelDetailedLog']=receivedMultiLuxAccel
    json_data = json.dumps(data)
    #clear message buffer
    if multiLuxAccelReceivedFromSender:
        receivedMultiLuxAccel=[]
    else:
        print 'Sending emulated data from Accel, since no data arrived jet from MultiLux'
    
    return json_data


@app.route(multiLuxGSRHostRoute, method=['OPTIONS', 'GET'])
def multiLuxGSRResponder():
    response.headers['Content-type'] = 'application/json'
    global receivedMultiLuxGSR
    global multiLuxGSRReceivedEventCounter
    data = {}
    data['receivedEventCounter']=multiLuxGSRReceivedEventCounter
    data['GSRDetailedLog']=receivedMultiLuxGSR
    json_data = json.dumps(data)
    #clear message buffer
    if multiLuxGSRReceivedFromSender:
        receivedMultiLuxGSR=[]
    else:
        print 'Sending emulated data from GSR, since no data arrived jet from MultiLux'
    
    return json_data    
      
#####################################################################
# clears all data buffers
@app.route(emptyDataServerHostRoute, method=['OPTIONS', 'GET'])
def emptyDataDataResponder():
    response.headers['Content-type'] = 'application/json'
    #i=i+1
    #global wearReceivedEventCounter
    global receivedWearMessage
    global receivedNoldusMessage
    global receivedTobiiMessage
    #data = {}
    #data['mykey']='myvalue'
    #data['receivedEventCounter']=wearReceivedEventCounter
    #data['wearLog'] = receivedWearMessage
    #json_data = json.dumps(data)
    #clear message buffer
    #if wearReceivedFromSender:
    #    receivedWearMessage=[]
    #else:
    #    print 'Sending emulated response for Wear, since no data arrived jet from Noldus.'
    print 'Clearing all data buffers.'    
    receivedWearMessage=[]
    receivedNoldusMessage=[]
    receivedTobiiMessage=[]
    return '[1]'
    
    #return json_data      
    
app.install(EnableCors())
print 'Starting http server on http://',serverHostIP,':',serverHostPort,tobiiEyeTrackerServerHostRoute
app.run(host=serverHostIP, port=serverHostPort)   

print 'Cleanup: http server stopped.'
print 'Cleanup: Stopping incomming tobii data socket server.'
tobiiSocketRunning = False
#send one last message to socket thread to disconnect. Ugly hack. Not working until other side client is connected.
tobiiClientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tobiiServer_address = (tobiiDotNetAddress, tobiiDotNeAppPort)
tobiiClientSock.connect(tobiiServer_address)  
tobiiClientSock.sendall('Die!')
tobiiClientSock.close()

print 'Cleanup: Stopping incomming noldus data socket server.'
noldusSocketRunning = False
#send one last message to socket thread to disconnect. Ugly hack. Not working until other side client is connected.
noldusClientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
noldusServer_address = (faceReaderDotNetAddress, faceReaderDotNeAppPort)
noldusClientSock.connect(noldusServer_address)  
noldusClientSock.sendall('Die!')
noldusClientSock.close()

print 'Cleanup: Stopping incomming wear data socket server.'
wearSocketRunning = False
#send one last message to socket thread to disconnect. Ugly hack. Not working until other side client is connected.
wearClientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
wearServer_address = (wearSocketAddress, wearSocketPort)
wearClientSock.connect(wearServer_address)  
wearClientSock.sendall('Die!')
wearClientSock.close()

print 'Cleanup: Stopping incomming Accel data socket server.'
multiLuxAccelSocketRunning = False
multiLuxAccelClientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
multiLuxAccelServer_address = (multiLuxAccelAddress,multiLuxAccelPort)
multiLuxAccelClientSock.connect(multiLuxAccelServer_address)
multiLuxAccelClientSock.sendall('Die!')
multiLuxAccelClientSock.close()

print 'Cleanup: Stopping incomming GSR data socket server.'
multiLuxGSRSocketRunning = False
multiLuxGSRClientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
multiLuxGSRServer_address = (multiLuxGSRAddress,multiLuxGSRPort)
multiLuxGSRClientSock.connect(multiLuxGSRServer_address)
multiLuxGSRClientSock.sendall('Die!')
multiLuxGSRClientSock.close()

    
# this should finish the program. Currently does not work, since socket does not disconnect.
listeningTobiiSocketThread.join()
listeningNoldusSocketThread.join()
listenWearSocketThread.join()
listenAccelSocket.join()
listenGSRSocket.join()

