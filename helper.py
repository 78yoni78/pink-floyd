import hashlib
from typing import Optional, Dict

SERVER_PORT = 1973
SERVER_IP = '127.0.0.1'
SERVER_ADDR = SERVER_IP, SERVER_PORT

FIELD_SEP = '&'
NAME_VALUE_SEP = ':'


class Error(Exception):
    """ An error in the protocol """
    pass


class ChecksumError(Error):
    def __init__(self, actual_checksum, expected_checksum):
        self.actual_checksum = actual_checksum
        self.expected_checksum = expected_checksum
        super().__init__('Expected checksum of {} but got {}'
                         .format(actual_checksum, expected_checksum))


def is_exit_request_code(req_code: int):
    return req_code == 8


def hash_field(field_name: str, field_value) -> str:
    """ A uniqe hash to use for checksums and such with message's fields.
    :param: The name of the field. Case ignored.
    :param: The value of the field. Can be any object. Case ignored.
    :return: A very random string
    """
    salted_input = '1d{}7cd4{}914c'.format(field_name, field_value).lower()
    return hashlib.md5(salted_input.encode()).hexdigest()


def checksum(**kwargs) -> int:
    """ The checksum of a message.
    :param kwargs: The fields of the message.
                   Use as you would use in make_message.
                   'checksum' fields will NOT be ignored.
    :return: The checksum of the message.
    """
    very_big_random_string = ''.join(hash_field(name, value)
                                     for name, value in kwargs.items())
    return sum(map(ord, very_big_random_string)) % 10_000


def make_message_no_checksum(**kwargs) -> bytes:
    """ Create a message with some fields.
    Example: make_message(data1='hello', data2=2) will return
             'data1:hello&data2:2'
    :param kwargs: The fields.
    :return: The message in the format of the protocol.
    """
    fields = ('{}{}{}'.format(name, NAME_VALUE_SEP, value).lower()
              for name, value in kwargs.items())

    return FIELD_SEP.join(fields).encode()


def make_message(**kwargs) -> bytes:
    kwargs['checksum'] = checksum(**kwargs)
    return make_message_no_checksum(**kwargs)


def parse_message(message: bytes) -> Optional[Dict[str, str]]:
    """
    :throws: Error
    """
    fields = message.decode().split(FIELD_SEP)

    #   Check for valid message fields
    if any(field for field in fields if NAME_VALUE_SEP not in field):
        raise Error('Incorrect message format')

    partitions = (field.partition(NAME_VALUE_SEP)
                  for field in fields)
    ret = {name: value for name, _, value in partitions}

    #   Check sum
    if 'checksum' in ret:
        no_checksum_dict = {name: value for name, value in ret.items()
                            if name != 'checksum'}
        my_checksum = int(checksum(**no_checksum_dict))
        his_checksum = int(ret['checksum'])
        if his_checksum != my_checksum:
            raise ChecksumError(expected_checksum=my_checksum,
                                actual_checksum=his_checksum)

    return ret
