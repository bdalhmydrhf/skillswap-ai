import grpc

JWT_TOKEN_KEY = 'token'

class JwtCredential(grpc.AuthMetadataPlugin):
  token = None

  def setToken(self, jwtToken):
    self.token = jwtToken

  def __call__(self, context, callback):
      callback(((JWT_TOKEN_KEY, self.token),), None)

class MasterClient:
  channel = None
  jwtCreds = None

  def __init__(self, ipAddr, port, caFile, certFile, keyFile):
    try:
      with open(caFile, 'rb') as ca, open(certFile, 'rb') as cert, open(keyFile, 'rb') as key:
        self.jwtCreds = JwtCredential()

        sslCreds = grpc.ssl_channel_credentials(ca.read(), key.read(), cert.read())
        callCreds = grpc.metadata_call_credentials(self.jwtCreds)
        self.channel = grpc.secure_channel("{}:{}".format(ipAddr, port), grpc.composite_channel_credentials(sslCreds, callCreds))
    except grpc.RpcError as e:
      print(f'Cannot create the master client: {e}')
      raise

  def getChannel(self):
    return self.channel

  def setToken(self, jwtToken):
    self.jwtCreds.setToken(jwtToken)