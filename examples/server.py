import socket
import threading

from pyremote import netspec

class ServerSignal(object):
  def __init__(self, finished=False):
    self.finished = finished
  def complete(self):
    self.finished = True


class ConnectionDataListener(threading.Thread):
  def __init__(self, conn, addr, buffer_size, func, pool, spec):
    super(ConnectionDataListener, self).__init__()
    self._conn = conn
    self._addr = addr
    self._func = func
    self._signal = ServerSignal()
    self._pool = pool
    self._spec = spec

  def run(self):
    while not self._signal.finished:
      size = self._conn.recv(4)
      if not size:
        self._signal.complete()
        return

      data = self._conn.recv(int.from_bytes(size, byteorder='big'))
      if not data:
        self._signal.complete()
        return

      payload = self._spec.serializer.deserialize(data)
      self._func(payload, self._addr, self._conn, self._pool)

  def finish(self):
    self._signal.complete()


class ObjectHandler(object):
  def __init__(self, spec):
    self._types = {}
    self._objects = {}
    self._spec = spec

  def handle(self, payload, req_conn):
    if type(payload) == self._spec.Typespec:
      self._types[payload.name] = payload
      return
    if type(payload) == self._spec.Instantiate:
      self._objects[payload.uuid] = (payload.typespec, req_conn)
      return
    if type(payload) == self._spec.ReplyRequested:
      resp, conn = self.reply(payload.request, req_conn)
      if conn:
        self._spec.write(self._spec.ReplyProvided(resp, payload.uuid), conn)

  def reply(self, payload, req_conn):
    if type(payload) == self._spec.RequestTypespec:
      return self._types.get(payload.typename, None), req_conn

    if type(payload) == self._spec.GetByType:
      result = []
      for uuid, (typespec, _) in self._objects.items():
        if typespec == payload.typespec:
          result.append(uuid)
      return result, req_conn

    return None, None


def OnSocketData(ip, port, buffer_size):
  spec = netspec.Netspec()
  pool = ObjectHandler(spec)
  def decorate(func):
    def create_server(*args, **kwargs):
      if args or kwargs:
        print('{} cant be called with arguments')
        return
      _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      _socket.bind((ip, port))
      _socket.listen(1)
      threads = []
      while True:
        conn, addr = _socket.accept();
        cdl = ConnectionDataListener(conn, addr, buffer_size, func, pool, spec)
        threads.append(cdl)
        cdl.start()
      for cdl in threads:
        cdl.finish()
        cdl.join()
    return create_server
  return decorate


@OnSocketData('127.0.0.1', 5005, 256)
def ObjectPoolServer(payload, addr, conn, pool):
  print((addr, payload))
  pool.handle(payload, conn)


if __name__ == '__main__':
  ObjectPoolServer()
