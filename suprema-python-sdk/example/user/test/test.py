import grpc
import logging
import connect_pb2

from testEvent import TestEvent
from testUser import TestUser
from testAuth import TestAuth
from testCard import TestCard
from testFinger import TestFinger
from testFace import TestFace

from example.client.client import GatewayClient
from example.connect.connect import ConnectSvc
from example.user.user import UserSvc
from example.event.event import EventSvc
from example.device.device import DeviceSvc
from example.auth.auth import AuthSvc
from example.card.card import CardSvc
from example.finger.finger import FingerSvc
from example.face.face import FaceSvc

GATEWAY_CA_FILE = '../../../../cert/gateway/ca.crt'
GATEWAY_IP = '192.168.8.98'
GATEWAY_PORT = 4000

DEVICE_IP = '192.168.8.227'
DEVICE_PORT = 51211
USE_SSL = False

CODE_MAP_FILE = '../../event/event_code.json'

def test():
  channel = None
  connectSvc = None
  devID = 0

  try:
    client = GatewayClient(GATEWAY_IP, GATEWAY_PORT, GATEWAY_CA_FILE)
    channel = client.getChannel()
    
    connectSvc = ConnectSvc(channel)
    connInfo = connect_pb2.ConnectInfo(IPAddr=DEVICE_IP, port=DEVICE_PORT, useSSL=USE_SSL)

    devID = connectSvc.connect(connInfo)

    deviceSvc = DeviceSvc(channel)
    capability = deviceSvc.getCapability(devID)

    authSvc = AuthSvc(channel)
    testAuth = TestAuth(authSvc)
    origAuthConfig = testAuth.prepareAuthConfig(devID)

    userSvc = UserSvc(channel)
    testUser = TestUser(userSvc)
    testUserID = testUser.enrollUser(devID, capability.extendedAuthSupported)

    eventSvc = EventSvc(channel)
    eventSvc.initCodeMap(CODE_MAP_FILE)
    testEvent = TestEvent(eventSvc)
    testEvent.startMonitoring(devID)

    if capability.cardInputSupported: 
      cardSvc = CardSvc(channel)
      TestCard(cardSvc, userSvc).test(devID, testUserID)
    else:
      print(f'!! The device {devID} does not support cards. Skip the card test.', flush=True)

    if capability.fingerprintInputSupported: 
      fingerSvc = FingerSvc(channel)
      TestFinger(fingerSvc, userSvc).test(devID, testUserID)
    else:
      print(f'!! The device {devID} does not support fingerprints. Skip the fingerprint test.', flush=True)      

    if capability.faceInputSupported: 
      faceSvc = FaceSvc(channel)
      TestFace(faceSvc, userSvc).test(devID, testUserID)
    else:
      print(f'!! The device {devID} does not support faces. Skip the face test.', flush=True)         

    testAuth.test(devID, capability.extendedAuthSupported)
    testEvent.test(devID, testUserID)    

    authSvc.setConfig(devID, origAuthConfig)
    userSvc.delete(devID, [testUserID])
    testEvent.stopMonitoring(devID)
    connectSvc.disconnect([devID])
    channel.close()    
  
  except grpc.RpcError as e:
    print(f'Cannot finish the user test: {e}', flush=True)
    
    if devID != 0:
      connectSvc.disconnect([devID])
      channel.close()   


if __name__ == '__main__':
    logging.basicConfig()
    test()
