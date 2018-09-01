import uuid

from . import serialize

class Netspec(object):
  serializer = serialize.Serializer()

  @serializer.forThis(name=str, doc=str, methods=list)
  class Typespec(object):
    def __repr__(self):
      return 'register type: {}'.format(self.name)

    def __eq__(self, other):
      return type(other) == type(self) and other.name == self.name

  @serializer.forThis(request=None, uuid=str)
  class ReplyRequested(object):
    def __init__(self):
      if not self.uuid:
        self.uuid = str(uuid.uuid4())

    def __repr__(self):
      return 'request {} made'.format(self.uuid[:8])

  @serializer.forThis(reply=None, uuid=str)
  class ReplyProvided(object):
    def __repr__(self):
      return 'response for {} given'.format(self.uuid[:8])

  @serializer.forThis(typename=str)
  class RequestTypespec(object):
    pass

  @serializer.forThis(typespec=None)
  class GetByType(object):
    pass

  @serializer.forThis(typespec=None, uuid=str)
  class Instantiate(object):
    def __repr__(self):
      return 'instantiate {}, id={}'.format(self.typespec, self.uuid[:8])

  @serializer.forThis(uuid=str)
  class Destroy(object):
    pass

  @serializer.forThis(uuid=str, methodname=None, args=list, kwargs=dict)
  class Call(object):
    pass

  @serializer.forThis(extype=str, msg=str)
  class Error(object):
    pass

  def write(self, obj, socket):
    strdata = self.serializer.serialize(obj)
    bytesdata = str.encode(strdata)
    socket.send( (len(bytesdata)).to_bytes(4, byteorder='big') )
    socket.send(bytesdata)
