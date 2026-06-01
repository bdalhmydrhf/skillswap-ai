import grpc
import finger_pb2
import user_pb2

from example.cli.input import UserInput

TEMPLATE_FORMAT = finger_pb2.TEMPLATE_FORMAT_SUPREMA
QUALITY_THRESHOLD = 50

class TestFinger:
  fingerSvc = None
  userSvc = None

  def __init__(self, fingerSvc, userSvc): 
    self.fingerSvc = fingerSvc
    self.userSvc = userSvc

  def test(self, deviceID, userID):
    try:
      print(f'\n===== Finger Test =====\n', flush=True)

      fingerData = finger_pb2.FingerData()

      print(f'>> Place a finger on the device...', flush=True)
      fingerData.templates.append(self.fingerSvc.scan(deviceID, TEMPLATE_FORMAT, QUALITY_THRESHOLD))

      print(f'>> Place the same finger again on the device...', flush=True)
      fingerData.templates.append(self.fingerSvc.scan(deviceID, TEMPLATE_FORMAT, QUALITY_THRESHOLD))

      userFinger = user_pb2.UserFinger(userID=userID, fingers=[fingerData])
      self.userSvc.setFinger(deviceID, [userFinger])

      UserInput.pressEnter('>> Try to authenticate the enrolled finger. And, press ENTER to end the test.\n')

    except grpc.RpcError as e:
      print(f'Cannot complete the finger test: {e}', flush=True)   
      raise




    