
import multiprocessing
import threading
import socket
import queue

from pyremote import netspec


class ServerSignal(object):
  def __init__(self, finished=False):
    self.finished = finished
  def complete(self):
    self.finished = True


class ConnectionDataListener(threading.Thread):
  def __init__(self, conn, addr, output, parent):
    super(ConnectionDataListener, self).__init__()
    self._conn = conn
    self._addr = addr
    self._output = output
    self._parent = parent
    self._signal = ServerSignal()

  def run(self):
    while not self._signal.finished:
      size = self._conn.recv(4)
      if not size:
        self._signal.complete()
        self._parent.purge(self._addr)
        return

      data = self._conn.recv(int.from_bytes(size, byteorder='big'))
      if not data:
        self._signal.complete()
        self._parent.purge(self._addr)
        return

      self._output.put((data, self._conn, self._addr))

  def finish(self):
    self._signal.complete()


class ServerProcess(multiprocessing.Process):
  def __init__(self, port, ip, output, kill_switch):
    multiprocessing.Process.__init__(self)
    self._kill_switch = kill_switch
    self._output = output
    self._port = port
    self._ip = ip
    self._threads = {}

    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self._socket.bind((ip, port))
    self._socket.listen(1)

  def run(self):
    while True:
      try:
        addr = self._kill_switch.get_nowait()
        if addr:
          self._threads[addr].join()
          self._threads[addr] = None
        else:
          for thread in self._threads.values():
            thread.finish()
            thread.join()
          self._output.close()
          return
      except queue.Empty:
        conn, addr = self._socket.accept();
        thread = ConnectionDataListener(
          conn, addr, self._output, self)
        self._threads[addr] = thread
        thread.start()

  def purge(self, addr):
    if self._threads[addr]:
      self._kill_switch.put(addr)


class ServerProcessClient(threading.Thread):
  def __init__(self, server, ip, port):
    super(ServerProcessClient, self).__init__()
    self._output_queue = multiprocessing.JoinableQueue()
    self._kill_switch = multiprocessing.JoinableQueue()
    self._signal = ServerSignal()
    self._server = server
    self._spec = netspec.Netspec()

    self._server_process = ServerProcess(
      port, ip, self._output_queue, self._kill_switch)

  def run(self):
    self._server_process.start()
    while not self._signal.finished:
      data, conn, addr = self._output_queue.get()
      payload = self._spec.serializer.deserialize(data)
      if payload and addr:
        self._server.OnData(payload, conn, addr)

  def kill(self):
    self._signal.complete()
    self._output_queue.put((None, None))


class ObjectHandler(object):
  def __init__(self, spec):
    self._types = {}
    self._objects = {}
    self._requests = {}
    self._spec = spec

  def handle(self, payload, req_conn, addr):
    if type(payload) == self._spec.Typespec:
      self._types[payload.name] = payload
      return
    if type(payload) == self._spec.Instantiate:
      self._objects[payload.uuid] = (payload.typespec, req_conn, addr)
      return
    if type(payload) == self._spec.Destroy:
      self._objects.pop(payload.uuid, None)
      return
    if type(payload) == self._spec.ReplyRequested:
      resp, conn = self.reply(payload.request, payload.uuid, req_conn)
      if conn:
        reply = self._spec.ReplyProvided(resp, payload.uuid)
        self._spec.write(reply, conn)
    if type(payload) == self._spec.ReplyProvided:
      uuid, conn = self._requests.pop(payload.uuid, (None, None))
      if conn:
        payload.uuid = uuid
        self._spec.write(payload, conn)

  def reply(self, payload, sender_uuid, req_conn):
    if type(payload) == self._spec.RequestTypespec:
      return self._types.get(payload.typename, None), req_conn

    if type(payload) == self._spec.GetByType:
      result = []
      for uuid, (typespec, _, addr) in self._objects.items():
        if typespec == payload.typespec:
          result.append(uuid)
      return result, req_conn

    if type(payload) == self._spec.Call:
      try:
        _, object_conn, addr = self._objects[payload.uuid]
      except LookupError as e:
        return self._spec.Error('LookupError', str(e)), req_conn
      forward_request = self._spec.ReplyRequested(payload, None)
      self._requests[forward_request.uuid] = (sender_uuid, req_conn)
      try:
        self._spec.write(forward_request, object_conn)
      except BrokenPipeError:
        self._objects.pop(payload.uuid)
        return self._spec.Error('LookupError', str(payload.uuid)), req_conn
      return None, None

    return None, None


class Server():
  def __init__(self):
    self._thread = None
    self._spec = netspec.Netspec()
    self._pool = ObjectHandler(self._spec)

  def OnData(self, payload, conn, addr):
    print('in', addr, payload)
    self._pool.handle(payload, conn, addr)

  def connect(self, ip, port):
    if self._thread:
      raise Exception("Cant connect twice in a row")
    self._thread = ServerProcessClient(self, ip, port)
    self._thread.start()
    return self

  def disconnect(self):
    if self._thread:
      self._thread.kill()
      self._thread.join()
      self._thread = None

  def __del__(self):
    self.disconnect()

  def wait(self):
    self._thread.join()