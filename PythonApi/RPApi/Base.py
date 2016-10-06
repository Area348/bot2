import threading

import requests
from PythonApi.Base.Exceptions import VerificationError, BannedError, \
    NoDataError, UndocumatedStatusCodeError, IAmATheaPotError, UnkownKeyError, ToSoonReloginError
from hashlib import sha1
import json
import time

VOS, META, SC_ALL, FOTO_ALL, GEBRUIKER_INFO = range(5)


def parse_time(tijd):
    # todo schrijf deze functie
    return tijd


def _retry_with_new_key_on_error(func):
    def decorate(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except VerificationError:
            self.api_key = None
            self.login()
            return func(self, *args, **kwargs)
    return decorate


class Api:
    instances = dict()

    def __init__(self, username, hashed_password):
        self.username = username
        self.hashed_password = hashed_password
        self.last_update = None
        self.api_key = None
        self.hunternaam = None
        self.api_key_lock = threading.RLock()
        self._base_url = 'http://jotihunt-API-V2.area348.nl/'
        self.login()

    @staticmethod
    def get_instance(username, password):
        if username not in Api.instances:
            hasher = sha1()
            hasher.update(password.encode('utf-8'))
            hashed_password = hasher.hexdigest()
            Api.instances[username] = Api(username, hashed_password)
        else:
            pass
        return Api.instances[username]

    def _send_request(self, root, functie="", data=None):
        r_val = None
        try:
            if self.api_key is None and root != 'login':
                raise UnkownKeyError(root)
            max_t = 24 * 60 * 60  # 1 dag
            if self.last_update is None or time.time() - self.last_update > max_t:
                self.login()
            else:
                self.last_update = time.time()
            if data is None:
                url = self._base_url + root + '/' + self.api_key + '/' + functie
                r = requests.get(url)
            else:
                url = self._base_url + root + '/' + functie
                r = requests.post(url, data=json.dumps(data))
            if r.status_code == 401:
                raise VerificationError(r.content)
            elif r.status_code == 403:
                raise BannedError(r.content)
            elif r.status_code == 404:
                raise NoDataError(r.content)
            elif r.status_code == 418:
                raise IAmATheaPotError(r.content)
            elif r.status_code == 200:
                r_val = r.json()
            else:
                raise UndocumatedStatusCodeError((r.status_code, r.content))
        finally:
            pass
        return r_val

    _send_request_b = _send_request
    _send_request = _retry_with_new_key_on_error(_send_request_b)

    def hunter_namen(self):
        root = 'hunter'
        functie = 'hunter_namen/'
        data = self._send_request(root, functie)
        return data

    def hunter_all(self, tijd=None):
        root = 'hunter'
        functie = 'all/'
        if tijd is not None:
            functie += parse_time(tijd) + '/'
        data = self._send_request(root, functie)
        return data

    def hunter_tail(self, hunter, tijd=None):
        root = 'hunter'
        functie = 'naam/tail/' + str(hunter) + '/'
        if tijd is not None:
            functie += parse_time(tijd) + '/'
        data = self._send_request(root, functie)
        return data

    def hunter_andere(self, hunter, tijd=None):
        root = 'hunter'
        functie = 'andere/' + str(hunter) + '/'
        if tijd is not None:
            functie += parse_time(tijd) + '/'
        data = self._send_request(root, functie)
        return data

    def hunter_single_location(self, hunter_id):
        root = 'hunter'
        functie = str(hunter_id) + '/'
        data = self._send_request(root, functie)
        return data

    def vos(self, team, tijd=None, vos_id=None):
        t = None
        if vos_id is None and tijd is None:
            result = self._vos_last(team)
        elif vos_id is not None and tijd is None:
            result = self._vos_single_location(team, vos_id)
        elif vos_id is None and tijd is not None:
            result = self._vos_all(team, tijd)
        else:
            result = None
        return Response(result, VOS)

    def _vos_last(self, team):
        root = 'vos'
        functie = team + '/last/'
        data = self._send_request(root, functie)
        return data

    def _vos_single_location(self, team, vos_id):
        root = 'vos'
        functie = team + '/' + str(vos_id) + '/'
        data = self._send_request(root, functie)
        return data

    def _vos_all(self, team, tijd):
        root = 'vos'
        functie = team + '/'
        if tijd is not None:
            functie += parse_time(tijd) + '/'
        data = self._send_request(root, functie)
        return data

    def meta(self):
        root = 'meta'
        functie = ''
        data = self._send_request(root, functie)
        return Response(data, META)

    def sc_all(self):
        root = 'sc'
        functie = 'all/'
        data = self._send_request(root, functie)
        return Response(data, SC_ALL)

    def foto_all(self):
        root = 'foto'
        functie = 'all/'
        data = self._send_request(root, functie)
        return Response(data, FOTO_ALL)

    def gebruiker_info(self):
        root = 'gebruiker'
        functie = 'info/'
        data = self._send_request(root, functie)
        return Response(data, GEBRUIKER_INFO)

    def login(self):
        if self.last_update is not None and \
                                time.time() - self.last_update < \
                120:
            raise ToSoonReloginError(time.time() - self.last_update)
        self.api_key_lock.acquire()
        try:
            data = {'gebruiker': self.username, 'ww': self.hashed_password}
            root = 'login'
            self.last_update = time.time()
            response = self._send_request(root, data=data)
            sleutel = response['SLEUTEL']
            self.api_key = sleutel
            import settings
            settings = settings.Settings
            settings.SLEUTEL = sleutel
        finally:
            self.api_key_lock.release()

    def send_hunter_location(self, lat, lon, icon=0):
        if self.hunternaam is None:
            hunternaam = self.username
        else:
            hunternaam = str(self.hunternaam)
        data = {'SLEUTEL': self.api_key,
                'hunter': hunternaam,
                'latitude': str(lat),
                'longitude': str(lon),
                'icon': str(icon)}
        root = 'hunter'
        self._send_request(root, data=data)

    def send_vos_location(self, team, lat, lon, icon=0, info='-'):
        if self.hunternaam is None:
            hunternaam = self.username
        else:
            hunternaam = str(self.hunternaam)
        root = 'vos'
        data = {'SLEUTEL': self.api_key,
                'team': team,
                'hunter': hunternaam,
                'latitude': str(lat),
                'longitude': str(lon), 'icon': str(icon), 'info': str(info)}
        self._send_request(root, data=data)


class Response:
    def __init__(self, json, type):
        self.data = json
        self.type = type

    def __eq__(self, other):
        if other is None:
            return False
        if other.type != self.type:
            return False
        if self.type == VOS:
            return self.data['id'] == other.data['id']

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __iter__(self):
        yield from self.data




