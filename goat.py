import asyncio

from sanic import Sanic, Blueprint, response
from sanic.log import logger

from dataclasses import dataclass, field
from datetime import datetime

app = Sanic(__name__)

goat = Blueprint('goat', url_prefix='/goat')



class Room:
    def __init__(self):
        self.goats_in_room = {}
    
    def send_message(self, data, f=None):
        for goat in filter(f, self.goats_in_room.values()):
            goat.send(data)
    
    @property
    def players(self):
        return '\r\n'.join([goat.player for goat in self.goats_in_room.values()])

class GoatChat:
    rooms = {}
    goats = {}
    available_ids = [*range(10, 100)]
    
    @staticmethod
    def add_goat(id, goat):
        GoatChat.goats[id] = goat

    @staticmethod
    def get_goat(id):
        return GoatChat.goats.get(id, None)
    
    @staticmethod
    def get_room(id):
        return GoatChat.rooms.get(id, Room(id))
    
    @staticmethod
    def find_number(n):
        if n.isnumeric():
            return int(n)
        n = ord(n)
        if n < 91:
            return n-55
        return n-61

    @staticmethod
    def find_code(n):
        n = int(n)
        if n < 10:
            return n
        if n < 36:
            return chr(n + 55)
        return chr(n + 61)

@goat.listener('before_server_start')
async def start_garbage_collector(app, loop):
    asyncio.create_task(garbage_collector())
                     
async def garbage_collector():
    while True:
        for goat in GoatChat.goats.copy().values():
            time_since_last_poll = datetime.now() - goat.last_poll
            if time_since_last_poll.seconds > 15:
                goat.leave_room()
                available_ids.append(goat.player_id)
                if goat.player_id in GoatChat.goats:
                    del  GoatChat.goats[goat.player_id]
        await asyncio.sleep(5)

         
    
@dataclass
class Goat:
    name: int = 0
    player_id: int = 0
    room: int = 0
    character: int = 0
    custom: int = 0
    direction: int =0
    x: int = 0
    y: int = 0
    chat: str = ""
    
    room_obj: Room = None
    
    last_poll: datetime = datetime.now()
    
    message_queue: list = field(default_factory=list)
    
    @property
    def messages(self):
        data = '\r\n'.join(map(str, self.message_queue))
        self.message_queue.clear()
        return data
    
    def parse_raw(self, data):
        self.character = GoatChat.find_number(data[0])
        self.custom = GoatChat.find_number(data[1])
        self.direction = GoatChat.find_number(data[2])
        self.x = GoatChat.find_number(data[3])
        self.y = GoatChat.find_number(data[4])
        self.chat = data[5::]

    def parse_data(self, data):
        self.room = int(data[0])
        data = data[3::]
        self.parse_raw(data)
        
    def parse_data_chat(self, data):
        data = data[2::]
        self.parse_raw(data)
        self.room_obj.send_message(self.data)
    
    def join_room(self):
        self.room_obj = GoatChat.get_room(self.room)
        self.room_obj.goats_in_room[self.player_id] = self
        self.room_obj.send_message(self.player)
    
    def leave_room(self):
        if self.room_obj is not None:
            self.room_obj.send_message(self.player_id, lambda goat: goat.player_id != self.player_id)
            del self.room_obj.goats_in_room[self.player_id]
            if len(self.room_obj.goats_in_room) < 1:
                del GoatChat.rooms[self.room]
            
    def send(self, data):
        self.message_queue.append(data)
    
    @property
    def data(self):
        data = f'{self.player_id}{GoatChat.find_code(self.character)}{GoatChat.find_code(self.custom)}{GoatChat.find_code(self.direction)}{GoatChat.find_code(self.x)}{GoatChat.find_code(self.y)}{self.chat}'
        self.chat = ""
        return data
     
    @property
    def player(self):
        data = f'{self.player_id}{GoatChat.find_code(self.character)}{GoatChat.find_code(self.custom)}{GoatChat.find_code(self.direction)}{GoatChat.find_code(self.x)}{GoatChat.find_code(self.y)}{self.name}'
        return data
     


@goat.post('/new')
async def new_goat(request):
    username = request.form.get('n', None)
    if username is None:
        return response.text('&e=2')
    for goat in GoatChat.goats.values():
        if goat.name == username:
            return response.text('&e=2')
   
    if not GoatChat.available_ids:
        return response.text('&e=3')
    
    id = GoatChat.available_ids.pop(0)
    GoatChat.add_goat(id, Goat(name=username,player_id=id,last_poll=datetime.now()))
    m = 0
    if username == 'iRod':
        m = 1
    return response.text(f'&id={id}&e=0&n=test&m={m}')
    
@goat.post('/join')
async def join_room(request):
    data = request.form.get('d', None)
    username = request.form.get('n', None)
    id = int(request.form.get('id', -999))
    if id < 0 or username is None or id not in GoatChat.goats or data is None:
        return response.text('Invalid Session!')
    
    goat = GoatChat.get_goat(id)
    if goat.room_obj is not None:
        goat.leave_room()
    
    goat.parse_data(data)
    goat.join_room()
    goat.last_poll = datetime.now()
    return response.text(f'&p={goat.room_obj.players}&e=0')
    
@goat.post('/chat')
async def server_chat(request):
    data = request.form.get('d', None)
    id = int(request.form.get('id', -999))
    if id < 0 or id not in GoatChat.goats or data is None:
        return response.text('&e=1')
    goat = GoatChat.get_goat(id)
    
    
    if len(data) < 6:
        goat.last_poll = datetime.now()
        return response.text(f'&c={goat.messages}&e=0')
    
    
    goat.parse_data_chat(data)
    goat.last_poll = datetime.now()
    return response.text(f'&c={goat.messages}&e=0')
    
@goat.post('/drop')
async def disconnect(request):
    id = int(request.form.get('id', -999))
    if id < 0 or id not in GoatChat.goats:
        return response.text('&e=1')
    goat = GoatChat.get_goat(id)
    del GoatChat.goats[id]
    goat.leave_room()
    available_ids.append(id)
    return response.text('&e=0')
    
if __name__ == '__main__':
    app.blueprint(goat)
    app.run(host="0.0.0.0", port=8000)
