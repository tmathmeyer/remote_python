
import json


def Serializable(*types):
  def decorate(clazz):
    NAME = clazz.__name__
    class __serialize__(object):
      def __init__(self, *args, name=NAME):
        assert len(args) == len(types)
        self.__types = {}
        self.__name = name
        self.__extra = {}
        for attrname, attr in clazz.__dict__.items():
          if getattr(attr, '__SMethod', None):
            self.__extra[attrname] = attr
        for ((arg, typeof), value) in zip(types, args):
          setattr(self, arg, value)
          self.__types[arg] = typeof

      def __repr__(self):
        return self.__name #ToJson(self)

      def __getattr__(self, attr):
        if attr in self.__extra:
          def method(*args, **kwargs):
            return self.__extra[attr](self, *args, **kwargs)
          return method
        if 'getattr' in self.__extra:
          return self.getattr(attr)
        raise TypeError()

      def serialize(self):
        response = {'type': self.__name}
        for k, v in self.__types.items():
          if v == list:
            response[k] = [serialize(o) for o in getattr(self, k)]
          if v == dict:
            response[k] = {x:serialize(y) for x,y in getattr(self, k).items()}
          if v == None:
            response[k] = serialize(getattr(self, k))
        return response

      @staticmethod
      def deserialize(data):
        return __serialize__(*[deserialize(data[n]) for (n,_) in types], name=data['type'])

    __serialize__.__name__ = NAME
    return __serialize__
  return decorate

def SMethod(func):
  func.__SMethod = True
  return func


@Serializable(('typename', None), ('typeid', None), ('remote_methods', list), ('object_ids', dict))
class Instantiate(object):
  @SMethod
  def matches(self, typename, **kwargs):
    if typename != self.typename:
      return False
    for k,v in kwargs.items():
      TMP = object()
      oid = self.object_ids.get(k, TMP)
      if oid is TMP:
        return False
      if oid != v:
        return False
    return True

  @SMethod
  def getattr(self, attr):
    if attr not in self.remote_methods:
      raise TypeError('{} not found'.format(attr))
    if not self.proxy:
      raise TypeError('Cant look up attributes without proxy')
    return self.proxy.make_call(self.typeid, attr)



@Serializable(('sender', None), ('objects', list))
class Response(object):
  pass


@Serializable(('clazz', None), ('name', None), ('args', list), ('kwargs', dict))
class Method(object):
  pass


@Serializable(('sender', None), ('typename', None), ('kwargs', dict))
class Query(object):
  pass

@Serializable(('objid', None))
class Delete(object):
  pass


def deserialize(data):
  if type(data) == list:
    return [deserialize(e) for e in data]
  if type(data) in (int, str, bool):
    return data
  if type(data) == dict:
    if data.get('type', None) == 'Method':
      return Method.deserialize(data)
    if data.get('type', None) == 'Query':
      return Query.deserialize(data)
    if data.get('type', None) == 'Response':
      return Response.deserialize(data)
    if data.get('type', None) == 'Instantiate':
      return Instantiate.deserialize(data)
    if data.get('type', None) == 'Delete':
      return Delete.deserialize(data)
    return {k:deserialize(v) for k,v in data.items()}
  if data is None:
    return None
  raise TypeError('Cant deserialize {}'.format(data))

def serialize(data):
  if type(data) == list:
    return [serialize(e) for e in data]
  if type(data) in (int, str, bool):
    return data
  if type(data) == dict:
    return {k:serialize(v) for k,v in data.items()}
  if type(data) in (Method, Response, Query, Instantiate, Delete):
    return data.serialize()
  if getattr(data, 'id', None):
    return serialize(data.id())

def ToJson(data):
  return json.dumps(serialize(data))

def FromJson(data):
  return deserialize(json.loads(data))
