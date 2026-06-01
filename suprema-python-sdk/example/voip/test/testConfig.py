import grpc
import voip_pb2

from example.cli.input import UserInput

class TestConfig:
  voipSvc = None

  def __init__(self, svc): 
    self.voipSvc = svc

  def test(self, deviceID, config):
    try:
      # Backup the original configuration
      origConfig = voip_pb2.VOIPConfig()
      origConfig.CopyFrom(config)

      config.serverURL = "voip.server.com"
      config.serverPort = 554
      config.userID = "VOIP User ID"
      config.userPW = "2378129307"
      config.enabled = True

      self.voipSvc.setConfig(deviceID, config)
      
      UserInput.pressEnter('>> Press ENTER if you finish testing this mode.\n')          

      # Restore the original configuration
      self.voipSvc.setConfig(deviceID, origConfig)

    except grpc.RpcError as e:
      print(f'Cannot finish the config test: {e}', flush=True)
      raise    