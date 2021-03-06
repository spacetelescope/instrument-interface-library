# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: event.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='event.proto',
  package='catkit.datalogging',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0b\x65vent.proto\x12\x12\x63\x61tkit.datalogging\"H\n\x06Tensor\x12\r\n\x05shape\x18\x01 \x03(\x03\x12\r\n\x05\x64type\x18\x02 \x01(\t\x12\x12\n\nbyte_order\x18\x03 \x01(\t\x12\x0c\n\x04\x64\x61ta\x18\x04 \x01(\x0c\"U\n\x05\x43urve\x12%\n\x01x\x18\x01 \x01(\x0b\x32\x1a.catkit.datalogging.Tensor\x12%\n\x01y\x18\x02 \x01(\x0b\x32\x1a.catkit.datalogging.Tensor\"\x15\n\x06\x46igure\x12\x0b\n\x03png\x18\x01 \x01(\x0c\"\x17\n\x08\x46itsFile\x12\x0b\n\x03uri\x18\x01 \x01(\t\"\x91\x02\n\x05\x45vent\x12\x11\n\twall_time\x18\x01 \x01(\x01\x12\x0b\n\x03tag\x18\x02 \x01(\t\x12\x12\n\nvalue_type\x18\x03 \x01(\t\x12\x10\n\x06scalar\x18\x08 \x01(\x02H\x00\x12,\n\x06tensor\x18\t \x01(\x0b\x32\x1a.catkit.datalogging.TensorH\x00\x12*\n\x05\x63urve\x18\n \x01(\x0b\x32\x19.catkit.datalogging.CurveH\x00\x12,\n\x06\x66igure\x18\x0b \x01(\x0b\x32\x1a.catkit.datalogging.FigureH\x00\x12\x31\n\tfits_file\x18\x0c \x01(\x0b\x32\x1c.catkit.datalogging.FitsFileH\x00\x42\x07\n\x05valueb\x06proto3'
)




_TENSOR = _descriptor.Descriptor(
  name='Tensor',
  full_name='catkit.datalogging.Tensor',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='shape', full_name='catkit.datalogging.Tensor.shape', index=0,
      number=1, type=3, cpp_type=2, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='dtype', full_name='catkit.datalogging.Tensor.dtype', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='byte_order', full_name='catkit.datalogging.Tensor.byte_order', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='data', full_name='catkit.datalogging.Tensor.data', index=3,
      number=4, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=35,
  serialized_end=107,
)


_CURVE = _descriptor.Descriptor(
  name='Curve',
  full_name='catkit.datalogging.Curve',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='x', full_name='catkit.datalogging.Curve.x', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='y', full_name='catkit.datalogging.Curve.y', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=109,
  serialized_end=194,
)


_FIGURE = _descriptor.Descriptor(
  name='Figure',
  full_name='catkit.datalogging.Figure',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='png', full_name='catkit.datalogging.Figure.png', index=0,
      number=1, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=196,
  serialized_end=217,
)


_FITSFILE = _descriptor.Descriptor(
  name='FitsFile',
  full_name='catkit.datalogging.FitsFile',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='uri', full_name='catkit.datalogging.FitsFile.uri', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=219,
  serialized_end=242,
)


_EVENT = _descriptor.Descriptor(
  name='Event',
  full_name='catkit.datalogging.Event',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='wall_time', full_name='catkit.datalogging.Event.wall_time', index=0,
      number=1, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='tag', full_name='catkit.datalogging.Event.tag', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='value_type', full_name='catkit.datalogging.Event.value_type', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='scalar', full_name='catkit.datalogging.Event.scalar', index=3,
      number=8, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='tensor', full_name='catkit.datalogging.Event.tensor', index=4,
      number=9, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='curve', full_name='catkit.datalogging.Event.curve', index=5,
      number=10, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='figure', full_name='catkit.datalogging.Event.figure', index=6,
      number=11, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='fits_file', full_name='catkit.datalogging.Event.fits_file', index=7,
      number=12, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='value', full_name='catkit.datalogging.Event.value',
      index=0, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
  ],
  serialized_start=245,
  serialized_end=518,
)

_CURVE.fields_by_name['x'].message_type = _TENSOR
_CURVE.fields_by_name['y'].message_type = _TENSOR
_EVENT.fields_by_name['tensor'].message_type = _TENSOR
_EVENT.fields_by_name['curve'].message_type = _CURVE
_EVENT.fields_by_name['figure'].message_type = _FIGURE
_EVENT.fields_by_name['fits_file'].message_type = _FITSFILE
_EVENT.oneofs_by_name['value'].fields.append(
  _EVENT.fields_by_name['scalar'])
_EVENT.fields_by_name['scalar'].containing_oneof = _EVENT.oneofs_by_name['value']
_EVENT.oneofs_by_name['value'].fields.append(
  _EVENT.fields_by_name['tensor'])
_EVENT.fields_by_name['tensor'].containing_oneof = _EVENT.oneofs_by_name['value']
_EVENT.oneofs_by_name['value'].fields.append(
  _EVENT.fields_by_name['curve'])
_EVENT.fields_by_name['curve'].containing_oneof = _EVENT.oneofs_by_name['value']
_EVENT.oneofs_by_name['value'].fields.append(
  _EVENT.fields_by_name['figure'])
_EVENT.fields_by_name['figure'].containing_oneof = _EVENT.oneofs_by_name['value']
_EVENT.oneofs_by_name['value'].fields.append(
  _EVENT.fields_by_name['fits_file'])
_EVENT.fields_by_name['fits_file'].containing_oneof = _EVENT.oneofs_by_name['value']
DESCRIPTOR.message_types_by_name['Tensor'] = _TENSOR
DESCRIPTOR.message_types_by_name['Curve'] = _CURVE
DESCRIPTOR.message_types_by_name['Figure'] = _FIGURE
DESCRIPTOR.message_types_by_name['FitsFile'] = _FITSFILE
DESCRIPTOR.message_types_by_name['Event'] = _EVENT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Tensor = _reflection.GeneratedProtocolMessageType('Tensor', (_message.Message,), {
  'DESCRIPTOR' : _TENSOR,
  '__module__' : 'event_pb2'
  # @@protoc_insertion_point(class_scope:catkit.datalogging.Tensor)
  })
_sym_db.RegisterMessage(Tensor)

Curve = _reflection.GeneratedProtocolMessageType('Curve', (_message.Message,), {
  'DESCRIPTOR' : _CURVE,
  '__module__' : 'event_pb2'
  # @@protoc_insertion_point(class_scope:catkit.datalogging.Curve)
  })
_sym_db.RegisterMessage(Curve)

Figure = _reflection.GeneratedProtocolMessageType('Figure', (_message.Message,), {
  'DESCRIPTOR' : _FIGURE,
  '__module__' : 'event_pb2'
  # @@protoc_insertion_point(class_scope:catkit.datalogging.Figure)
  })
_sym_db.RegisterMessage(Figure)

FitsFile = _reflection.GeneratedProtocolMessageType('FitsFile', (_message.Message,), {
  'DESCRIPTOR' : _FITSFILE,
  '__module__' : 'event_pb2'
  # @@protoc_insertion_point(class_scope:catkit.datalogging.FitsFile)
  })
_sym_db.RegisterMessage(FitsFile)

Event = _reflection.GeneratedProtocolMessageType('Event', (_message.Message,), {
  'DESCRIPTOR' : _EVENT,
  '__module__' : 'event_pb2'
  # @@protoc_insertion_point(class_scope:catkit.datalogging.Event)
  })
_sym_db.RegisterMessage(Event)


# @@protoc_insertion_point(module_scope)
