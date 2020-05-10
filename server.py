#   import data
from socket import socket, AF_INET, SOCK_STREAM, error as SocketError
from typing import Tuple, Optional
import helper
from helper import RequestCode

DEFAULT_RESPONSES = {
    1: 'List albums',
    2: 'List album song',
    3: 'Song length',
    4: 'Song lyrics',
    5: 'Song album',
    6: 'Search song by name',
    7: 'Search song by lyrics',
    8: 'Quit',
}

EXIT_REQUEST_CODE = 8

WELCOME = 'Welcome to the pink floyd server!'


class ServerError(Exception):
    def __init__(self, message):
        self.message = message


class ChecksumError(Exception):
    pass


def get_request_fields(request: str) -> Tuple[RequestCode, str]:
    """ Parses the request and returns the data.
    :param request: The request
    :return: The request code and the data field.
    :throws: ServerError
    """
    try:
        request_code, checksum_field, data_field = request.split('&')
    except ValueError:
        raise ServerError('Incorrect requst format! Must be '
                          '<code>&checksum:<checksum>&data:<data>')

    request_checksum = int(checksum_field[len('checksum:'):])
    request_data = data_field[len('data:'):]
    helper.checksum_request(request_code, request_data)

    if request_checksum != helper.checksum_request(request_code, request_data):
        raise ChecksumError()

    return request_code, request_data


def get_response(request_code: RequestCode,
                 request_data: str) -> str:
    """ Replys to a request.
    :param request_code: The request type.
    :param request_data: The data field of the request.
    :return: A response to the request.
    """
    #   For now, send a dummy response
    resp_data = DEFAULT_RESPONSES[int(request_code)]
    checksum = helper.checksum_response(resp_data)

    response = 'checksum:{}&data:{}'.format(checksum, resp_data)
    return response


def get_listen_socket() -> socket:
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind(helper.SERVER_ADDR)
    sock.listen(1)
    return sock


def accept_client(listen_sock: socket) -> Optional[socket]:
    """ Tries accepting the next client.
    :param listen_sock: The socket listening on the server address.
    :return: The socket connected to the client.
             If something went wrong, returns None.
    """
    try:
        client_sock, client_addr = listen_sock.accept()

        client_sock.send(WELCOME.encode())
        print('Connected to {}'.format(client_addr))

        return client_sock

    except SocketError:
        if client_sock is not None:
            client_sock.close()

        return None


def do_request_response(client_sock: socket) -> bool:
    """ Will respond to the next request from the client.
    :param client_sock: The connection to the client.
    :return: True if succesful, False if client disconnected.
    """
    try:
        connected = True
        try:
            request = client_sock.recv(1024).decode()
            print('Client: {}'.format(request))
            req_code, req_data = get_request_fields(request)

            response = get_response(req_code, req_data)
            if helper.is_exit_request_code(req_code):
                connected = False

        except ChecksumError:
            response = '*CHECKSUMERROR'
        except ServerError:
            response = '*ERROR'

        print('Server: {}'.format(response))
        client_sock.send(response.encode())

    except SocketError:
        connected = False

    return connected


def main():
    with get_listen_socket() as listen_sock:
        print('Server listening')

        while True:
            client_sock = accept_client(listen_sock)

            if client_sock is not None:
                with client_sock:
                    stay_connected = True
                    while stay_connected:
                        stay_connected = do_request_response(client_sock)
                    print('Client disconnected!')


if __name__ == '__main__':
    main()
