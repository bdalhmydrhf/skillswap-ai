import grpc
import action_pb2

from example.cli.input import UserInput

BS2_EVENT_VERIFY_FAIL = 0x1100
BS2_EVENT_IDENTIFY_FAIL = 0x1400

BS2_SUB_EVENT_CREDENTIAL_CARD = 0x02
BS2_SUB_EVENT_CREDENTIAL_FINGER = 0x04

class TestConfig:
  actionSvc = None

  def __init__(self, svc): 
    self.actionSvc = svc

  def test(self, deviceID):
    try:
      # Backup the original configuration
      origConfig = self.actionSvc.getConfig(deviceID)
      print(f'\nOriginal Config: \n{origConfig}', flush=True)

      print(f'\n===== Test TriggerAction Config =====\n', flush=True)
      self.testEventTrigger(deviceID)

      # Restore the original configuration 
      self.actionSvc.setConfig(deviceID, origConfig)

    except grpc.RpcError as e:
      print(f'Cannot finish the config test: {e}', flush=True)
      raise

  def testEventTrigger(self, deviceID):
    try:
      cardFailEventTrigger = action_pb2.EventTrigger(eventCode=BS2_EVENT_VERIFY_FAIL | BS2_SUB_EVENT_CREDENTIAL_CARD)
      cardFailTrigger = action_pb2.Trigger(deviceID=deviceID, type=action_pb2.TRIGGER_EVENT, event=cardFailEventTrigger)

      fingerFailEventTrigger = action_pb2.EventTrigger(eventCode=BS2_EVENT_IDENTIFY_FAIL | BS2_SUB_EVENT_CREDENTIAL_FINGER)
      fingerFailTrigger = action_pb2.Trigger(deviceID=deviceID, type=action_pb2.TRIGGER_EVENT, event=fingerFailEventTrigger)

      relaySignal = action_pb2.Signal(count=3, onDuration=500, offDuration=500)
      relayAction = action_pb2.RelayAction(relayIndex=0, signal=relaySignal)
      failAction = action_pb2.Action(deviceID=deviceID, type=action_pb2.ACTION_RELAY, relay=relayAction)

      cardTriggerAction = action_pb2.TriggerActionConfig.TriggerAction(trigger=cardFailTrigger, action=failAction)
      fingerTriggerAction = action_pb2.TriggerActionConfig.TriggerAction(trigger=fingerFailTrigger, action=failAction)

      config = action_pb2.TriggerActionConfig(triggerActions=[cardTriggerAction, fingerTriggerAction])
      self.actionSvc.setConfig(deviceID, config)

      newConfig = self.actionSvc.getConfig(deviceID)
      print(f'\nTest Config: \n{newConfig}', flush=True)

      print(f'>> Try to authenticate a unregistered card or finger. It should trigger a relay signal.', flush=True)
      UserInput.pressEnter('>> Press ENTER for the next test.\n')   

    except grpc.RpcError as e:
      print(f'Cannot test an event trigger: {e}', flush=True)
      raise
