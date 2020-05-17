from typing import Tuple, Dict, List, Set, NamedTuple, Iterable, Optional
from json import loads as from_json, dumps as to_json


class SongInfo(NamedTuple):
    """ Details about a song. """
    album: str
    lyrics: str
    time: float


Albums = Dict[str, Set[str]]
Songs = Dict[str, SongInfo]


class Dataset(NamedTuple):
    """ The dataset is used for answering requests by the server. """
    songs: Songs
    albums: Albums


def parse_song(song_text: str, album: str) -> Tuple[str, SongInfo]:
    """ Reads a song from part of the dataset text file.
    :param song_text: The text from the file.
    :param album: The name of the album the song belongs to.
    :return: The name of the song and it's data.
    """
    name, _, time, words = song_text.split('::')
    name = name.lower()
    words = words.lower()
    minutes, _, seconds = time.partition(':')
    time_float = int(minutes) + int(seconds) / 60
    return name, SongInfo(lyrics=words, album=album, time=time_float)


def parse_album(album_text: str) -> Tuple[str, Set[Tuple[str, SongInfo]]]:
    """ Reads an album from part of the dataset.
    :param album_text: The text from the file.
    :return: The name of the album, along with a
             list of songs inside it.
    """
    header, _, inner = album_text.partition('\n')

    name, _, _ = header.partition('::')
    name = name.lower()

    song_texts = inner.split('*')[1:]

    return name, {parse_song(song_text, name) for song_text in song_texts}


def parse_dataset(dataset_text: str) -> Dataset:
    """ Reads the full dataset from text.
    :param dataset_text: The text in the format of the dataset.
    :return: The dataset.
    """
    album_texts = dataset_text.split('#')
    album_texts = album_texts[1:]

    albums = [parse_album(album_text)
              for album_text in album_texts]
    albums_dict = {album_name: [song_name for song_name, _ in songs]
                   for album_name, songs in albums}
    songs_dict = dict()
    for _, songs in albums:
        for song_name, song_info in songs:
            songs_dict[song_name] = song_info

    return Dataset(songs=songs_dict, albums=albums_dict)


def get_albums(dataset: Dataset) -> Iterable[str]:
    return dataset.albums.keys()


def get_songs_in(dataset: Dataset, album: str) -> Optional[List[str]]:
    return dataset.albums.get(album)


def get_song_length(dataset: Dataset, song_name: str) -> Optional[float]:
    song = dataset.songs.get(song_name)
    return song.time if song is not None else None


def get_song_lyrics(dataset: Dataset, song_name: str) -> Optional[str]:
    song = dataset.songs.get(song_name)
    return song.lyrics if song is not None else None


def get_song_album(dataset: Dataset, song_name: str) -> Optional[str]:
    song = dataset.songs.get(song_name)
    return song.album if song is not None else None


def search_song_by_name(dataset: Dataset,
                        search_string: str) -> Iterable[str]:
    return (song_name for song_name in dataset.songs.keys()
            if search_string in song_name)


def search_song_by_lyrics(dataset: Dataset,
                          search_string: str) -> Iterable[str]:
    return (song_name for song_name, song_info in dataset.songs.items()
            if search_string in song_info.lyrics)


def password_compare(pass1: str, pass2: str) -> bool:
    """ Use this to securely compare 2 passwords. """
    matchs = True
    for c1, c2 in zip(pass1, pass2):
        matchs &= (c1 == c2)
    if len(pass1) != len(pass2):
        matchs = False
    return matchs


def password_matchs_username(passwords_file_name: str,
                             username: str,
                             password: str) -> bool:
    """ Securely checks if the password belongs to the username """
    with open(passwords_file_name, 'r') as file:
        text = file.read()

    logins: Dict[str, str] = from_json(text)
    logged_password = logins[username]
    return password_compare(logged_password, password)


def add_new_user(passwords_file_name: str,
                 username: str,
                 password: str) -> bool:
    """ Adds a new user with a username and password. """
    with open(passwords_file_name, 'r+') as file:
        logins = from_json(file.read())
        if username not in logins:
            logins[username] = password
            file.seek(0)
            file.write(to_json(logins))
            file.truncate()
    return True


fname = 'login.txt'
