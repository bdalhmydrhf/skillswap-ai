import grpc
import user_pb2
import face_pb2
from example.cli.input import UserInput
from FaceEnrollMenu import FaceMenuResourceType, showMenuFace


TEST_USER_STARTTIME = 946684800
TEST_USER_ENDTIME = 1924991999


class FaceUserTest:
  userSvc_ = None
  faceSvc_ = None

  def __init__(self, userSvc, faceSvc):
    self.userSvc_ = userSvc
    self.faceSvc_ = faceSvc

  def updateFaceConfig(self, deviceID):
    try:
      print(f"Get face config from {deviceID}...")
      faceConfig = self.faceSvc_.getConfig(deviceID)
      if not faceConfig:
        print(f'Cannot get the face config from {deviceID}', flush=True)
        return

      print(f'Current face config: {faceConfig}', flush=True)

      changeQuestion = "False" if faceConfig.unableToSaveImageOfVisualFace else "True"
      isYes = UserInput.getBoolean(f"Do you want to change the value of unableToSaveImageOfVisualFace to {changeQuestion}? (Y/N): ")
      if isYes:
        faceConfig.unableToSaveImageOfVisualFace = not faceConfig.unableToSaveImageOfVisualFace
        self.faceSvc_.setConfig(deviceID, faceConfig)
        print(f'Update success=====:\n{faceConfig}\n')
    except grpc.RpcError as e:
      print(f'Cannot update face config to {deviceID}: {e}', flush=True)
      raise
      
  def getUsers(self, deviceID):
    try:
      uIDs = UserInput.getStrings("Please enter userIDs separated by spaces: ")
      if 0 < len(uIDs):
        selectedUsers = self.userSvc_.getUser(deviceID, uIDs)
        print(f'Users=====:\n{selectedUsers}\n')
    except grpc.RpcError as e:
      print(f'Cannot get users from {deviceID}: {e}', flush=True)
      raise

  def removeUsers(self, deviceID):
    try:
      uIDs = UserInput.getStrings("Please enter userIDs separated by spaces: ")
      if 0 < len(uIDs):
        self.userSvc_.delete(deviceID, uIDs)
        print(f'Remove success=====:\n{uIDs}\n')
    except grpc.RpcError as e:
      print(f'Cannot remove users from {deviceID}: {e}', flush=True)

  def enrollUser(self, deviceID):
    try:
      uID = input("Please enter a userID: ")
      if 0 < len(uID):
        numOfFace = UserInput.getInteger("Enter the number of Faces: ", 0)
        hdr = user_pb2.UserHdr(ID = uID, userFlag = user_pb2.USER_FLAG_CREATED, numOfFace = numOfFace)
        userName = f'User{uID}'
        setting = user_pb2.UserSetting(startTime = TEST_USER_STARTTIME, endTime = TEST_USER_ENDTIME)
        faceData = []
        for i in range(numOfFace):
          fromWhere = showMenuFace(prompt=f'Where do you get #{i + 1} face data from?')

          if fromWhere == FaceMenuResourceType.SCAN_FACE.value:
            print(f'>> Scan your face...\n')
            face = self.faceSvc_.scan(deviceID, face_pb2.BS2_FACE_ENROLL_THRESHOLD_DEFAULT)
            faceData.append(face)

          elif fromWhere == FaceMenuResourceType.WITH_IMAGE.value:
            print(f'>> Select the face image you want to enroll.')
            warpedData = self.getFaceImage(deviceID)
            if not warpedData:
              print(f'Normalize failed from image.')
              continue

            face = face_pb2.FaceData(index=i, flag=face_pb2.BS2_FACE_FLAG_EX|face_pb2.BS2_FACE_FLAG_WARPED, imageData=warpedData)
            faceData.append(face)

          elif fromWhere == FaceMenuResourceType.WITH_TEMPLATE.value:
            print(f'>> Select the face image file to extract the template.')
            warpedData = self.getFaceImage(deviceID)
            if not warpedData:
              print(f'Normalize failed from image.')
              continue

            templateData = self.getTemplateData(deviceID, warpedData)
            if not templateData:
              print(f'Extract failed from image.')
              continue

            face = face_pb2.FaceData(index=i, flag=face_pb2.BS2_FACE_FLAG_EX|face_pb2.BS2_FACE_FLAG_TEMPLATE_ONLY, templates=[templateData])
            faceData.append(face)

        userInfo = user_pb2.UserInfo(hdr = hdr, setting = setting, name = userName, faces = faceData)
        self.userSvc_.enroll(deviceID, [userInfo], True)

        print(f'Enroll success=====:\n{uID}\n')
    except grpc.RpcError as e:
      print(f'Cannot enroll the user to {deviceID}: {e}', flush=True)
      raise

  def getFaceImage(self, deviceID):
    try:
      path = input("Enter the image file path: ")
      if path:
        with open(path, 'rb') as f:
          unwarpedData = f.read()
          warpedData = self.faceSvc_.normalize(deviceID, unwarpedData)
          if not warpedData:
            print(f'Cannot normalize the image: {deviceID}', flush=True)
            return None
          
          return warpedData
    except grpc.RpcError as e:
      print(f'Cannot get the face image: {e}', flush=True)
      return None
    except FileNotFoundError as e:
      print(f'Cannot find the file: {path}', flush=True)
      return None
    except IOError as e:
      print(f'Cannot read the file: {path}', flush=True)
      return None
    finally:
      f.close()

    return None

  def getTemplateData(self, deviceID, warpedData):
    try:
      templateData = self.faceSvc_.extract(deviceID, warpedData, True)
      if not templateData:
        print(f'Cannot extract the template data.', flush=True)
        return None

      return templateData
    except grpc.RpcError as e:
      print(f'Cannot extract the template data: {e}', flush=True)
      return None
