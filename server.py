from socket import socket, AF_INET, SOCK_STREAM, error as SocketError
from typing import Optional
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


def get_response_data(dataset: data.Dataset,
                      request_code: int,
                      request_data: str) -> str:
    """ Replys to a request.
    :param request_code: The request type.
    :param request_data: The data field of the request.
    :param dataset: The dataset the server uses.
    :return: A response to the request
             (Only the data - use server_get_response).
    """
    resp_func = RESPONSES[request_code]
    response_value = resp_func(dataset, request_data.lower())

    if (isinstance(response_value, Iterable) and
            not isinstance(response_value, str)):
        msg = '\n'.join(response_value)
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


def accept_client(listen_sock: socket) -> Optional[socket]:
    """ Tries accepting the next client.
    :param listen_sock: The socket listening on the server address.
    :return: The socket connected to the client.
             If something went wrong, returns None.
    """
    try:
        client_sock, client_addr = listen_sock.accept()

        client_sock.send(helper.make_message_no_checksum(data=WELCOME))
        print('Connected to {}'.format(client_addr))

        return client_sock

    except SocketError:
        if client_sock is not None:
            client_sock.close()

        return None


def do_request_response(client_sock: socket, dataset: data.Dataset) -> bool:
    """ Will respond to the next request from the client.
    :param client_sock: The connection to the client.
    :param dataset: The dataset the server uses.
    :return: True if succesful, False if client disconnected.
    """
    try:
        connected = True
        try:
            request = client_sock.recv(1024)
            print('Client: {}'.format(request.decode()))
            # req_code, req_data = get_request_fields(request)
            request_dict = helper.parse_message(request)

            if 'code' not in request_dict or 'data' not in request_dict:
                raise helper.Error('Message need a code '
                                   'field and a data field!')

            req_code = int(request_dict['code'])
            req_data = request_dict['data']

            resposne_data = get_response_data(dataset, req_code, req_data)
            response = helper.make_message(data=resposne_data)
            if helper.is_exit_request_code(req_code):
                connected = False

        except helper.ChecksumError as e:
            response = helper.make_message_no_checksum(
                error='ChecksumError',
                actual=e.actual_checksum,
                expected=e.expected_checksum)

        except helper.Error as e:
            response = helper.make_message_no_checksum(
                error=str(e))

        print('Server: {}'.format(response.decode().replace('\n', ', ')))
        client_sock.send(response)

    except SocketError:
        connected = False

    return connected


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

            if client_sock is not None:
                serve_client(client_sock, dataset)
            else:
                print('Something went wrong with connecting to a client')


if __name__ == '__main__':
    main()
