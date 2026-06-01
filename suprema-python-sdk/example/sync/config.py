import json
import sys

import connect_pb2

def convertToAsyncInfo(devInfo):
  return connect_pb2.AsyncConnectInfo(deviceID=devInfo['device_id'], IPAddr=devInfo['ip_addr'], port=devInfo['port'], useSSL=devInfo['use_ssl'])

class TestConfig:
  configData = None
  configFile = None

  def __init__(self, configFile): 
    try:
      self.configFile = configFile
      with open(configFile) as f:
        self.configData = json.load(f)
    except:
      e = sys.exc_info()[0]
      print(f'Cannot init the test config: {e}')    

  def write(self):
    try:
      f = open(self.configFile, 'w')
      f.write(json.dumps(self.configData, indent='\t'))
      f.close()
    except:
      e = sys.exc_info()[0]
      print(f'Cannot write the test config: {e}')    

  def getConfigData(self):
    return self.configData

  def getDeviceInfo(self, deviceID):
    if deviceID == self.configData['enroll_device']['device_id']:
      return self.configData['enroll_device']
    else:
      for dev in self.configData['devices']:
        if deviceID == dev['device_id']:
          return dev

    return None

  def updateLastEventID(self, deviceID, lastEventID):
    updated = False

    if deviceID == self.configData['enroll_device']['device_id']:
      self.configData['enroll_device']['last_event_id'] = lastEventID
      updated = True
    else:
      for dev in self.configData['devices']:
        if deviceID == dev['device_id']:
          dev['last_event_id'] = lastEventID
          updated = True
          break
    
    if updated:
      self.write()

  def getAsyncConnectInfo(self):
    connInfos = []
    connInfos.append(convertToAsyncInfo(self.configData['enroll_device']))
    for dev in self.configData['devices']:
      connInfos.append(convertToAsyncInfo(dev))
    
    return connInfos

  def getTargetDeviceIDs(self, connectedIDs):
    targetIDs = []

    for devID in connectedIDs:
      for dev in self.configData['devices']:
        if devID != dev['device_id']:
          targetIDs.append(dev['device_id'])
          break

    return targetIDs
