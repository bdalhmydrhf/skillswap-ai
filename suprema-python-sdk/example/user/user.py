import grpc

import user_pb2_grpc
import user_pb2


class UserSvc:
  stub = None

  def __init__(self, channel): 
    try:
      self.stub = user_pb2_grpc.UserStub(channel)
    except grpc.RpcError as e:
      print(f'Cannot get the user stub: {e}')
      raise

  def getList(self, deviceID):
    try:
      response = self.stub.GetList(user_pb2.GetListRequest(deviceID=deviceID))
      return response.hdrs
    except grpc.RpcError as e:
      print(f'Cannot get the user list: {e}')
      raise

  def getUser(self, deviceID, userIDs, mask=user_pb2.USER_MASK_ALL):
    try:
      if mask == user_pb2.USER_MASK_ALL:
        response = self.stub.Get(user_pb2.GetRequest(deviceID=deviceID, userIDs=userIDs))
      else:
        response = self.stub.GetPartial(user_pb2.GetPartialRequest(deviceID=deviceID, userIDs=userIDs, infoMask=mask))
      return response.users    
    except grpc.RpcError as e:
      print(f'Cannot get the users: {e}')
      raise

  def enroll(self, deviceID, users, overwrite):
    try:
      self.stub.Enroll(user_pb2.EnrollRequest(deviceID=deviceID, users=users, overwrite=overwrite))
    except grpc.RpcError as e:
      print(f'Cannot enroll users: {e}')
      raise

  def enrollMulti(self, deviceIDs, users, overwrite):
    try:
      self.stub.EnrollMulti(user_pb2.EnrollMultiRequest(deviceIDs=deviceIDs, users=users, overwrite=overwrite))
    except grpc.RpcError as e:
      print(f'Cannot enroll users multi: {e}')
      raise

  def update(self, deviceID, users):
    try:
      self.stub.Update(user_pb2.UpdateRequest(deviceID=deviceID, users=users))
    except grpc.RpcError as e:
      print(f'Cannot update users: {e}')
      raise

  def updateMulti(self, deviceIDs, users):
    try:
      self.stub.UpdateMulti(user_pb2.UpdateMultiRequest(deviceIDs=deviceIDs, users=users))
    except grpc.RpcError as e:
      print(f'Cannot update users multi: {e}')
      raise

  def delete(self, deviceID, userIDs):
    try:
      self.stub.Delete(user_pb2.DeleteRequest(deviceID=deviceID, userIDs=userIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete users: {e}')
      raise

  def deleteAll(self, deviceID):
    try:
      self.stub.DeleteAll(user_pb2.DeleteAllRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all users: {e}')
      raise

  def deleteMulti(self, deviceIDs, userIDs):
    try:
      self.stub.DeleteMulti(user_pb2.DeleteMultiRequest(deviceIDs=deviceIDs, userIDs=userIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete users multi: {e}')
      raise

  def setFinger(self, deviceID, userFingers):
    try:
      self.stub.SetFinger(user_pb2.SetFingerRequest(deviceID=deviceID, userFingers=userFingers))
    except grpc.RpcError as e:
      print(f'Cannot set user fingers: {e}')
      raise

  def getCard(self, deviceID, userIDs):
    try:
      response = self.stub.GetCard(user_pb2.GetCardRequest(deviceID=deviceID, userIDs=userIDs))
      return response.userCards
    except grpc.RpcError as e:
      print(f'Cannot get user cards: {e}')
      raise

  def setCard(self, deviceID, userCards):
    try:
      self.stub.SetCard(user_pb2.SetCardRequest(deviceID=deviceID, userCards=userCards))
    except grpc.RpcError as e:
      print(f'Cannot set user cards: {e}')
      raise

  def setFace(self, deviceID, userFaces):
    try:
      self.stub.SetFace(user_pb2.SetFaceRequest(deviceID=deviceID, userFaces=userFaces))
    except grpc.RpcError as e:
      print(f'Cannot set user faces: {e}')
      raise

  def hashPIN(self, userPIN):
    try:
      response = self.stub.GetPINHash(user_pb2.GetPINHashRequest(PIN=userPIN))
      return response.hashVal
    except grpc.RpcError as e:
      print(f'Cannot hash user PIN: {e}')
      raise 

  def setAccessGroup(self, deviceID, userAccessGroups):
    try:
      self.stub.SetAccessGroup(user_pb2.SetAccessGroupRequest(deviceID=deviceID, userAccessGroups=userAccessGroups))
    except grpc.RpcError as e:
      print(f'Cannot set user access groups: {e}')
      raise 

  def getAccessGroup(self, deviceID, userIDs):
    try:
      response = self.stub.GetAccessGroup(user_pb2.GetAccessGroupRequest(deviceID=deviceID, userIDs=userIDs))
      return response.userAccessGroups
    except grpc.RpcError as e:
      print(f'Cannot get user access groups: {e}')
      raise 

  def setJobCode(self, deviceID, userJobCodes):
    try:
      self.stub.SetJobCode(user_pb2.SetJobCodeRequest(deviceID=deviceID, userJobCodes=userJobCodes))
    except grpc.RpcError as e:
      print(f'Cannot set user job codes: {e}')
      raise 

  def getJobCode(self, deviceID, userIDs):
    try:
      response = self.stub.GetJobCode(user_pb2.GetJobCodeRequest(deviceID=deviceID, userIDs=userIDs))
      return response.userJobCodes
    except grpc.RpcError as e:
      print(f'Cannot get user job codes: {e}')
      raise 

  def getStatistic(self, deviceID):
    try:
      response = self.stub.GetStatistic(user_pb2.GetStatisticRequest(deviceID=deviceID))
      return response.userStatistic
    except grpc.RpcError as e:
      print(f'Cannot get user statistic: {e}')
      raise

  def getUserOverride(self, deviceID, userIDs):
    try:
      response = self.stub.GetUserOverride(user_pb2.GetUserOverrideRequest(deviceID=deviceID, userIDs=userIDs))
      return response.userOverrides
    except grpc.RpcError as e:
      print(f'Cannot get user overrides: {e}')
      raise

  def getAllUserOverride(self, deviceID):
    try:
      response = self.stub.GetAllUserOverride(user_pb2.GetAllUserOverrideRequest(deviceID=deviceID))
      return response.userOverrides
    except grpc.RpcError as e:
      print(f'Cannot get all user overrides: {e}')
      raise

  def setUserOverride(self, deviceID, userOverrides):
    try:
      self.stub.SetUserOverride(user_pb2.SetUserOverrideRequest(deviceID=deviceID, userOverrides=userOverrides))
    except grpc.RpcError as e:
      print(f'Cannot set user overrides: {e}')
      raise

  def deleteUserOverride(self, deviceID, userIDs):
    try:
      self.stub.DeleteUserOverride(user_pb2.DeleteUserOverrideRequest(deviceID=deviceID, userIDs=userIDs))
    except grpc.RpcError as e:
      print(f'Cannot delete user overrides: {e}')
      raise

  def deleteAllUserOverride(self, deviceID):
    try:
      self.stub.DeleteAllUserOverride(user_pb2.DeleteAllUserOverrideRequest(deviceID=deviceID))
    except grpc.RpcError as e:
      print(f'Cannot delete all user overrides: {e}')
      raise