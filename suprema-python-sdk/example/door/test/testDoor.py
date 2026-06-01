import grpc
import door_pb2
import device_pb2
import access_pb2
import user_pb2
from example.cli.input import UserInput

TEST_DOOR_ID = 1
TEST_ACCESS_LEVEL_ID = 1
TEST_ACCESS_GROUP_ID = 1
ALWAYS_SCHEDULE_ID = 1 # ID 1 is reserved for 'always' 

class TestDoor:
  doorSvc = None
  accessSvc = None
  userSvc = None
  testEvent = None

  def __init__(self, doorSvc, accessSvc, userSvc, testEvent): 
    self.doorSvc = doorSvc
    self.accessSvc = accessSvc
    self.userSvc = userSvc
    self.testEvent = testEvent

  def test(self, deviceID):
    try:
      # Backup the original doors
      origDoors = self.doorSvc.getList(deviceID)
      print(f'Original Doors: \n{origDoors}\n', flush=True)

      self.testDoor(deviceID)
      self.testAccessGroup(deviceID)

      # Restore the original doors
      self.doorSvc.deleteAll(deviceID)
      if len(origDoors) > 0:
        self.doorSvc.add(deviceID, origDoors)

    except grpc.RpcError as e:
      print(f'Cannot finish the door test: {e}', flush=True)
      raise

  def testDoor(self, deviceID):
    try:
      relay = door_pb2.Relay(deviceID=deviceID, port=0) # 1st relay
      sensor = door_pb2.Sensor(deviceID=deviceID, port=0, type=device_pb2.NORMALLY_OPEN) # 1st input port
      button = door_pb2.ExitButton(deviceID=deviceID, port=1, type=device_pb2.NORMALLY_OPEN) # 2nd input port

      doorInfo = door_pb2.DoorInfo(doorID=TEST_DOOR_ID, name='Test Door', entryDeviceID=deviceID, relay=relay, sensor=sensor, button=button, autoLockTimeout=3, heldOpenTimeout=10)

      self.doorSvc.deleteAll(deviceID)
      self.doorSvc.add(deviceID, [doorInfo])

      print(f'\n===== Door Test =====\n', flush=True)
      testDoors = self.doorSvc.getList(deviceID)
      print(f'Test Doors: \n{testDoors}\n', flush=True)

      print(f'>> Try to authenticate a registered credential. It should fail since you can access a door only with a proper access group.', flush=True)
      UserInput.pressEnter('>> Press ENTER for the next test.\n')   

    except grpc.RpcError as e:
      print(f'Cannot test the door: {e}', flush=True)
      raise    

  def testAccessGroup(self, deviceID):
    try:
      userID = self.testEvent.getUserID(deviceID)
      if userID is None:
        print(f'!! Cannot find ACCESS_DENIED event. You should have tried to authenticate a registered credentail for the test.', flush=True)
        return

      # Backup access groups
      origGroups = self.accessSvc.getList(deviceID)
      origLevels = self.accessSvc.getLevelList(deviceID)
      origUserAccessGroups = self.userSvc.getAccessGroup(deviceID, [userID])

      print(f'Original Access Groups: \n{origGroups}\n', flush=True)
      print(f'Original Access Levels: \n{origLevels}\n', flush=True)
      print(f'Original User Access Groups: \n{origUserAccessGroups}\n', flush=True)

      self.accessSvc.deleteAll(deviceID)
      self.accessSvc.deleteAllLevel(deviceID)

      # Make an access group and assign it to the user
      doorSchedule = access_pb2.DoorSchedule(doorID=TEST_DOOR_ID, scheduleID=ALWAYS_SCHEDULE_ID) # can access the test door all the time
      accessLevel = access_pb2.AccessLevel(ID=TEST_ACCESS_LEVEL_ID, name='Test Access Level', doorSchedules=[doorSchedule])
      self.accessSvc.addLevel(deviceID, [accessLevel])

      accessGroup = access_pb2.AccessGroup(ID=TEST_ACCESS_GROUP_ID, name='Test Access Group', levelIDs=[TEST_ACCESS_LEVEL_ID])
      self.accessSvc.add(deviceID, [accessGroup])

      userAccessGroup = user_pb2.UserAccessGroup(userID=userID, accessGroupIDs=[TEST_ACCESS_GROUP_ID])
      self.userSvc.setAccessGroup(deviceID, [userAccessGroup])

      newGroups = self.accessSvc.getList(deviceID)
      newLevels = self.accessSvc.getLevelList(deviceID)
      newUserAccessGroups = self.userSvc.getAccessGroup(deviceID, [userID])

      print(f'Test Access Groups: \n{newGroups}\n', flush=True)
      print(f'Test Access Levels: \n{newLevels}\n', flush=True)
      print(f'Test User Access Groups: \n{newUserAccessGroups}\n', flush=True)

      print(f'>> Try to authenticate the same registered credential. It should succeed since the access group is added.', flush=True)
      UserInput.pressEnter('>> Press ENTER for the next test.\n')  

      self.testLock(deviceID)

      # Restore access groups
      self.userSvc.setAccessGroup(deviceID, origUserAccessGroups)
      self.accessSvc.deleteAll(deviceID)
      if len(origGroups) > 0:
        self.accessSvc.add(deviceID, origGroups)
      self.accessSvc.deleteAllLevel(deviceID)
      if len(origLevels) > 0:
        self.accessSvc.addLevel(deviceID, origLevels)
    
    except grpc.RpcError as e:
      print(f'Cannot test the access group: {e}', flush=True)
      raise    

  def testLock(self, deviceID):
    try:
      UserInput.pressEnter('>> Press ENTER to unlock the door.\n') 
      self.doorSvc.unlock(deviceID, [TEST_DOOR_ID], door_pb2.OPERATOR)
      doorStatus = self.doorSvc.getStatus(deviceID)
      print(f'Status after unlocking the door: \n{doorStatus}\n', flush=True)

      UserInput.pressEnter('>> Press ENTER to lock the door.\n') 
      self.doorSvc.lock(deviceID, [TEST_DOOR_ID], door_pb2.OPERATOR)
      doorStatus = self.doorSvc.getStatus(deviceID)
      print(f'Status after locking the door: \n{doorStatus}\n', flush=True)

      print(f'>> Try to authenticate the same registered credential. The relay should not work since the door is locked by the operator with the higher priority.', flush=True)
      UserInput.pressEnter('>> Press ENTER to release the door flag.\n') 
      self.doorSvc.release(deviceID, [TEST_DOOR_ID], door_pb2.OPERATOR)
      doorStatus = self.doorSvc.getStatus(deviceID)
      print(f'Status after releasing the door flag: \n{doorStatus}\n', flush=True)

      print(f'>> Try to authenticate the same registered credential. The relay should work since the door flag is cleared.', flush=True)
      UserInput.pressEnter('>> Press ENTER for the next test.\n') 

    except grpc.RpcError as e:
      print(f'Cannot test the lock/unlock operations: {e}', flush=True)
      raise    
