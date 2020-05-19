from socket import socket, AF_INET, SOCK_STREAM, error as SocketError
from typing import Optional, Dict
from collections.abc import Iterable
import data
import helper

RESPONSES = {
    1: lambda x, y: data.get_albums(x),
    2: data.get_songs_in,
    3: data.get_song_length,
    4: data.get_song_lyrics,
    5: data.get_song_album,
    6: data.search_song_by_name,
    7: data.search_song_by_lyrics,
    8: lambda x, y: 'Goodbye!',
}

WELCOME = 'Welcome to the pink floyd server!'

DATASET_FILE_PATH = 'Pink_Floyd_DB.txt'
PASSWORD_FILE_PATH = 'Passwords.txt'


def get_response_data(dataset: data.Dataset,
                      request_code: int,
                      request_data: str) -> str:
    """ Takes a python object and turns it into a string that the client can read.
    :param dataset: The dataset the server uses.
    :param request_code: The request type.
    :param request_data: The data field of the request.
    :return: A string to be read by the client
    """
    resp_func = RESPONSES[request_code]
    response_value = resp_func(dataset, request_data.lower())

    if (isinstance(response_value, Iterable) and
            not isinstance(response_value, str)):
        msg = '\n'.join(response_value)
        if msg == '':
            msg = 'Empty list'
    elif isinstance(response_value, float):
        msg = '{:.2f}'.format(response_value)
    elif response_value is None:
        msg = 'Parameter was not found'
    else:
        msg = str(response_value)

    return msg


def get_listen_socket() -> socket:
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind(helper.SERVER_ADDR)
    sock.listen(1)
    return sock


def recieve(sock: socket) -> Dict[str, str]:
    """ Receives a message from the client and prints it.
    :param sock: The socket with the client.
    :return: A dictionary as returned by helper.parse_message.
    """
    message = sock.recv(1024)
    print('Client: {}'.format(message.decode()))
    return helper.parse_message(message)


def send(sock: socket, checksum: bool = True, **kwargs) -> None:
    """ Sends a message to the client and prints it.
    :param sock: The client socket.
    :param checksum: Wether or not a checksum should be included. Default True.
    :param kwargs: The fields of the message, like in helper.make_message.
    """
    message = (helper.make_message(**kwargs)
               if checksum else
               helper.make_message_no_checksum(**kwargs))
    print('Server: {}'.format(message.decode().replace('\n', ', ')))
    sock.send(message)


def accept_client(listen_sock: socket) -> Optional[socket]:
    """ Tries accepting the next client.
    :param listen_sock: The socket listening on the server address.
    :return: The socket connected to the client.
             If something went wrong, returns None.
    """
    try:
        client_sock, client_addr = listen_sock.accept()
        print('Connected to {}'.format(client_addr))
        send(client_sock, checksum=False, data=WELCOME)
        return client_sock

    except SocketError:
        if client_sock is not None:
            client_sock.close()

        return None


def get_user(sock: socket) -> Optional[str]:
    try:
        login_request = recieve(sock)
        username = login_request['username']
        password = login_request['password']

        login_func = (data.add_new_user
                      if 'new_user' in login_request else
                      data.password_matchs_username)
        login_successful = login_func(PASSWORD_FILE_PATH, username, password)

        if login_successful:
            print('User successfuly logged in!')
            send(sock, login_successful='')
            return username
        else:
            send(sock, error='Invalid username or password')
            return None
    except SocketError:
        return None


def do_request_response(sock: socket, dataset: data.Dataset) -> bool:
    """ Will respond to the next request from the client.
    :param sock: The connection to the client.
    :param dataset: The dataset the server uses.
    :return: True if succesful, False if client disconnected.
    """
    try:
        request = recieve(sock)

        if 'code' not in request or 'data' not in request:
            raise helper.Error('Message need a code '
                               'field and a data field!')

        req_code = int(request['code'])
        req_data = request['data']

        resposne_data = get_response_data(dataset, req_code, req_data)
        send(sock, data=resposne_data)

        if helper.is_exit_request_code(req_code):
            return False

    except helper.ChecksumError as e:
        send(sock, False,
             error='checksumerror',
             actual=e.actual_checksum,
             expected=e.expected_checksum)

    except helper.Error as e:
        send(sock, False, error=str(e))

    except SocketError:
        return False

    return True


def serve_client(sock: socket, dataset: data.Dataset) -> None:
    """ Answers all the requests from the client until disconnect.
        To be called after accepting a client (accept_client(sock)).
    :param sock: A socket connected to client. Will be closed afterwards!
    :param dataset: The dataset the server uses.
    """
    with sock:
        stay_connected = True
        while stay_connected:
            stay_connected = do_request_response(sock, dataset)
        print('Client disconnected!')


def main():

    with open(DATASET_FILE_PATH, 'r') as file:
        text = file.read()
        dataset = data.parse_dataset(text)

    with get_listen_socket() as listen_sock:
        print('Server listening')
        while True:
            client_sock = accept_client(listen_sock)

            if client_sock is None:
                print('Something went wrong with connecting to a client')
            else:
                username = get_user(client_sock)

                if username is None:
                    print('User could not log in')
                else:
                    serve_client(client_sock, dataset)


if __name__ == '__main__':
    main()
