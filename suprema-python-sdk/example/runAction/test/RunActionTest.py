import action_pb2
from example.action.action import ActionSvc


class RunActionTest:
    def __init__(self, actionSvc: ActionSvc):
        self.actionSvc = actionSvc

    def runAction(self, deviceID: int):
        actionData = action_pb2.Action(
            deviceID=deviceID,
            type=action_pb2.ACTION_SOUND,
            sound=action_pb2.SoundAction(count=1, soundIndex=0, delay=50),
            stopFlag=action_pb2.STOP_NONE
        )
        self.actionSvc.runAction(deviceID, actionData)
        print("===== Run action success =====")
