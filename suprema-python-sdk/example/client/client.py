import grpc

class GatewayClient:
  channel = None

  def __init__(self, ipAddr, port, caFile):
    try:
      with open(caFile, 'rb') as f:
        creds = grpc.ssl_channel_credentials(f.read())
        self.channel = grpc.secure_channel("{}:{}".format(ipAddr, port), creds)
    except grpc.RpcError as e:
      print(f'Cannot create the gateway client: {e}')
      raise

  def getChannel(self):
    return self.channel

  def close(self):
    if self.channel:
      self.channel.close()