import json

class Serializer(object):

  def __init__(self):
    self._known_types = {}

  def serialize(self, obj):
    return json.dumps(self._serialize(obj))

  def _serialize(self, obj):
    if type(obj) in (int, str, bool):
      return obj
    if type(obj) == list:
      return [self._serialize(e) for e in obj]
    if type(obj) == dict:
      return {k: self._serialize(v) for k,v in obj.items()}
    if type(obj) in self._known_types.values():
      return obj.serialize()

  def deserialize(self, string):
    return self._deserialize(json.loads(string))

  def _deserialize(self, data):
    if type(data) in (int, str, bool):
      return data
    if type(data) == list:
      return [self._deserialize(e) for e in data]
    if type(data) == dict:
      cls = self._known_types.get(data.get('__type__', None), None)
      if cls:
        nd = {}
        for k, v in data.items():
          if k != '__type__':
            nd[k] = self._deserialize(v)
        return cls(**nd)
      return {k: self._deserialize(v) for k,v in data.items()}
    if data == None:
      return None
    raise TypeError('Cant deserialize {}'.format(data))

  def forThis(self, **constructor_types):
    def TE(msg, name, *args):
      raise TypeError(msg.format(name, '__init__()', *args))

    def type_mismatch(name, *args):
      err = ('{}.{} got mismatched type for argument "{}". '
            'required = {}, received = {}')
      TE(err, name, *args)

    def multiple_values(name, value):
      err = '{}.{} got multiple values for argument "{}"'
      TE(err, name, value)

    def missing_attrs(name, attrs):
      err = '{}.{} missing {} required positional argument{}: {}'
      count = len(attrs)
      TE(err, name, count, 's'*min(1, count), ', '.join(attrs))


    def __decorator__(clazz):
      name = clazz.__name__

      def perfect_init(obj, *args, **attrs):
        for (attr, t), value in zip(constructor_types.items(), args):
          if t != None and value != None and type(value) != t:
            type_mismatch(name, attr, t, type(value))
          obj.__dict__[attr] = value
        for attr, value in attrs.items():
          if attr in obj.__dict__:
            multiple_values(name, attr)
          else:
            obj.__dict__[attr] = value
        missing = []
        for attr in constructor_types.keys():
          if attr not in obj.__dict__:
            missing.append(attr)
        if missing:
          missing_attrs(name, missing)
        super(obj.__class__, obj).__init__()

      def serialize(obj):
        response = {'__type__': name}
        for k, v in constructor_types.items():
          if v == list:
            response[k] = [self._serialize(o) for o in getattr(obj, k)]
          elif v == dict:
            response[k] = {
              x: self._serialize(y) for x,y in getattr(obj, k).items()
            }
          else:
            response[k] = self._serialize(getattr(obj, k))
        return response

      result = type(name, (clazz, ), {
        '__init__': perfect_init,
        'serialize': serialize
      })
      self._known_types[name] = (result)
      return result

    return __decorator__

  
