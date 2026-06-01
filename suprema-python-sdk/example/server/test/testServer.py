import grpc
import server_pb2
import user_pb2
import card_pb2
import finger_pb2
import auth_pb2
import threading
from example.cli.input import UserInput

QUEUE_SIZE = 16
TEST_USER_ID = '1234'

class TestServer:
  serverSvc = None
  authSvc = None
  reqCh = None
  returnError = False

  def __init__(self, serverSvc, authSvc): 
    self.serverSvc = serverSvc
    self.authSvc = authSvc

  def test(self, deviceID):
    try:
      # Backup the auth config
      origAuthConfig = self.authSvc.getConfig(deviceID)

      testConfig = auth_pb2.AuthConfig()
      testConfig.CopyFrom(origAuthConfig)
      testConfig.useServerMatching = True

      self.authSvc.setConfig(deviceID, testConfig)

      self.testVerify(deviceID)
      self.testIdentify(deviceID)

      # Restore the original auth config
      self.authSvc.setConfig(deviceID, origAuthConfig)

    except grpc.RpcError as e:
      print(f'Cannot finish the server test: {e}', flush=True)
      raise

  def testVerify(self, deviceID):
    try:
      self.reqCh = self.serverSvc.subscribe(QUEUE_SIZE)
      self.returnError = True

      verifyThread = threading.Thread(target=self.handleVerify)
      verifyThread.start()

      print(f'\n===== Server Matching: Verify Test =====\n', flush=True)

      print(f'>> Try to authenticate a card. It should fail since the device gateway will return an error code to the request.', flush=True)
      UserInput.pressEnter('>> Press ENTER for the next test.\n')  

      self.returnError = False
      print(f'>> Try to authenticate a card. The gateway will return SUCCESS with user information this time. The result will vary according to the authentication modes of the devices.', flush=True)
      UserInput.pressEnter('>> Press ENTER for the next test.\n')  

      self.reqCh.cancel()
      self.serverSvc.unsubscribe()

    except grpc.RpcError as e:
      print(f'Cannot test verify: {e}', flush=True) 
      raise        

  def handleVerify(self):
    try:
      for req in self.reqCh:
        if req.reqType != server_pb2.VERIFY_REQUEST:
          print(f'!! Request type is not VERIFY_REQUEST. Just ignore it!', flush=True)
          break

        if self.returnError:
          print(f'## Gateway returns VERIFY_FAIL.', flush=True)
          self.serverSvc.handleVerify(req, server_pb2.VERIFY_FAIL, None)
        else:
          userHdr = user_pb2.UserHdr(ID=TEST_USER_ID, userFlag = user_pb2.USER_FLAG_CREATED, numOfCard=1)
          cardData = card_pb2.CSNCardData(data=req.verifyReq.cardData)
          userInfo = user_pb2.UserInfo(hdr=userHdr, cards=[cardData])

          self.serverSvc.handleVerify(req, server_pb2.SUCCESS, userInfo)

    except grpc.RpcError as e:
      if e.code() == grpc.StatusCode.CANCELLED:
        print('Subscription is cancelled', flush=True)    
      else:
        print(f'Cannot get server matching requests: {e}') 

  def testIdentify(self, deviceID):
    try:
      self.reqCh = self.serverSvc.subscribe(QUEUE_SIZE)
      self.returnError = True

      identifyThread = threading.Thread(target=self.handleIdentify)
      identifyThread.start()

      print(f'\n===== Server Matching: Identify Test =====\n', flush=True)

      print(f'>> Try to authenticate a fingerprint. It should fail since the device gateway will return an error code to the request.', flush=True)
      UserInput.pressEnter('>> Press ENTER for the next test.\n')  

      self.returnError = False
      print(f'>> Try to authenticate a fingerprint. The gateway will return SUCCESS with user information this time. The result will vary according to the authentication modes of the devices.', flush=True)
      UserInput.pressEnter('>> Press ENTER for the next test.\n')  

      self.reqCh.cancel()
      self.serverSvc.unsubscribe()

    except grpc.RpcError as e:
      print(f'Cannot test identify: {e}', flush=True) 
      raise        

  def handleIdentify(self):
    try:
      for req in self.reqCh:
        if req.reqType != server_pb2.IDENTIFY_REQUEST:
          print(f'!! Request type is not IDENTIFY_REQUEST. Just ignore it!', flush=True)
          break

        if self.returnError:
          print(f'## Gateway returns IDENTIFY_FAIL.', flush=True)
          self.serverSvc.handleIdentify(req, server_pb2.IDENTIFY_FAIL, None)
        else:
          userHdr = user_pb2.UserHdr(ID=TEST_USER_ID, userFlag = user_pb2.USER_FLAG_CREATED, numOfFinger=1)
          fingerData = finger_pb2.FingerData(templates=[req.identifyReq.templateData, req.identifyReq.templateData,])
          userInfo = user_pb2.UserInfo(hdr=userHdr, fingers=[fingerData])

          self.serverSvc.handleIdentify(req, server_pb2.SUCCESS, userInfo)

    except grpc.RpcError as e:
      if e.code() == grpc.StatusCode.CANCELLED:
        print('Subscription is cancelled', flush=True)    
      else:
        print(f'Cannot get server matching requests: {e}') 

