import grpc
import json

from example.cli.menu import MenuItem, Menu
from example.cli.input import UserInput

from event import MAX_NUM_OF_LOG

DEFAULT_USER_ID = '1234'
MAX_NEW_LOG = 16

class TestMenu:
  menu = None

  userMgr = None
  deviceMgr = None
  eventMgr = None
  testConfig = None

  def __init__(self, userMgr, deviceMgr, eventMgr, testConfig):
    self.userMgr = userMgr
    self.deviceMgr = deviceMgr
    self.eventMgr = eventMgr
    self.testConfig = testConfig

    menuItems = [
      MenuItem('1', 'Show test devices', self.showTestDevice, False),
      MenuItem('2', 'Show new events', self.showNewEvent, False),
      MenuItem('3', 'Show new users', self.showNewUser, False),
      MenuItem('4', 'Enroll a user', self.enrollUser, False),
      MenuItem('5', 'Delete a user', self.deleteUser, False),
      MenuItem('q', 'Quit', None, True),
    ]

    self.menu = Menu('Test Menu', menuItems)

  def showTestDevice(self):
    print(f'***** Test Configuration: \n{json.dumps(self.testConfig.getConfigData(), indent=2)}')
    print(f'***** Connected Devices: {self.deviceMgr.getConnectedDevices(True)}')

  def showNewEvent(self):
    try:
      devIDs = self.deviceMgr.getConnectedDevices(False)

      for devID in devIDs:
        devInfo = self.testConfig.getDeviceInfo(devID)
        if devInfo is None:
          print(f'Device {devID} is not in the configuration file', flush=True)
          continue

        print(f'Read new event logs from device {devID}...', flush=True)
        eventLogs = self.eventMgr.readNewLog(devInfo, MAX_NUM_OF_LOG)

        print(f'Read {len(eventLogs)} event logs', flush=True)

        numOfLog = len(eventLogs)
        if numOfLog > MAX_NEW_LOG:
          numOfLog = MAX_NEW_LOG

        if numOfLog > 0:
           print(f'Show the last {numOfLog} events...')
           for i in range(numOfLog):
             self.eventMgr.printEvent(eventLogs[numOfLog - i - 1])
    except grpc.RpcError as e:
      print(f'Cannot show the new events: {e}')   

  def showNewUser(self):
    try:
      devIDs = self.deviceMgr.getConnectedDevices(False)

      for devID in devIDs:    
        print(f'Read new users from device {devID}...', flush=True)
        userInfos = self.userMgr.getNewUser(devID)
        if not (userInfos is None):
          print(f'New users: {userInfos}', flush=True)

    except grpc.RpcError as e:
      print(f'Cannot show the new users: {e}')   

  def getUserID(self):
    userInputs = [
      UserInput('Enter the user ID', DEFAULT_USER_ID)
    ]

    inputs = UserInput.getUserInput(userInputs)
    return inputs[0]

  def enrollUser(self):
    self.userMgr.enrollUser(self.getUserID())

  def deleteUser(self):
    self.userMgr.deleteUser(self.getUserID())

  def show(self):
    self.menu.show()

