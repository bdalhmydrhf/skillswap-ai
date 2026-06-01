import grpc
import apb_zone_pb2
import action_pb2
from example.cli.input import UserInput

TEST_ZONE_ID = 1

class TestAPBZone:
  apbSvc = None

  def __init__(self, apbSvc): 
    self.apbSvc = apbSvc

  def test(self, deviceID, slaves):
    try:
      # Backup the original zones
      origZones = self.apbSvc.get(deviceID)
      print(f'Original APB Zones: \n{origZones}\n', flush=True)

      self.apbSvc.deleteAll(deviceID)

      testZone = self.makeZone(deviceID, slaves)
      self.apbSvc.add(deviceID, [testZone])

      print(f'===== Anti Passback Zone Test =====\n', flush=True)
      print(f'Test Zone: \n{testZone}\n', flush=True)

      print(f'>> Authenticate a regsistered credential on the entry device({deviceID}) and/or the exit device({slaves[0].deviceID}) to test if the APB zone works correctly.', flush=True)
      UserInput.pressEnter('>> Press ENTER for the next test.\n')

      UserInput.pressEnter('>> Press ENTER after generating an APB violation.\n')

      self.apbSvc.clearAll(deviceID, TEST_ZONE_ID)

      print(f'>> The APB records are cleared. Try to authenticate the last credential which caused the APB violation. It should succeed since the APB records are cleared.', flush=True)
      UserInput.pressEnter('>> Press ENTER to finish the test.\n')

      # Restore the original zones
      self.apbSvc.deleteAll(deviceID)
      if len(origZones) > 0:
        self.apbSvc.add(deviceID, origZones)

    except grpc.RpcError as e:
      print(f'Cannot finish the apb zone test: {e}', flush=True)
      raise

  def makeZone(self,deviceID, slaves):
    entryDevice = apb_zone_pb2.Member(deviceID=deviceID, readerType=apb_zone_pb2.ENTRY)
    exitDevice = apb_zone_pb2.Member(deviceID=slaves[0].deviceID, readerType=apb_zone_pb2.EXIT)

    relaySignal = action_pb2.Signal(count=3, onDuration=500, offDuration=500)
    relayAction = action_pb2.RelayAction(relayIndex=0, signal=relaySignal)
    zoneAction = action_pb2.Action(deviceID=deviceID, type=action_pb2.ACTION_RELAY, relay=relayAction)

    zone = apb_zone_pb2.ZoneInfo(zoneID=TEST_ZONE_ID, name='Test APB Zone', resetDuration=0, members=[entryDevice, exitDevice], actions=[zoneAction])

    return zone

