import err_pb2

from grpc_status import rpc_status

def getMultiError(rpcError):
  status = rpc_status.from_call(rpcError)
  if not (status is None):
    for detail in status.details:
      if detail.Is(err_pb2.MultiErrorResponse.DESCRIPTOR):
        info = err_pb2.MultiErrorResponse()
        detail.Unpack(info)
        return info

  return None

