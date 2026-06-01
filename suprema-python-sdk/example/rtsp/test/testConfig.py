import grpc
import rtsp_pb2

from example.cli.input import UserInput

class TestConfig:
  rtspSvc = None

  def __init__(self, svc): 
    self.rtspSvc = svc

  def test(self, deviceID, config):
    try:
      # Backup the original configuration
      origConfig = rtsp_pb2.RTSPConfig()
      origConfig.CopyFrom(config)

      config.serverURL = "rtsp.server.com"
      config.serverPort = 554
      config.userID = "RTSP User ID"
      config.userPW = "2378129307"
      config.enabled = True

      self.rtspSvc.setConfig(deviceID, config)
      
      UserInput.pressEnter('>> Press ENTER if you finish testing this mode.\n')          

      # Restore the original configuration
      self.rtspSvc.setConfig(deviceID, origConfig)

    except grpc.RpcError as e:
      print(f'Cannot finish the config test: {e}', flush=True)
      raise    