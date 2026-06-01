import grpc
import user_pb2
import finger_pb2
import face_pb2

NUM_OF_NEW_USER = 3
START_USER_ID = 10000000
TEMPLATE_FORMAT = finger_pb2.TEMPLATE_FORMAT_SUPREMA
QUALITY_THRESHOLD = 50

def getNewUserIDs():
  userIDs = []

  for i in range(0, NUM_OF_NEW_USER):
    userIDs.append(str(START_USER_ID + i))

  return userIDs


def makeNewUser():
  userInfos = []

  for i in range(0, NUM_OF_NEW_USER):
    userHdr = user_pb2.UserHdr(ID=str(START_USER_ID + i), userFlag = user_pb2.USER_FLAG_CREATED)
    userInfo = user_pb2.UserInfo(hdr=userHdr)

    userInfos.append(userInfo)

  return userInfos

def testSetFinger(userSvc, fingerSvc, deviceID, userID):
  userIDs = [userID]

  try:
    users = userSvc.getUser(deviceID, userIDs)

    print(f'\nUser without fingerprint: \n{users[0]}')

    print('>>> Scan a finger...', flush=True)

    templateData1 = fingerSvc.scan(deviceID, TEMPLATE_FORMAT, QUALITY_THRESHOLD)

    print('>>> Scan the same finger again...', flush=True)

    templateData2 = fingerSvc.scan(deviceID, TEMPLATE_FORMAT, QUALITY_THRESHOLD)

    fingerData = finger_pb2.FingerData(templates=[templateData1, templateData2])
    userFingers = [user_pb2.UserFinger(userID=userID, fingers=[fingerData])]

    userSvc.setFinger(deviceID, userFingers)

    users = userSvc.getUser(deviceID, userIDs)

    print(f'\nUser with fingerprint: \n{users[0]}')

  except grpc.RpcError as e:
    print(f'Cannot complete the set finger test: {e}')    


def testSetFace(userSvc, faceSvc, deviceID, userID):
  userIDs = [userID]

  try:
    users = userSvc.getUser(deviceID, userIDs)

    print(f'\nUser without face: \n{users[0]}')

    print('>>> Scan a face...', flush=True)

    faceData = faceSvc.scan(deviceID, face_pb2.BS2_FACE_ENROLL_THRESHOLD_DEFAULT)

    userFaces = [user_pb2.UserFace(userID=userID, faces=[faceData])]

    userSvc.setFace(deviceID, userFaces)

    users = userSvc.getUser(deviceID, userIDs)

    print(f'\nUser with face: \n{users[0]}')

  except grpc.RpcError as e:
    print(f'Cannot complete the set face test: {e}')    


def testUser(userSvc, fingerSvc, faceSvc, deviceID, capabilityInfo):
  try:
    userList = userSvc.getList(deviceID)
    print(f'Initial user list: {userList}', flush=True)

    userIDs = []
    for user in userList:
      userIDs.append(user.ID)

    userInfos = userSvc.getUser(deviceID, userIDs)

    for info in userInfos:
      print(f'\nUser: \n{info}', flush=True)

    userSvc.enroll(deviceID, makeNewUser(), True)

    userList = userSvc.getList(deviceID)
    print(f'User list after adding new users: {userList}', flush=True)

    if capabilityInfo.fingerSupported:
      testSetFinger(userSvc, fingerSvc, deviceID, getNewUserIDs()[0])

    if capabilityInfo.faceSupported:
      testSetFace(userSvc, faceSvc, deviceID, getNewUserIDs()[0])

    userSvc.delete(deviceID, getNewUserIDs())

    userList = userSvc.getList(deviceID)
    print(f'User list after deleting new users: {userList}', flush=True)

  except grpc.RpcError as e:
    print(f'Cannot complete the user test: {e}')    