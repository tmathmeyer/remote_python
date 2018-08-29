
from . import serialize

class Netspec(object):
  serializer = serialize.Serializer()

  @serializer.forThis(name=str, doc=str, methods=list)
  class Typespec(object):
    pass

  @serializer.forThis(request=None, uuid=str)
  class ReplyRequested(object):
    def __init__(self):
      print('proper init called')

  @serializer.forThis(reply=None, uuid=str)
  class ReplyProvided(object):
    pass

  @serializer.forThis(typename=str)
  class RequestTypespec(object):
    pass

  @serializer.forThis(typespec=None):
  class GetByType(object):
    pass

  def __init__(self, socket):
    self._socket = socket

  def write(self, obj, socket):
    strdata = serializer.serialize(obj)
    bytesdata = str.encode(strdata)
    socket.send( (len(bytesdata)).to_bytes(4, byteorder='big') )
    socket.send(bytesdata)