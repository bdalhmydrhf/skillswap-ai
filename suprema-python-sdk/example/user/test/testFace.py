import grpc
import face_pb2
import user_pb2

from example.cli.input import UserInput

ENROLL_THRESHOLD = face_pb2.BS2_FACE_ENROLL_THRESHOLD_DEFAULT

class TestFace:
  faceSvc = None
  userSvc = None

  def __init__(self, faceSvc, userSvc): 
    self.faceSvc = faceSvc
    self.userSvc = userSvc

  def test(self, deviceID, userID):
    try:
      print(f'\n===== Face Test =====\n', flush=True)
      print(f'>> Enroll a face on the device...', flush=True)

      faceData = self.faceSvc.scan(deviceID, ENROLL_THRESHOLD)

      userFace = user_pb2.UserFace(userID=userID, faces=[faceData])
      self.userSvc.setFace(deviceID, [userFace])

      UserInput.pressEnter('>> Try to authenticate the enrolled face. And, press ENTER to end the test.\n')

    except grpc.RpcError as e:
      print(f'Cannot complete the face test: {e}', flush=True)   
      raise




    