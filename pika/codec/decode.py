# ***** BEGIN LICENSE BLOCK *****
#
# For copyright and licensing please refer to COPYING
#
# ***** END LICENSE BLOCK *****
"""
AMQP Data Decoder

Functions for decoding data of various types including field tables and arrays

"""
__author__ = 'Gavin M. Roy'
__email__ = 'gmr@myyearbook.com'
__since__ = '2011-03-30'

import decimal as _decimal
import struct
import time

# Base data type decoders


def bit(value, position):
    """Decode a bit value

    :param str value: Value to decode
    :return tuple: bytes used, bool value

    """
    bit_buffer = struct.unpack('B', value[0])[0]
    return 0, (bit_buffer & (1 << position)) != 0


def boolean(value):
    """Decode a boolean value

    :param str value: Value to decode
    :return tuple: bytes used, bool

    """
    return 1, bool(struct.unpack_from('B', value[0])[0])


def decimal(value):
    """Decode a decimal value

    :param str value: Value to decode
    :return tuple: bytes used, decimal.Decimal value

    """
    decimals = struct.unpack('B', value[0])[0]
    raw = struct.unpack('>I', value[1:5])[0]
    return 5, _decimal.Decimal(raw) * (_decimal.Decimal(10) ** -decimals)


def floating_point(value):
    """Decode a floating point value

    :param str value: Value to decode
    :return tuple: bytes used, float

    """
    return 4, struct.unpack_from('>f', value)[0]


def long_int(value):
    """Decode a long integer value

    :param str value: Value to decode
    :return tuple: bytes used, int

    """
    return 4, struct.unpack('>l', value[0:4])[0]


def long_long_int(value):
    """Decode a long-long integer value

    :param str value: Value to decode
    :return tuple: bytes used, int

    """
    return 8, struct.unpack('>q', value[0:8])[0]


def long_string(value):
    """Decode a string value

    :param str value: Value to decode
    :return tuple: bytes used, unicode

    """
    length = struct.unpack('>I', value[0:4])[0]
    return length + 4, unicode(value[4:length + 4])


def octet(value):
    """Decode an octet value

    :param str value: Value to decode
    :return tuple: bytes used, int

    """
    return 1, struct.unpack('B', value[0])[0]


def short_int(value):
    """Decode a short integer value

    :param str value: Value to decode
    :return tuple: bytes used, int

    """
    return 2, struct.unpack_from('>H', value[0:2])[0]


def short_string(value):
    """Decode a string value

    :param str value: Value to decode
    :return tuple: bytes used, unicode

    """
    length = struct.unpack('B', value[0])[0]
    return length + 1, unicode(value[1:length + 1])


def timestamp(value):
    """Decode a timestamp value

    :param str value: Value to decode
    :return tuple: bytes used, struct_time

    """
    return 8, time.gmtime(struct.unpack('>Q', value[0:8])[0])


# Compound data types


def field_array(value):
    """Decode a field array value

    :param str value: Value to decode
    :return tuple: bytes used, list

    """
    length = struct.unpack('>I', value[0:4])[0]
    offset = 4
    data = list()
    field_array_end = offset + length
    while offset < field_array_end:
        consumed, result = _embedded_value(value[offset:])
        offset += consumed + 1
        data.append(result)
    return offset, data


def field_table(value):
    """Decode a field array value

    :param str value: Value to decode
    :return tuple: bytes used, dict

    """
    length = struct.unpack('>I', value[0:4])[0]
    offset = 4
    data = dict()
    field_table_end = offset + length
    while offset < field_table_end:
        key_length = struct.unpack_from('B', value, offset)[0]
        offset += 1
        key = value[offset:offset + key_length]
        offset += key_length
        consumed, result = _embedded_value(value[offset:])
        offset += consumed + 1
        data[key] = result
    return field_table_end, data


def _embedded_value(value):
    """Takes in a value looking at the first byte to determine which decoder to
    use

    :param str value: Value to decode
    :return tuple: bytes consumed, mixed

    """
    if not value:
        return 0, None

    # Determine the field type and encode it
    if value[0] == 'A':
        return field_array(value[1:])
    elif value[0] == 'D':
        return decimal(value[1:])
    elif value[0] == 'f':
        return floating_point(value[1:])
    elif value[0] == 'F':
        return field_table(value[1:])
    elif value[0] == 'I':
        return long_int(value[1:])
    elif value[0] == 'L':
        return long_long_int(value[1:])
    elif value[0] == 't':
        return boolean(value[1:])
    elif value[0] == 'T':
        return timestamp(value[1:])
    elif value[0] == 's':
        return short_string(value[1:])
    elif value[0] == 'S':
        return long_string(value[1:])
    elif value[0] == 'U':
        return short_int(value[1:])
    elif value[0] == '\x00':
        return 0, None

    raise ValueError('Unknown type: %s' % value[0])


def by_type(value, data_type, offset=0):
    """Decodes values using the specified type

    :param str value: Value to decode
    :param str data_type: type of data to decode
    :return tuple: bytes consumed, mixed based on field type

    """
    # Determine the field type and encode it
    if data_type == 'bit':
        return bit(value, offset)
    if data_type == 'boolean':
        return boolean(value)
    elif data_type == 'long':
        return long_int(value)
    elif data_type == 'longlong':
        return long_long_int(value)
    elif data_type == 'longstr':
        return long_string(value)
    elif data_type == 'octet':
        return octet(value)
    elif data_type == 'short':
        return short_int(value)
    elif data_type == 'shortstr':
        return short_string(value)
    elif data_type == 'table':
        return field_table(value)
    elif data_type == 'timestamp':
        return timestamp(value)

    raise ValueError('Unknown type: %s' % value)


# Define a data type mapping to methods
METHODS = {'bit': bit,
           'boolen': boolean,
           'long': long_int,
           'longlong': long_long_int,
           'longstr': long_string,
           'octet': octet,
           'short': short_int,
           'shortstr': short_string,
           'table': field_table,
           'timestamp': timestamp}
