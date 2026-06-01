import grpc
import rs485_pb2
import time

class SlaveConnect:
  rs485Svc_ = None

  def __init__(self, rs485Svc): 
    self.rs485Svc_ = rs485Svc

  def getFirstSlave(self, deviceID):
    try:
      config = self.rs485Svc_.getConfig(deviceID)

      for ch in config.channels:
        if ch.mode != rs485_pb2.MASTER:
          ch.mode = rs485_pb2.MASTER

      self.rs485Svc_.setConfig(deviceID, config)

      slaves = self.rs485Svc_.searchSlave(deviceID)
      if 0 == len(slaves):
          print(f'!! No slave device is configured. Configure and wire the slave devices first.', flush=True)
          return 0;

      print(f'Found Slaves: {slaves}')

      for info in slaves:
        info.enabled = True

      self.rs485Svc_.setSlave(deviceID, slaves)

      print(f'Waiting for slaves to be connected...')
      time.sleep(3);

      registeredSlaves = self.rs485Svc_.searchSlave(deviceID)

      print(f'Registered slaves: {registeredSlaves}')
    except grpc.RpcError as e:
      print(f'Cannot get slave device {deviceID}: {e}')
      return 0;

    return registeredSlaves[0].deviceID
