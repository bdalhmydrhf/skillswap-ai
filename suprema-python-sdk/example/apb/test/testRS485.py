import grpc
import rs485_pb2
import time

class TestRS485:
  rs485Svc = None
  slaves = []
  registeredSlaves = []

  def __init__(self, rs485Svc): 
    self.rs485Svc = rs485Svc

  def checkSlaves(self, deviceID):
    try:
      config = self.rs485Svc.getConfig(deviceID)

      hasMasterChannel = False

      for ch in config.channels:
        if ch.mode == rs485_pb2.MASTER:
          hasMasterChannel = True
          break

      if not hasMasterChannel:
        print(f'!! Only a master device can have slave devices. Skip the test.', flush=True)
        return False

      self.slaves = self.rs485Svc.searchSlave(deviceID)  
      if len(self.slaves) == 0:
        print(f'!! No slave device is configured. Configure and wire the slave devices first.', flush=True)
        return False

      print(f'Found Slaves: \n{self.slaves}\n', flush=True)

      self.registeredSlaves = self.rs485Svc.getSlave(deviceID)

      print(f'Registered Slaves: \n{self.registeredSlaves}\n', flush=True)

      if len(self.registeredSlaves) == 0:
        self.rs485Svc.setSlave(deviceID, self.slaves)

      for i in range(10):
        newSlaves = self.rs485Svc.searchSlave(deviceID)
        if newSlaves[0].connected:
          break  
        
        print(f'Waiting for the slave to be connected {i}...\n', flush=True)

      return True

    except grpc.RpcError as e:
      print(f'Cannot check the slave devices: {e}', flush=True)
      raise

  def restoreSlaves(self, deviceID):
    try:
      self.rs485Svc.setSlave(deviceID, self.registeredSlaves)
    
    except grpc.RpcError as e:
      print(f'Cannot restore the slave devices: {e}', flush=True)
      raise

  def getSlaves(self):
    return self.slaves

