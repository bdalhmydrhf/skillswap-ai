import grpc
import time
import user_pb2
import device_pb2
import auth_pb2

class TestUser:
  userSvc = None

  def __init__(self, userSvc): 
    self.userSvc = userSvc

  def enrollUser(self, deviceID, extendedAuthSupported):
    try:
      userHdrs = self.userSvc.getList(deviceID)
      print(f'Existing User List: {userHdrs}\n', flush=True)

      newUserID = "%d" % int(time.time())
      newUserHdr = user_pb2.UserHdr(ID=newUserID, userFlag = user_pb2.USER_FLAG_CREATED)
      newUser = user_pb2.UserInfo(hdr=newUserHdr, setting=user_pb2.UserSetting())

      if extendedAuthSupported:
        newUser.setting.cardAuthExtMode = auth_pb2.AUTH_EXT_MODE_CARD_ONLY
        newUser.setting.fingerAuthExtMode = auth_pb2.AUTH_EXT_MODE_FINGERPRINT_ONLY
        newUser.setting.faceAuthExtMode = auth_pb2.AUTH_EXT_MODE_FACE_ONLY
      else:
        newUser.setting.cardAuthMode = auth_pb2.AUTH_MODE_CARD_ONLY
        newUser.setting.biometricAuthMode = auth_pb2.AUTH_MODE_BIOMETRIC_ONLY

      self.userSvc.enroll(deviceID, [newUser], True)

      userInfos = self.userSvc.getUser(deviceID, [newUserID])
      print(f'Test User: {userInfos[0]}\n', flush=True)

      return newUserID
    except grpc.RpcError as e:
      print(f'Cannot enroll the test user: {e}', flush=True)   
      raise




    