from socket import socket, AF_INET, SOCK_STREAM, error as SocketError
from typing import Tuple, Optional, Dict
import hashlib

import helper

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


def encrypt_password(password: str):
    return hashlib.pbkdf2_hmac('sha256',
                               password.encode(),
                               b'de71446e074cb947baf6',
                               31703).hex()


def get_response(sock: socket, request: bytes) -> Optional[Dict[str, str]]:
    """ Gets the response of the server to a request.
    :param sock: The socket connected to the server
    :param request: The request.
    :return: The reply from the server as a string
             If disconnected, returns None.
    """
    try:
        sock.send(request)
        response = sock.recv(1025)

    except SocketError:
        return None

    else:
        return helper.parse_message(response)


def connect_to_server() -> Tuple[socket, str]:
    """ Opens a conversation with the server
    :return: A socket with the server and the server's welcome message
    :throws: SocketError
    """
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(helper.SERVER_ADDR)

    welcome_msg = helper.parse_message(sock.recv(1024))['data']

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


def do_request_response(sock: socket, req_code: int, req_data: str) -> bool:
    """ Prints the result of the request to the user.
    :param sock: The connection to the server
    :param req_code: The request code
    :param req_data: The data field of the request
    :return: True if succesful, False if connection error
    """
    request = helper.make_message(code=req_code, data=req_data)
    response = get_response(sock, request)

    if response is None:
        return False

    if 'error' in response:
        if response['error'] == 'checksumerror':
            msg = ('An error has uccoured. '
                   'Please try again. '
                   'Are you using an official client?')
        else:
            msg = response['error']
    elif 'data' in response:
        msg = response['data']
    else:
        print('The server sent a weird message: ')
        msg = response

    print(msg)
    return True


def make_requests_to_server(sock: socket) -> bool:
    """ Makes consecetive requests until disconnected.
    :param sock: Socket to the server
    :return: True if successful, False if connection error
    """
    while True:
        print(REQUEST_CODE_NAMES)
        req_code = get_user_number(1, 8)

        #   If the request code requires data, ask for it
        req_data = ''
        if req_code in REQUEST_CODE_PROMPTS:
            req_data = input(REQUEST_CODE_PROMPTS[int(req_code)])

        success = do_request_response(sock, req_code, req_data)
        if not success:
            return False

        if helper.is_exit_request_code(req_code):
            return True


def start_conversation() -> None:
    connected = False

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

            success = make_requests_to_server(sock)
            if not success:
                print('Oops! It seams you were disconnected. '
                      'Check your internet connection.')
                reconnect = input('Would you like to try reconnecting? y/n: ')
                if reconnect == 'y':
                    start_conversation()


def main():

    do_user_login()

    start_conversation()



if __name__ == '__main__':
    main()
