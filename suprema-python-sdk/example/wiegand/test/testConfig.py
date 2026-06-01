import grpc
import wiegand_pb2

from example.cli.input import UserInput

class TestConfig:
  wiegandSvc = None

  def __init__(self, svc): 
    self.wiegandSvc = svc

  def test(self, deviceID):
    try:
      # Backup the original configuration
      origConfig = self.wiegandSvc.getConfig(deviceID)
      print(f'\n>>> Original Wiegand Config: \n{origConfig}', flush=True)

      print(f'\n===== Wiegand Config Test =====\n', flush=True)
      self.test26bit(deviceID)
      self.test37bit(deviceID)

      UserInput.pressEnter('>> Press ENTER to finish the test.\n')       

      # Restore the original configuration 
      self.wiegandSvc.setConfig(deviceID, origConfig)

    except grpc.RpcError as e:
      print(f'Cannot finish the config test: {e}', flush=True)
      raise

  # 26 bit standard
  # FC: 01 1111 1110 0000 0000 0000 0000 : 0x01fe0000
  # ID: 00 0000 0001 1111 1111 1111 1110 : 0x0001fffe
  # EP: 01 1111 1111 1110 0000 0000 0000 : 0x01ffe000, Pos 0, Type: Even
  # OP: 00 0000 0000 0001 1111 1111 1110 : 0x00001ffe, Pos 25, Type: Odd 

  def test26bit(self, deviceID):
    try:
      default26bit = wiegand_pb2.WiegandFormat(length=26)
      default26bit.IDFields.append(bytes([0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])) # Facility Code
      default26bit.IDFields.append(bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0])) # ID

      evenParity = wiegand_pb2.ParityField(parityPos=0, parityType=wiegand_pb2.WIEGAND_PARITY_EVEN)
      evenParity.data = bytes([0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

      oddParity = wiegand_pb2.ParityField(parityPos=25, parityType=wiegand_pb2.WIEGAND_PARITY_ODD)
      oddParity.data = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0])

      default26bit.parityFields.append(evenParity)
      default26bit.parityFields.append(oddParity)

      wiegandConfig = wiegand_pb2.WiegandConfig(mode=wiegand_pb2.WIEGAND_IN_ONLY, outPulseWidth=40, outPulseInterval=10000, useWiegandUserID=wiegand_pb2.WIEGAND_OUT_USER_ID)
      wiegandConfig.formats.append(default26bit)

      self.wiegandSvc.setConfig(deviceID, wiegandConfig)

      newConfig = self.wiegandSvc.getConfig(deviceID)
      print(f'>>> Wiegand Config with Standard 26bit Format: \n{newConfig}', flush=True)

    except grpc.RpcError as e:
      print(f'Cannot set the 26bit standard format: {e}', flush=True)
      raise

  # 37 bit HID
  # FC: 0 1111 1111 1111 1111 0000 0000 0000 0000 0000 : 0x0ffff00000
  # ID: 0 0000 0000 0000 0000 1111 1111 1111 1111 1110 : 0x00000ffffe
  # EP: 0 1111 1111 1111 1111 1100 0000 0000 0000 0000 : 0x0ffffc0000, Pos 0, Type: Even
  # OP: 0 0000 0000 0000 0000 0111 1111 1111 1111 1110 : 0x000007fffe, Pos 36, Type: Odd     

  def test37bit(self, deviceID):
    try:
      hid37bitFormat = wiegand_pb2.WiegandFormat(length=37)
      hid37bitFormat.IDFields.append(bytes([0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])) # Facility Code
      hid37bitFormat.IDFields.append(bytes([0, 0, 0, 0, 0, 0, 0 ,0 ,0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0])) # ID

      evenParity = wiegand_pb2.ParityField(parityPos=0, parityType=wiegand_pb2.WIEGAND_PARITY_EVEN)
      evenParity.data = bytes([0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

      oddParity = wiegand_pb2.ParityField(parityPos=36, parityType=wiegand_pb2.WIEGAND_PARITY_ODD)
      oddParity.data = bytes([0, 0, 0, 0, 0, 0, 0 ,0 ,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0])

      hid37bitFormat.parityFields.append(evenParity)
      hid37bitFormat.parityFields.append(oddParity)

      wiegandConfig = wiegand_pb2.WiegandConfig(mode=wiegand_pb2.WIEGAND_IN_ONLY, outPulseWidth=40, outPulseInterval=10000, useWiegandUserID=wiegand_pb2.WIEGAND_OUT_USER_ID)
      wiegandConfig.formats.append(hid37bitFormat)

      self.wiegandSvc.setConfig(deviceID, wiegandConfig)

      newConfig = self.wiegandSvc.getConfig(deviceID)
      print(f'>>> Wiegand Config with HID 37bit Format: \n{newConfig}', flush=True)

    except grpc.RpcError as e:
      print(f'Cannot set the HID 37bit format: {e}', flush=True)
      raise
