import grpc
import door_pb2
import device_pb2
import access_pb2
import auth_pb2
import user_pb2
import apb_zone_pb2
import action_pb2
from example.cli.input import UserInput


TEST_DOOR_ID = 1
RELAY_PORT = 0
SENSOR_PORT = 0
SENSOR_APB_DOORSENSOR = False
EXIT_BUTTON_PORT = 1
AUTO_LOCK_TIMEOUT = 3
HELD_OPEN_TIMEOUT = 10
TEST_USER_ID = '10'
TEST_USER_NAME = 'testUser10'
TEST_USER_STARTTIME = 946684800
TEST_USER_ENDTIME = 1924991999
TEST_ZONE_ID = TEST_DOOR_ID
TEST_ACCESS_LEVEL_ID = 1
TEST_ACCESS_LEVEL_NAME = 'AccLevel01'
TEST_ACCESS_GROUP_ID = 1
TEST_ACCESS_GROUP_NAME = 'AccGroup01'
TEST_SCHEDULE_ID_ALWAYS = 1


class DoorAPBTest:
  doorSvc_ = None
  accessSvc_ = None
  userSvc_ = None
  cardSvc_ = None
  authSvc_ = None

  def __init__(self, doorSvc, accessSvc, authSvc, userSvc, cardSvc):
    self.doorSvc_ = doorSvc;
    self.accessSvc_ = accessSvc;
    self.authSvc_ = authSvc;
    self.userSvc_ = userSvc;
    self.cardSvc_ = cardSvc;

  def setDoor(self, deviceID, slaveID):
    try:
      self.doorSvc_.deleteAll(deviceID)

      relay = door_pb2.Relay(deviceID = deviceID, port = RELAY_PORT)
      sensor = door_pb2.Sensor(deviceID = deviceID, port = SENSOR_PORT, type = device_pb2.NORMALLY_OPEN, apbUseDoorSensor = SENSOR_APB_DOORSENSOR)
      button = door_pb2.ExitButton(deviceID = deviceID, port = EXIT_BUTTON_PORT, type = device_pb2.NORMALLY_OPEN)
      apbInfo = self.makeZone(deviceID, slaveID)

      door = door_pb2.DoorInfo(doorID = TEST_DOOR_ID, name = 'Test Door', entryDeviceID = slaveID, exitDeviceID = deviceID, relay = relay, sensor = sensor, button = button, autoLockTimeout = AUTO_LOCK_TIMEOUT, heldOpenTimeout = HELD_OPEN_TIMEOUT, apbZone = apbInfo)
      self.doorSvc_.add(deviceID, [door])
      print(f'===== Set door success =====\n', flush=True)

      newDoors = self.doorSvc_.getList(deviceID)
      print(f'Doors=====:\n{newDoors}\n')
    except grpc.RpcError as e:
      print(f'Cannot set the door to {deviceID}: {e}', flush=True)
      raise

  def makeZone(self, deviceID, slaveID):
    relaySignal = action_pb2.Signal(count = 3, onDuration = 500, offDuration = 500)
    relayAction = action_pb2.RelayAction(relayIndex = 0, signal = relaySignal)
    action = action_pb2.Action(deviceID = deviceID, type = action_pb2.ACTION_RELAY, relay = relayAction)

    exitDevice = apb_zone_pb2.Member(deviceID = deviceID, readerType = apb_zone_pb2.EXIT)
    entryDevice = apb_zone_pb2.Member(deviceID = slaveID, readerType = apb_zone_pb2.ENTRY)

    zone = apb_zone_pb2.ZoneInfo(zoneID = TEST_ZONE_ID, name = 'Test APB Zone', type = apb_zone_pb2.HARD, resetDuration = 0, members = [exitDevice, entryDevice], actions = [action])
    return zone

  def setAccessGroup(self, deviceID):
    try:
      self.accessSvc_.deleteAll(deviceID)
      self.accessSvc_.deleteAllLevel(deviceID)

      doorSchedule = access_pb2.DoorSchedule(doorID = TEST_DOOR_ID, scheduleID = TEST_SCHEDULE_ID_ALWAYS)
      accessLevel = access_pb2.AccessLevel(ID = TEST_ACCESS_LEVEL_ID, name = TEST_ACCESS_LEVEL_NAME, doorSchedules = [doorSchedule])
      accessGroup = access_pb2.AccessGroup(ID = TEST_ACCESS_GROUP_ID, name = TEST_ACCESS_GROUP_NAME, levelIDs = [TEST_ACCESS_LEVEL_ID])

      self.accessSvc_.addLevel(deviceID, [accessLevel])
      self.accessSvc_.add(deviceID, [accessGroup])

      getLevels = self.accessSvc_.getLevelList(deviceID)
      print(f'Access levels=====:\n{getLevels}\n')

      getGroups = self.accessSvc_.getList(deviceID)
      print(f'Access groups=====:\n{getGroups}\n')
    except grpc.RpcError as e:
      print(f'Cannot set the access group to {deviceID}: {e}', flush=True)
      raise

  def updateAuthConfig(self, deviceID):
    try:
      config = self.authSvc_.getConfig(deviceID)
      config.usePrivateAuth = True
      self.authSvc_.setConfig(deviceID, config)

      getConfig = self.authSvc_.getConfig(deviceID)
      print(f'Auth config=====:\n{getConfig}\n')
    except grpc.RpcError as e:
      print(f'Cannot update the auth config to {deviceID}: {e}', flush=True)
      raise

  def enrollUser(self, deviceID):
    try:
      userIDs = [TEST_USER_ID]
      self.userSvc_.delete(deviceID, userIDs)

      hdr = user_pb2.UserHdr(ID = TEST_USER_ID, userFlag = user_pb2.USER_FLAG_CREATED, numOfCard = 1)
      setting = user_pb2.UserSetting(startTime = TEST_USER_STARTTIME, endTime = TEST_USER_ENDTIME, cardAuthMode = auth_pb2.AUTH_MODE_CARD_ONLY, cardAuthExtMode = auth_pb2.AUTH_EXT_MODE_CARD_ONLY)

      print(f'>> Scan your card...\n')
      cardData = self.cardSvc_.scan(deviceID)

      userInfo = user_pb2.UserInfo(hdr = hdr, setting = setting, name = TEST_USER_NAME, cards = [cardData.CSNCardData], accessGroupIDs = [TEST_ACCESS_GROUP_ID])
      self.userSvc_.enroll(deviceID, [userInfo], True)

      print(f'Enroll success=====:\n{userIDs}\n')

      masterUsers = self.userSvc_.getUser(deviceID, userIDs)
      print(f'Master user=====:\n{masterUsers}\n')

      print(f'>> APB authentication test...\n')
      UserInput.pressEnter('>> Press ENTER to stop.\n') 
    except grpc.RpcError as e:
      print(f'Cannot enroll the user to {deviceID}: {e}', flush=True)
      raise
