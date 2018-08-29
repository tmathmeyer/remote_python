import uuid

from . import serialize

class Netspec(object):
  serializer = serialize.Serializer()

  @serializer.forThis(name=str, doc=str, methods=list)
  class Typespec(object):
    def __repr__(self):
      return str(self.serialize())

    def __eq__(self, other):
      return type(other) == type(self) and other.name == self.name

    def mocks(self, client, uuids):
      pass #TODO make this return a pseudo object, which calls remotely

  @serializer.forThis(request=None, uuid=str)
  class ReplyRequested(object):
    def __init__(self):
      if not self.uuid:
        self.uuid = str(uuid.uuid4())

  @serializer.forThis(reply=None, uuid=str)
  class ReplyProvided(object):
    pass

  @serializer.forThis(typename=str)
  class RequestTypespec(object):
    pass

  @serializer.forThis(typespec=None)
  class GetByType(object):
    pass

  @serializer.forThis(typespec=None, uuid=str)
  class Instantiate(object):
    pass

  @serializer.forThis(uuid=str)
  class Destroy(object):
    pass

  def write(self, obj, socket):
    strdata = self.serializer.serialize(obj)
    bytesdata = str.encode(strdata)
    socket.send( (len(bytesdata)).to_bytes(4, byteorder='big') )
    socket.send(bytesdata)