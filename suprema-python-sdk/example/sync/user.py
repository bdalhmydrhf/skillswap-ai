import grpc

import user_pb2
from example.err.err import getMultiError

BS2_EVENT_USER_ENROLL_SUCCESS = 0x2000
BS2_EVENT_USER_UPDATE_SUCCESS = 0x2200
BS2_EVENT_USER_DELETE_SUCCESS = 0x2400
BS2_EVENT_USER_DELETE_ALL_SUCCESS = 0x2600

class UserMgr:
  userSvc = None
  cardSvc = None
  testConfig = None
  deviceMgr = None
  eventMgr = None

  enrolledIDs = []

  def __init__(self, userSvc, cardSvc, testConfig, deviceMgr, eventMgr): 
    self.userSvc = userSvc
    self.cardSvc = cardSvc
    self.testConfig = testConfig
    self.deviceMgr = deviceMgr
    self.eventMgr = eventMgr

  def enrollUser(self, userID):
    try:
      enrollDeviceID = self.testConfig.getConfigData()['enroll_device']['device_id']
      print(f'>>> Place a unregistered CSN card on the device {enrollDeviceID}...', flush=True)

      cardData = self.cardSvc.scan(enrollDeviceID)

      if cardData.CSNCardData is None:
        print('This test does not support a smart card', flush=True) 
        return

      userHdr = user_pb2.UserHdr(ID=userID, userFlag = user_pb2.USER_FLAG_CREATED, numOfCard=1)
      userInfo = user_pb2.UserInfo(hdr=userHdr, cards=[cardData.CSNCardData])

      self.userSvc.enroll(enrollDeviceID, [userInfo], False)
    except grpc.RpcError as e:
      print(f'Cannot enroll user: {e}')         

  def deleteUser(self, userID):      
    try:
      enrollDeviceID = self.testConfig.getConfigData()['enroll_device']['device_id']
      self.userSvc.delete(enrollDeviceID, [userID])
    except grpc.RpcError as e:
      print(f'Cannot delete user: {e}')  

  def getNewUser(self, deviceID):
    if len(self.enrolledIDs) == 0:
      print('No new user', flush=True)
      return None

    return self.userSvc.getUser(deviceID, self.enrolledIDs)

  def syncUser(self, eventLog):
    try:
      self.eventMgr.printEvent(eventLog)

      # Handle only the events of the enrollment device
      if eventLog.deviceID != self.testConfig.getConfigData()['enroll_device']['device_id']:
        return

      connectedIDs = self.deviceMgr.getConnectedDevices(False)
      targetDeviceIDs = self.testConfig.getTargetDeviceIDs(connectedIDs)

      if len(targetDeviceIDs) == 0:
        print('No device to sync', flush=True)
        return

      if eventLog.eventCode == BS2_EVENT_USER_ENROLL_SUCCESS or eventLog.eventCode == BS2_EVENT_USER_UPDATE_SUCCESS:
        print(f'Trying to synchronize the enrolled user {eventLog.userID}...', flush=True)
        newUserInfos = self.userSvc.getUser(eventLog.deviceID, [eventLog.userID])
        self.userSvc.enrollMulti(targetDeviceIDs, newUserInfos, False)

        try:
          self.enrolledIDs.index(eventLog.userID)
        except ValueError:
          self.enrolledIDs.append(eventLog.userID)

        # Generate a MultiErrorResponse 
        # It should fail since the users are duplicated.   
        # Depends on grpcio-status       
        #try:
        #  self.userSvc.enrollMulti(targetDeviceIDs, newUserInfos, False)
        #except grpc.RpcError as e:
        #  multiError = getMultiError(e)
        #  print(f'Multi error: {multiError}')

      elif eventLog.eventCode == BS2_EVENT_USER_DELETE_SUCCESS:
        print(f'Trying to synchronize the deleted user {eventLog.userID}...', flush=True)
        self.userSvc.deleteMulti(targetDeviceIDs, [eventLog.userID])

        self.enrolledIDs.remove(eventLog.userID)

    except grpc.RpcError as e:
      print(f'Cannot synchronize the user: {e}')  
    


