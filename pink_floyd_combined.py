from typing import Union, Tuple, Optional
from socket import socket, AF_INET, SOCK_STREAM, error as SocketError
import sys

RequestCode = Union[int, str]

SERVER_PORT = 1973
SERVER_IP = '127.0.0.1'
SERVER_ADDR = SERVER_IP, SERVER_PORT


def checksum_response(string: str) -> int:
    return sum(map(ord, string))


def checksum_request(request_code: RequestCode, request_data: str) -> None:
    return checksum_response(request_data) + ord(str(request_code))


def is_exit_request_code(req_code: RequestCode):
    return int(req_code) == 8


REQUEST_CODE_NAMES = """1 - List all albums
2 - List album song
3 - Length of song
4 - Lyrics of song
5 - Get album of song
6 - Search song by name
7 - Search song by lyrics
8 - Quit """

#   Missing requests codes do not hold data
REQUEST_CODE_PROMPTS = {
    2: 'Choose an album: ',
    3: 'Choose a song: ',
    4: 'Choose a song: ',
    5: 'Choose a song: ',
    6: 'Choose a word to search: ',
    7: 'Choose a a word to search: ',
}

PASSWORD = 'Pink Floyd'


def client_get_request(req_code: RequestCode, req_data: str) -> str:
    """ Returns a string repressenting a request
    :param req_code: The request code repressenting which type
                     of request is being sent
    :param req_data: The parameters fed to the request
    :return: The string to be sent as the response to the server
    """
    checksum = checksum_request(req_code, req_data)
    request = '{}&checksum:{}&data:{}'.format(req_code, checksum, req_data)
    return request


def client_get_response_data(response: str) -> Optional[str]:
    """ Get the data from the response
    :param response: A response from the server. Example: checksum:743&data:hi
    :return: The data field OR the error message if successful.
             May fail if there is a client-side checksum error.
    """
    if response.startswith('*ERROR') or response.startswith('*CHECKSUMERROR'):
        return response

    checksum_field, data_field = response.split('&')
    checksum = int(checksum_field[len('checksum:'):])
    resp_data = data_field[len('data:'):]

    if checksum != checksum_response(resp_data):
        return None

    return resp_data


def client_get_response(sock: socket, request: str) -> Optional[str]:
    """ Gets the response of the server to a request.
    :param sock: The socket connected to the server
    :param request: The request.
    :return: The reply from the server as a string
             If disconnected, returns None.
    """
    try:
        sock.send(request.encode())
        response = sock.recv(1025).decode()

    except SocketError:
        return None

    else:
        return client_get_response_data(response)


def connect_to_server() -> Tuple[socket, str]:
    """ Opens a conversation with the server
    :return: A socket with the server and the server's welcome message
    :throws: SocketError
    """
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(SERVER_ADDR)

    welcome_msg = client_get_response_data(sock.recv(1024).decode())

    return sock, welcome_msg


def get_user_number(min: int, max: int) -> int:
    """ Gets a number from the user between a certain range.
    :param min: inclusive minimum value.
    :param min: inclusive maximum value.
    :return: The number choosen by the user.
    """
    res = None
    try:
        res = int(input('Choose an option: '))
    except ValueError:
        pass
    if res is not None and min <= res <= max:
        return res
    print('Please enter a valid number between {} and {}'.format(min, max))
    return get_user_number(min, max)


def do_user_login():
    user_password = ''
    while user_password != PASSWORD:
        user_password = input('Enter the password: ')


def client_do_request_response(sock: socket,
                               req_code: RequestCode,
                               req_data: str) -> bool:
    """ Prints the result of the request to the user.
    :param sock: The connection to the server
    :param req_code: The request code
    :param req_data: The data field of the request
    :return: True if succesful, False if connection error
    """
    request = client_get_request(req_code, req_data)
    response = client_get_response(sock, request)

    if response is None:
        print('Oops! It seams you were disconnected. '
              'Try again or check your internet connection.')
        return False
    else:
        print(response)
        return True


def make_requests_to_server(sock: socket) -> None:
    """ Makes consecetive requests until disconnected.
    :param sock: Socket to the server
    """
    while True:
        print(REQUEST_CODE_NAMES)
        req_code = get_user_number(1, 8)

        #   If the request code requires data, ask for it
        req_data = ''
        if req_code in REQUEST_CODE_PROMPTS:
            req_data = input(REQUEST_CODE_PROMPTS[int(req_code)])

        client_do_request_response(sock, req_code, req_data)

        if is_exit_request_code(req_code):
            break


def client_main():
    connected = False

    do_user_login()

    print('Connecting to server...', end='')
    try:
        sock, welcome_msg = connect_to_server()
    except SocketError as e:
        print('failure!')
        print('Cannot connect to server. please try again. \n{}'.format(e))
    else:
        connected = True

    if connected:
        with sock:
            print('connected! \n')
            print(welcome_msg)

            make_requests_to_server(sock)


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


def server_get_request_fields(request: str) -> Tuple[RequestCode, str]:
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
    checksum_request(request_code, request_data)

    if request_checksum != checksum_request(request_code, request_data):
        raise ChecksumError()

    return request_code, request_data


def server_get_response(resp_data: str) -> str:
    """ Get the data from the response
    :param response: A response from the server. Example: checksum:743&data:hi
    :return: The data field OR the error message if successful.
             May fail if there is a client-side checksum error.
    """
    checksum = checksum_response(resp_data)
    response = 'checksum:{}&data:{}'.format(checksum, resp_data)

    return response


def server_get_response_data(request_code: RequestCode,
                             request_data: str) -> str:
    """ Replys to a request.
    :param request_code: The request type.
    :param request_data: The data field of the request.
    :return: A response to the request (Only the data - use server_get_response).
    """
    #   For now, send a dummy response
    resp_data = DEFAULT_RESPONSES[int(request_code)]
    return resp_data


def get_listen_socket() -> socket:
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind(SERVER_ADDR)
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

        client_sock.send(server_get_response(WELCOME).encode())
        print('Connected to {}'.format(client_addr))

        return client_sock

    except SocketError:
        if client_sock is not None:
            client_sock.close()

        return None


def server_do_request_response(client_sock: socket) -> bool:
    """ Will respond to the next request from the client.
    :param client_sock: The connection to the client.
    :return: True if succesful, False if client disconnected.
    """
    try:
        connected = True
        try:
            request = client_sock.recv(1024).decode()
            print('Client: {}'.format(request))
            req_code, req_data = server_get_request_fields(request)

            response = server_get_response(server_get_response_data(req_code, req_data))
            if is_exit_request_code(req_code):
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


def serve_client(sock: socket) -> None:
    """ Answers all the requests from the client until disconnect.
        To be called after accepting a client (accept_client(sock)).
    :param sock: A socket connected to client. Will be closed afterwards!
    """
    with sock:
        stay_connected = True
        while stay_connected:
            stay_connected = server_do_request_response(sock)
        print('Client disconnected!')


def server_main():
    with get_listen_socket() as listen_sock:
        print('Server listening')

        while True:
            client_sock = accept_client(listen_sock)

            if client_sock is not None:
                serve_client(client_sock)
            else:
                print('Something went wrong with connecting to a client')


def valid_operation(operation_type: str) -> bool:
    """ Is the given string an operation type? (client/server) """
    return operation_type == 'client' or operation_type == 'server'


def get_program_operation_type() -> str:
    """ Weather to open up a server or open a client
    :return: 'client' or 'server'
    """
    operation_type = None
    if len(sys.argv) == 2:
        operation_type = sys.argv[1].lower()

    if (not valid_operation(operation_type)):
        print('How to use this program correctly: \n'
              'python <file-name> <client/server>')

    while not valid_operation(operation_type):
        operation_type = input(' \nWhat do you want to do (client/server)? ')
        operation_type = operation_type.lower()

    return operation_type


def main():
    operation_type = get_program_operation_type()

    print('Ok! openning {}!'.format(operation_type))
    print('')

    if operation_type == 'client':
        client_main()
    else:
        server_main()


if __name__ == '__main__':
    main()
