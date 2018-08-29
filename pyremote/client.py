
import socket
import threading
import uuid
import weakref

from . import netspec

class DataLock(object):
  def __init__(self):
    self.lock = threading.Lock()
    self.data = None

  def take(self):
    self.lock.acquire()
    return self.data

  def release(self, data):
    self.data = data
    self.lock.release()


class SocketReader(threading.Thread):
  """Keeps reading thread and pumping messages back."""
  def __init__(self, serialized_io, connection):
    super(SocketReader, self).__init__()
    self._io_response_waiter = serialized_io
    self._connection = connection

  def run(self):
    while self._io_response_waiter.isRunning():
      message_size = self._connection.recv(4)
      if not self._io_response_waiter.isRunning():
        # Shutdown process involves setting running = false
        # then closing the socket.
        return

      payload = self._connection.recv(
        int.from_bytes(message_size, byteorder='big'))
      if not self._io_response_waiter.isRunning():
        # In case shutdown happens between the two reads.
        return

      self._io_response_waiter.handle(payload)


class SerializedSocketIO(object):
  """Reader and writer for raw objects over a TCP socket."""
  def __init__(self, ip, port, client, netspec):
    self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self._connection.connect((ip, port))
    self._reader = SocketReader(self, self._connection)
    self._reader.start()
    self._netspec = netspec
    self._data_locks = {}

  def isRunning(self):
    return True

  def write(self, obj, await_response=False):
    """Write an object, and potentially get a response."""
    response = None
    if await_response:
      obj = self._netspec.ReplyRequested(obj, None)
      response = self.notify_on(obj)
    self._netspec.write(obj, self._connection)
    return response

  def notify_on(self, reply_expected):
    """Create a DataLock which when acquired gives back response data."""
    lock = DataLock()
    self._data_locks[reply_expected.uuid] = lock
    lock.take()
    return lock

  def handle(self, payload_data):
    """Handle a payload object."""
    payload = self._netspec.serializer.deserialize(payload_data)
    if not payload:
      return

    if type(payload) == self._netspec.ReplyProvided:
      datalock = self._data_locks.get(payload.uuid, None)
      if datalock:
        datalock.release(payload.reply)
      return

    # TODO accept calls and return from them
    print(payload)


class Client(object):
  """Client connection."""
  def __init__(self, ip, port):
    self._specs = netspec.Netspec()
    self._socket_io = SerializedSocketIO(ip, port, self, self._specs)
    self._weakrefs = {}
    self._strongrefs = {}

  def r_call(self, req):
    """Remote call, and get a reply."""
    return self._socket_io.write(req, True).take()

  def shareClassspec(self, clazz):
    """Uploads a class-specification to the server, and returns clazz."""
    #TODO get methods
    remote_methods = []
    for method_name, method in clazz.__dict__.items():
      if getattr(method, '__remote_exposed__', False):
        remote_methods.append(method_name)
    typespec = self._specs.Typespec(clazz.__name__, clazz.__doc__, remote_methods)
    self._socket_io.write(typespec)
    clazz.__typespec__ = typespec

    def notify_on_delete(obj):
      if obj.__uuid__ in self._weakrefs:
        del self._weakrefs[obj.__uuid__]
      self._socket_io.write(self._specs.Destroy(obj.__uuid__))

    return type(clazz.__name__, (clazz, ), {
      '__del__': notify_on_delete,
      'notify_on_delete': True
    })

  def expose(self, func):
    """Allows a class method to be exposed in a classspec."""
    func.__remote_exposed__ = True
    return func

  def getClassspec(self, clsname):
    """Gets a classspec by classname from the server."""
    return self.r_call(self._specs.RequestTypespec(clsname))

  def getObjects(self, clazz):
    """Query server for objects of type clazz."""
    if clazz is None:
      return []
    return clazz.mocks(self, self.r_call(self._specs.GetByType(clazz)))

  def maintain_reference(self, obj):
    """Holds a reference to a classspec'd object."""
    obj_id = str(uuid.uuid4())
    obj.__uuid__ = obj_id
    self._strongrefs[obj_id] = obj
    instantiate = self._specs.Instantiate(obj.__class__.__typespec__, obj_id)
    self._socket_io.write(instantiate)

  def weak_reference(self, obj):
    """Maintains a weakref to a classspec'd object."""
    print(obj)
    print(dir(obj))
    print(obj.__dict__)
    if not getattr(obj.__class__, 'notify_on_delete', None):
      raise TypeError(
        '{} does not have a shared typespec'.format(obj.__class__))

    obj_id = str(uuid.uuid4())
    obj.__uuid__ = obj_id
    self._strongrefs[obj_id] = weakref.ref(obj)
    instantiate = self._specs.Instantiate(obj.__class__.__typespec__, obj_id)
    self._socket_io.write(instantiate)
