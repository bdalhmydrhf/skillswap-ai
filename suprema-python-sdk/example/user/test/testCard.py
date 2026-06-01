import grpc
import card_pb2
import user_pb2

from example.cli.input import UserInput

class TestCard:
  cardSvc = None
  userSvc = None

  def __init__(self, cardSvc, userSvc): 
    self.cardSvc = cardSvc
    self.userSvc = userSvc

  def test(self, deviceID, userID):
    try:
      print(f'\n===== Card Test =====\n', flush=True)
      print(f'>> Place a unregistered card on the device...', flush=True)

      cardData = self.cardSvc.scan(deviceID)

      if cardData.CSNCardData == None:
        print(f'!! The card is a smart card. For this test, you have to use a CSN card. Skip the card test.\n', flush=True)
        return

      userCard = user_pb2.UserCard(userID=userID, cards=[cardData.CSNCardData])
      self.userSvc.setCard(deviceID, [userCard])

      UserInput.pressEnter('>> Try to authenticate the enrolled card. And, press ENTER to end the test.\n')

    except grpc.RpcError as e:
      print(f'Cannot complete the card test: {e}', flush=True)   
      raise




    