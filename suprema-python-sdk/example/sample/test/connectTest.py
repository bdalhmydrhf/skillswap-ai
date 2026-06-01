import connect_pb2
from typing import List


class ConnectTest:

    def __init__(self, connectSvc):
        self.connectSvc_ = connectSvc

    def connect(self, deviceAddr, port, useSSL):
        connInfo = connect_pb2.ConnectInfo(IPAddr=deviceAddr, port=port, useSSL=useSSL)
        return self.connectSvc_.connect(connInfo)
    
    def showPendingList(self):
        print(f"Getting the pending device list...")

        try:
            pendingList = self.connectSvc_.getPendingList()

            print(f"")
            print(f"***** Pending Devices: {len(pendingList)}")
            for item in pendingList:
                print(f"{item}")
            print(f"")
        except Exception as e:
            print(f"Cannot get the pending list: {e}")
            return

    def showAcceptFilter(self):
        print(f"Getting the accept filter...")

        try:
            filter = self.connectSvc_.getAcceptFilter()

            print(f"")
            print(f"***** Accept Filter: {filter}")
            print(f"")
        except Exception as e:
            print(f"Cannot get the accept filter: {e}")
            return

    def allowAll(self):
        try:
            filter = connect_pb2.AcceptFilter(allowAll=True)
            self.connectSvc_.setAcceptFilter(filter)
            self.showAcceptFilter()
        except Exception as e:
            print(f"Cannot set the accept filter: {e}")
            return
        
    def getDeviceList(self):
        print(f"Getting the devices managed by the gateway...")
        
        try:
            devList = self.connectSvc_.getDeviceList()

            print(f"")
            print(f"***** Managed Devices: {len(devList)}")
            for item in devList:
                print(f"{item}")
            print(f"")
            return len(devList)
        except Exception as e:
            print(f"Cannot get the device list: {e}")
            return 0

    def getConnectedDevice(self) -> List[int]:
        print(f"Getting the connected devices...")

        items: List[int] = []
        try:
            devList = self.connectSvc_.getDeviceList()

            for item in devList:
                items.append(item.deviceID)
        except Exception as e:
            print(f"Cannot get the device list: {e}")

        return items
