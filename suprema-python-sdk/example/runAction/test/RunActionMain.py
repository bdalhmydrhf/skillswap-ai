import grpc
import logging
import connect_pb2

from LogTest import LogTest
from RunActionTest import RunActionTest
from RunActionMenu import RunActionMenu, MainMenuResourceType

from example.master.master import MasterClient
from example.client.client import GatewayClient
from example.connect.connect import ConnectSvc
from example.connectMaster.connectMaster import ConnectMasterSvc
from example.login.login import LoginSvc
from example.event.event import EventSvc
from example.action.action import ActionSvc


class RunActionApp:
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
        "DEVICE_ADDR": "192.168.40.11",
        "DEVICE_PORT": 51211,
        "USE_SSL": False,
        "MASTER_MODE": False,
    }

    def __init__(self):
        self.client = None
        self.channel = None
        self.connectSvc = None

    @staticmethod
    def getInput(prompt, default):
        return input(f"{prompt} (default: {default}): ") or default

    def createClientAndServices(self):
        if self.DEFAULTS["MASTER_MODE"]:
            self.client = MasterClient(
                self.getInput("Enter Master Address", self.DEFAULTS["MASTER_ADDR"]),
                int(self.getInput("Enter Master Port", self.DEFAULTS["MASTER_PORT"])),
                self.getInput("Enter Master CA File Path", self.DEFAULTS["MASTER_CA_FILE"]),
                self.getInput("Enter Tenant Cert File Path", self.DEFAULTS["TENANT_CERT_FILE"]),
                self.getInput("Enter Tenant Key File Path", self.DEFAULTS["TENANT_KEY_FILE"]),
            )
            self.channel = self.client.getChannel()
            self.client.setToken(LoginSvc(self.channel).login(self.DEFAULTS["TENANT_CERT_FILE"]))
            self.connectSvc = ConnectMasterSvc(self.channel)
        else:
            self.client = GatewayClient(
                self.getInput("Enter Gateway Address", self.DEFAULTS["GATEWAY_ADDR"]),
                int(self.getInput("Enter Gateway Port", self.DEFAULTS["GATEWAY_PORT"])),
                self.getInput("Enter Gateway CA File Path", self.DEFAULTS["GATEWAY_CA_FILE"]),
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
                IPAddr=self.getInput("Enter Device IP", self.DEFAULTS["DEVICE_ADDR"]),
                port=int(self.getInput("Enter Device Port", self.DEFAULTS["DEVICE_PORT"])),
                useSSL=self.DEFAULTS["USE_SSL"],
            )
            deviceID = self.connectDevice(connInfo)

            actionSvc = ActionSvc(self.channel)
            eventSvc = EventSvc(self.channel)
            logTest = LogTest(eventSvc)
            progTest = RunActionTest(actionSvc)

            logTest.startMonitoring(deviceID)
            while (selected := RunActionMenu.showMenuMain()) != MainMenuResourceType.EXIT:
                if selected == MainMenuResourceType.RUN_ACTION:
                    progTest.runAction(deviceID)
            logTest.stopMonitoring(deviceID)
        except grpc.RpcError as e:
            print(f"Error: {e}", flush=True)
        finally:
            self.disconnectAll()
            if self.channel:
                self.channel.close()


if __name__ == "__main__":
    logging.basicConfig()
    app = RunActionApp()
    app.run()
