import grpc
import tna_pb2

from example.cli.input import UserInput

class TestConfig:
  tnaSvc = None

  def __init__(self, svc): 
    self.tnaSvc = svc

  def test(self, deviceID):
    try:
      # Backup the original configuration
      origConfig = self.tnaSvc.getConfig(deviceID)
      print(f'\nOriginal T&A Config: \n{origConfig}', flush=True)

      print(f'\n===== Test for TNAConfig =====\n', flush=True)

      # (1) BY_USER
      config = tna_pb2.TNAConfig()
      config.mode = tna_pb2.BY_USER
      config.labels[:] = ["In", "Out", "Scheduled In", "Fixed Out"]
      self.tnaSvc.setConfig(deviceID, config)
      
      print(f'(1) The T&A mode is set to BY_USER(optional). You can select a T&A key before authentication. Try to authenticate after selecting a T&A key.\n')
      UserInput.pressEnter('>> Press ENTER if you finish testing this mode.\n')

      # (2) IsRequired
      config.isRequired = True
      self.tnaSvc.setConfig(deviceID, config)

      print(f'(2) The T&A mode is set to BY_USER(mandatory). Try to authenticate without selecting a T&A key.\n')
      UserInput.pressEnter('>> Press ENTER if you finish testing this mode.\n')

      # (3) LAST_CHOICE
      config.mode = tna_pb2.LAST_CHOICE
      self.tnaSvc.setConfig(deviceID, config)

      print(f'(3) The T&A mode is set to LAST_CHOICE. The T&A key selected by the previous user will be used. Try to authenticate multiple users.\n')
      UserInput.pressEnter('>> Press ENTER if you finish testing this mode.\n')      

      # (4) BY_SCHEDULE
      config.mode = tna_pb2.BY_SCHEDULE
      config.schedules[:] = [0, 0, 1] # Always for KEY_3 (Scheduled In)
      self.tnaSvc.setConfig(deviceID, config)

      print(f'(4) The T&A mode is set to BY_SCHEDULE. The T&A key will be determined automatically by schedule. Try to authenticate without selecting a T&A key.\n')
      UserInput.pressEnter('>> Press ENTER if you finish testing this mode.\n')          

      # (5) FIXED 
      config.mode = tna_pb2.FIXED
      config.key = tna_pb2.KEY_4
      self.tnaSvc.setConfig(deviceID, config)

      print(f'(5) The T&A mode is set to FIXED(KEY_4). Try to authenticate without selecting a T&A key.\n')
      UserInput.pressEnter('>> Press ENTER if you finish testing this mode.\n')        

      return origConfig

    except grpc.RpcError as e:
      print(f'Cannot finish the config test: {e}', flush=True)
      raise