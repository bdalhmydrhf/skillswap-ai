import grpc
import thermal_pb2

from example.cli.input import UserInput

class TestConfig:
  thermalSvc = None

  def __init__(self, svc): 
    self.thermalSvc = svc

  def test(self, deviceID, config):
    try:
      # Backup the original configuration
      origConfig = thermal_pb2.ThermalConfig()
      origConfig.CopyFrom(config)

      print(f'\n===== Test for ThermalConfig =====\n', flush=True)

      # Set options for the test
      config.auditTemperature = True # write temperature logs
      config.checkMode = thermal_pb2.HARD # disalllow access when temperature is too high

      # (1) Set check order to AFTER_AUTH
      config.checkOrder = thermal_pb2.AFTER_AUTH 
      self.thermalSvc.setConfig(deviceID, config)
      
      print(f'(1) The Check Order is set to AFTER_AUTH. The device will measure the temperature only after successful authentication. Try to authenticate faces.\n')
      UserInput.pressEnter('>> Press ENTER if you finish testing this mode.\n')

      # (2) Set check order to BEFORE_AUTH
      config.checkOrder = thermal_pb2.BEFORE_AUTH 
      self.thermalSvc.setConfig(deviceID, config)
      
      print(f'(2) The Check Order is set to BEFORE_AUTH. The device will try to authenticate a user only when the user\'s temperature is within the threshold. Try to authenticate faces.\n')
      UserInput.pressEnter('>> Press ENTER if you finish testing this mode.\n')      

      # (3) Set check order to WITHOUT_AUTH
      config.checkOrder = thermal_pb2.WITHOUT_AUTH 
      self.thermalSvc.setConfig(deviceID, config)
      
      print(f'(3) The Check Order is set to WITHOUT_AUTH. Any user whose temperature is within the threshold will be allowed to access. Try to authenticate faces.\n')
      UserInput.pressEnter('>> Press ENTER if you finish testing this mode.\n')     

      # (4) Set check order to AFTER_AUTH with too low threshold
      config.checkOrder = thermal_pb2.AFTER_AUTH 
      config.temperatureThresholdHigh = 3500 # Too low threshold. Most temperature check will fail
      config.temperatureThresholdLow = 3200
      self.thermalSvc.setConfig(deviceID, config)
      
      print(f'(4) To reproduce the case of high temperature, the Check Order is set to AFTER_AUTH with the threshold of 35 degree Celsius. Most temperature check will fail, now. Try to authenticate faces.\n')
      UserInput.pressEnter('>> Press ENTER if you finish testing this mode.\n')          

      # Restore the original configuration
      self.thermalSvc.setConfig(deviceID, origConfig)

    except grpc.RpcError as e:
      print(f'Cannot finish the config test: {e}', flush=True)
      raise    