import grpc
import status_pb2
import action_pb2
import device_pb2

from example.cli.input import UserInput

class TestConfig:
  statusSvc = None

  def __init__(self, svc): 
    self.statusSvc = svc

  def test(self, deviceID):
    try:
      # Backup the original configuration
      origConfig = self.statusSvc.getConfig(deviceID)
      print(f'\nOriginal Config: \n{origConfig}', flush=True)

      testConfig = status_pb2.StatusConfig()
      testConfig.CopyFrom(origConfig)

      self.testLED(deviceID, testConfig)
      self.testBuzzer(deviceID, testConfig)

      # Restore the original configuration 
      self.statusSvc.setConfig(deviceID, origConfig)

    except grpc.RpcError as e:
      print(f'Cannot finish the config test: {e}', flush=True)
      raise

  def testLED(self, deviceID, config):
    print(f'\n===== LED Status Test =====\n', flush=True)
    
    try:
      for i in range(len(config.LEDState)):
        if config.LEDState[i].deviceStatus == status_pb2.DEVICE_STATUS_NORMAL: # Change the LED color of the normal status to yellow
          config.LEDState[i].count = 0 # indefinite

          del config.LEDState[i].signals[:]
          ledSignal = action_pb2.LEDSignal(color=device_pb2.LED_COLOR_YELLOW, duration=2000, delay=0)
          config.LEDState[i].signals.append(ledSignal)
          break
      
      self.statusSvc.setConfig(deviceID, config)

      newConfig = self.statusSvc.getConfig(deviceID)
      print(f'\nNew Config: \n{newConfig}', flush=True)

      print(f'>> The LED color of the normal status is changed to yellow.', flush=True)
      UserInput.pressEnter('>> Press ENTER for the next test.\n')   

    except grpc.RpcError as e:
      print(f'Cannot change the LED status: {e}', flush=True)
      raise

  def testBuzzer(self, deviceID, config):
    print(f'\n===== Buzzer Status Test =====\n', flush=True)
    
    try:
      for i in range(len(config.BuzzerState)):
        if config.BuzzerState[i].deviceStatus == status_pb2.DEVICE_STATUS_FAIL: # Change the buzzer signal for FAIL
          config.BuzzerState[i].count = 1 # indefinite

          del config.BuzzerState[i].signals[:]
          buzzerSignal = action_pb2.BuzzerSignal(tone=device_pb2.BUZZER_TONE_HIGH, duration=500, delay=2) # 2 x 500ms beeps
          config.BuzzerState[i].signals.append(buzzerSignal)
          config.BuzzerState[i].signals.append(buzzerSignal)
          break
      
      self.statusSvc.setConfig(deviceID, config)

      newConfig = self.statusSvc.getConfig(deviceID)
      print(f'\nNew Config: \n{newConfig}', flush=True)

      print(f'>> The buzzer for the FAIL status is changed to two 500ms beeps. Try to authenticate unregistered credentials for the test.', flush=True)
      UserInput.pressEnter('>> Press ENTER for the next test.\n')   

    except grpc.RpcError as e:
      print(f'Cannot change the buzzer status: {e}', flush=True)
      raise
