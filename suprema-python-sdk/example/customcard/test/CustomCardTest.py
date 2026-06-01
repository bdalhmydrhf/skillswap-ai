import grpc
import card_pb2
from example.cli.input import UserInput
import system_pb2


TEST_START_BLOCK_INDEX = 4
TEST_DATA_SIZE = 8
TEST_SKIP_BYTES = 0


class CustomCardTest:
  cardSvc_ = None
  systemSvc_ = None

  def __init__(self, cardSvc, systemSvc):
    self.cardSvc_ = cardSvc;
    self.systemSvc_ = systemSvc;

  def setCustomCardConfig(self, deviceID):
    try:
      config = self.getCustomCardConfig(deviceID)
      if not config:
        return

      config.dataType = UserInput.getInteger("Please enter a data type of cards. (0: Binary, 1: ASCII, 2: UTF16, 3: BCS)", config.dataType, 0, 3)
      config.useSecondaryKey = 1 if UserInput.getBoolean("Do you want to use secondary key?") else 0
      useMifare = UserInput.getBoolean("Do you want to change mifare custom card settings?")
      if useMifare:
        config.mifare.primaryKey = UserInput.getBytes("Please enter the hexadecimal 6 bytes primary key for mifare card.", config.mifare.primaryKey)
        if config.useSecondaryKey == 1:
          config.mifare.secondaryKey = UserInput.getBytes("Please enter the hexadecimal 6 bytes secondary key for mifare card.", config.mifare.secondaryKey)

        config.mifare.startBlockIndex = UserInput.getInteger("Please enter the start block index of mifare card.", config.mifare.startBlockIndex)
        config.mifare.dataSize = UserInput.getInteger("Please enter the card data size of mifare card.", config.mifare.dataSize)
        config.mifare.skipBytes = UserInput.getInteger("Please enter the skip bytes of mifare card.", config.mifare.skipBytes)

      useDesfire = UserInput.getBoolean("Do you want to change desfire custom card settings?")
      if useDesfire:
        config.desfire.operationMode = UserInput.getInteger("Please enter a operation mode for desfire card. (0: Legacy, 1: Advanced(AppLevelKey))", 0, 0, 1)

        if card_pb2.OPERATION_LEGACY == config.desfire.operationMode:
          config.desfire.primaryKey = UserInput.getBytes("Please enter the hexadecimal 16 bytes primary key for desfire card.", config.desfire.primaryKey)
          if config.useSecondaryKey:
            config.desfire.secondaryKey = UserInput.getBytes("Please enter the hexadecimal 16 bytes secondary key for desfire card.", config.desfire.secondaryKey)
        else:
          config.desfire.desfireAppKey.appMasterKey = UserInput.getBytes("Please enter the hexadecimal 16 bytes appMasterKey for desfire card.", config.desfire.desfireAppKey.appMasterKey)
          config.desfire.desfireAppKey.fileReadKey = UserInput.getBytes("Please enter the hexadecimal 16 bytes fileReadKey for desfire card.", config.desfire.desfireAppKey.fileReadKey)
          config.desfire.desfireAppKey.fileReadKeyNumber = UserInput.getInteger("Please enter the fileReadKeyNumber of desfire card.", config.desfire.desfireAppKey.fileReadKeyNumber)

        config.desfire.appID = UserInput.getBytes("Please enter the hexadecimal 3 bytes appID for desfire card.", config.desfire.appID)
        config.desfire.fileID = UserInput.getInteger("Please enter the fileID for desfire card.", config.desfire.fileID)
        config.desfire.encryptionType = UserInput.getInteger("Please enter a encryption type for desfire card. (0: DES/3DES, 1: AES)", config.desfire.encryptionType)
        config.desfire.dataSize = UserInput.getInteger("Please enter the card data size of desfire card.", config.desfire.dataSize)
        config.desfire.skipBytes = UserInput.getInteger("Please enter the skip bytes of desfire card.", config.desfire.skipBytes)

      config.smartCardByteOrder = UserInput.getInteger("Please enter a smart card byte order. (0: MSB, 1: LSB)", config.smartCardByteOrder)
      config.formatID = UserInput.getInteger("Please enter a formatID.", config.formatID)

      self.cardSvc_.setCustomConfig(deviceID, config)

      self.changeCardOperationMode(deviceID)

    except grpc.RpcError as e:
      print(f'Cannot set the door to {deviceID}: {e}', flush=True)
      raise

  def getCustomCardConfig(self, deviceID):
    try:
      config = self.cardSvc_.getCustomConfig(deviceID)
      print(f'Custom card config=====:\n{config}\n', flush=True)
      return config
    except grpc.RpcError as e:
      print(f'Cannot set the door to {deviceID}: {e}', flush=True)
      raise

  def changeCardOperationMode(self, deviceID):
    try:
      updateMode = UserInput.getBoolean("To use the custom smart card function, you must turn off the Suprema smart card function.\nDo you want to change the card operation mode?", True)
      if updateMode:
        systemConfig = self.systemSvc_.getConfig(deviceID)

        prevMask = systemConfig.useCardOperationMask

        CONST_CARD_OPERATION_MASK_USE = 0x80000000

        # Turn off Suprema smart card
        systemConfig.useCardOperationMask &= ~system_pb2.CARD_OPERATION_MASK_CLASSIC_PLUS
        systemConfig.useCardOperationMask &= ~system_pb2.CARD_OPERATION_MASK_DESFIRE_EV1
        systemConfig.useCardOperationMask &= ~system_pb2.CARD_OPERATION_MASK_SR_SE
        systemConfig.useCardOperationMask &= ~system_pb2.CARD_OPERATION_MASK_SEOS

        # Turn on Custom smart card
        systemConfig.useCardOperationMask |= system_pb2.CARD_OPERATION_MASK_CUSTOM_CLASSIC_PLUS
        systemConfig.useCardOperationMask |= system_pb2.CARD_OPERATION_MASK_CUSTOM_DESFIRE_EV1

        # Apply
        systemConfig.useCardOperationMask |= CONST_CARD_OPERATION_MASK_USE
        self.systemSvc_.setConfig(deviceID, systemConfig)

        print("Card operation mode was changed {prevMask} ====> {systemConfig.useCardOperationMask}", flush=True)

    except grpc.RpcError as e:
      print(f'Cannot set the access group to {deviceID}: {e}', flush=True)
      raise

  def scanCard(self, deviceID):
    try:
      print(f'>>> Scan your card from the device {deviceID}...', flush=False)
      cardData = self.cardSvc_.scan(deviceID)

      print(f'Card data=====:\n{cardData}\n', flush=True)

    except grpc.RpcError as e:
      print(f'Cannot scan card from the device {deviceID}: {e}', flush=True)
      raise
