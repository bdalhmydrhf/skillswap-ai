import grpc
import logging
import connect_pb2

from CS20485Menu import MainMenuResourceType, CS20485Menu
from CS20485Test import CS20485Test, SlaveFilter, getInput

from example.master.master import MasterClient
from example.client.client import GatewayClient
from example.connect.connect import ConnectSvc
from example.connectMaster.connectMaster import ConnectMasterSvc
from example.login.login import LoginSvc
from example.device.device import DeviceSvc
from example.rs485.rs485 import RS485Svc
from example.input.input import InputSvc
from example.card.card import CardSvc
from example.user.user import UserSvc

class CS20485Main:
    DEFAULTS = {
        "GATEWAY_CA_FILE": "c:/cert/gateway/ca.crt",
        "GATEWAY_ADDR": "192.168.43.108",
        "GATEWAY_PORT": 4000,
        "MASTER_CA_FILE": "c:/cert/master/master_ca.crt",
        "MASTER_ADDR": "192.168.43.108",
        "MASTER_PORT": 4010,
        "TENANT_CERT_FILE": "c:/cert/master/tenant_tenant1.crt",
        "TENANT_KEY_FILE": "c:/cert/master/tenant_tenant1_key.pem",
        "GATEWAY_ID": "gateway1",
        "DEVICE_ADDR": "192.168.41.27",
        "DEVICE_PORT": 51211,
        "USE_SSL": False,
        "MASTER_MODE": False,
    }

    def __init__(self):
        self.client = None
        self.channel = None
        self.connectSvc = None

    def createClientAndServices(self):
        if self.DEFAULTS["MASTER_MODE"]:
            self.client = MasterClient(
                getInput("Enter Master Address", self.DEFAULTS["MASTER_ADDR"]),
                int(getInput("Enter Master Port", self.DEFAULTS["MASTER_PORT"])),
                getInput("Enter Master CA File Path", self.DEFAULTS["MASTER_CA_FILE"]),
                getInput("Enter Tenant Cert File Path", self.DEFAULTS["TENANT_CERT_FILE"]),
                getInput("Enter Tenant Key File Path", self.DEFAULTS["TENANT_KEY_FILE"]),
            )
            self.channel = self.client.getChannel()
            self.client.setToken(LoginSvc(self.channel).login(self.DEFAULTS["TENANT_CERT_FILE"]))
            self.connectSvc = ConnectMasterSvc(self.channel)
        else:
            self.client = GatewayClient(
                getInput("Enter Gateway Address", self.DEFAULTS["GATEWAY_ADDR"]),
                int(getInput("Enter Gateway Port", self.DEFAULTS["GATEWAY_PORT"])),
                getInput("Enter Gateway CA File Path", self.DEFAULTS["GATEWAY_CA_FILE"]),
            )
            self.channel = self.client.getChannel()
            self.connectSvc = ConnectSvc(self.channel)

    def connectDevice(self, connInfo):
        if self.DEFAULTS["MASTER_MODE"]:
            return self.connectSvc.connect(self.DEFAULTS["GATEWAY_ID"], connInfo)
        return self.connectSvc.connect(connInfo)

    def disconnectAll(self):
        if self.DEFAULTS["MASTER_MODE"]:
            self.connectSvc.disconnectAll(self.DEFAULTS["GATEWAY_ID"])
        else:
            self.connectSvc.disconnectAll()

    def run(self):
        try:
            self.createClientAndServices()
            connInfo = connect_pb2.ConnectInfo(
                IPAddr=getInput("Enter Device IP", self.DEFAULTS["DEVICE_ADDR"]),
                port=int(getInput("Enter Device Port", self.DEFAULTS["DEVICE_PORT"])),
                useSSL=self.DEFAULTS["USE_SSL"],
            )

            deviceID = self.connectDevice(connInfo)

            deviceSvc = DeviceSvc(self.channel)
            rs485Svc = RS485Svc(self.channel)
            inputSvc = InputSvc(self.channel)
            cardSvc = CardSvc(self.channel)
            userSvc = UserSvc(self.channel)
            progTest = CS20485Test(self.connectSvc, deviceSvc, rs485Svc, inputSvc, cardSvc, userSvc)

            while (selected := CS20485Menu.showMenuMain()) != MainMenuResourceType.EXIT:
                if selected == MainMenuResourceType.GET_SLAVE_LIST:
                    progTest.showSlaves(deviceID, SlaveFilter.ALL)
                elif selected == MainMenuResourceType.SEARCH_SLAVE:
                    progTest.searchSlave(deviceID)
                elif selected == MainMenuResourceType.GET_INPUTCONFIG:
                    progTest.getInputConfig(deviceID)
                elif selected == MainMenuResourceType.SET_INPUTCONFIG:
                    progTest.setInputConfig(deviceID)
                elif selected == MainMenuResourceType.GET_FACILITYCODECONFIG:
                    progTest.getFacilityCodeConfig(deviceID)
                elif selected == MainMenuResourceType.SET_FACILITYCODECONFIG:
                    progTest.setFacilityCodeConfig(deviceID)
                elif selected == MainMenuResourceType.ENROLL_USER:
                    progTest.enrollUser(deviceID)
                else:
                    print("Invalid selection. Please try again.")
        except grpc.RpcError as e:
            print(f"Error during operation: {e}")
        finally:
            self.disconnectAll()
            if self.channel:
                self.channel.close()

if __name__ == "__main__":
    logging.basicConfig()
    app = CS20485Main()
    app.run()