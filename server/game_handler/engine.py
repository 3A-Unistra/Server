import json
import os
from typing import List, Dict

from server.game_handler.data import Player
from server.game_handler.data.cards import ChanceCard, CommunityCard, CardUtils
from server.game_handler.data.exceptions import \
    GameNotExistsException
from server.game_handler.data.packets import Packet, ExceptionPacket, \
    CreateGame, CreateGameSuccess, BroadcastUpdatedRoom, DeleteRoom, \
    DeleteRoomSuccess

from django.conf import settings
from server.game_handler.data.squares import Square, SquareUtils
from server.game_handler.game import Game, GameState, QueuePacket


class Engine:
    games: Dict[str, Game]
    squares: List[Square]
    chance_deck: List[ChanceCard]
    community_deck: List[CommunityCard]

    def __init__(self):
        self.games = {}
        self.squares = []
        self.chance_deck = []
        self.community_deck = []
        self.__load_json()

    def __load_json(self):
        squares_path = os.path.join(settings.STATIC_ROOT, 'data/squares.json')
        with open(squares_path) as squares_file:
            squares_json = json.load(squares_file)
            self.squares = []
            for j_square in squares_json:
                square = SquareUtils.load_from_json(j_square)
                if square is None:
                    continue
                self.squares.append(square)

        cards_path = os.path.join(settings.STATIC_ROOT, 'data/cards.json')
        with open(cards_path) as cards_file:
            cards_json = json.load(cards_file)
            self.cards = []
            for j_card in cards_json:
                card = CardUtils.load_from_json(j_card)

                if card is None:
                    continue

                if isinstance(card, ChanceCard):
                    self.chance_deck.append(card)
                elif isinstance(card, CommunityCard):
                    self.community_deck.append(card)

    def player_exists(self, player_token: str) -> bool:
        """
        Checks if a player exists in any of the game instances
        """
        for game in self.games.values():
            if game.board.player_exists(player_token):
                return True
        return False

    def add_game(self, game: Game):
        """
        Add a game to active games list

        :param game: Game to add
        """
        if game.uid in self.games:
            return

        # set loaded cards
        game.board.load_data(
            squares=self.squares.copy(),
            chance_deck=self.chance_deck.copy(),
            community_deck=self.community_deck.copy()
        )

        # Reference to games dict (delete game)
        game.games = self.games

        self.games[game.uid] = game

        # start thread only if state is offline
        if game.state is not GameState.OFFLINE:
            return

        # Start thread
        game.start()

    def remove_game(self, uid: str):
        """
        Remove a game from active games list

        :param uid: UUID of an existing game
        """

        if uid not in self.games:
            raise GameNotExistsException()

        game = self.games[uid]

        # Game should be stop thread
        game.state = GameState.STOP_THREAD

        del self.games[uid]

    def send_packet(self, game_uid: str, packet: Packet,
                    channel_name: str = None):
        """
        Add packet to game packets queue
        Blocking thread until packet is added to queue

        :param game_uid: UUID of an existing game
        :param packet: Packet to send
        :param channel_name: Channel name (to contact player)
        """
        if game_uid not in self.games:
            raise GameNotExistsException()

        # Blocking function that adds packet to queue
        self.games[game_uid].packets_queue.put(
            QueuePacket(packet=packet, channel_name=channel_name))

    def delete_room(self, packet):
        """
        delete instance of game as specified by the DeleteRoom packet
        warning : sender of the pocket must be host of the game
        :param packet: packet envoyé
        """

        if not isinstance(packet, DeleteRoom):
            return

        id_room = packet.id_room

        if id_room not in self.games:
            self.send_packet(game_uid=id_room,
                             packet=ExceptionPacket(code=4207),
                             channel_name=packet.player_token)
            return

        # if player sending it isn't host of the game
        if packet.player_token != self.games[id_room].host_player:
            self.send_packet(game_uid=id_room,
                             packet=ExceptionPacket(code=4206),
                             channel_name=packet.player_token)
            return

        nb_players = len(self.games[id_room].board.players)

        # sending update
        self.games[id_room].send_packet_lobby(BroadcastUpdatedRoom(
            id_room=id_room, old_nb_players=nb_players, new_nb_players=1,
            state="CLOSED"))

        # sending success
        self.send_packet(game_uid=id_room, packet=DeleteRoomSuccess(),
                         channel_name=packet.player_token)

        self.remove_game(id_room)

    def create_game(self, packet):
        """
        creating a new game based on the CreateGame packet specification
         sent by a host
        :param packet: MUST BE CREATEGAME INSTANCE otherwise useless
        """
        if not isinstance(packet, CreateGame):
            return

        # if player is already in another game
        if self.player_exists(packet.player_token):
            return  # or maybe send error

        new_game = Game()
        if len(self.games) > getattr(settings, "MAX_NUMBER_OF_GAMES", 10):
            self.send_packet(game_uid=new_game.uid,
                             packet=ExceptionPacket(code=4206),
                             channel_name=packet.player_token)
            self.remove_game(new_game.uid)
            return

        # adding a new game
        id_new_game = new_game.uid
        self.add_game(new_game)

        # adding host to the game
        self.games[id_new_game].board.add_player(Player(
            channel_name=packet.player_token, bot=False))
        # giving him host status
        self.games[id_new_game].host_player = packet.player_token
        # setting up the numbers of players
        self.games[id_new_game].board.players_nb = packet.max_nb_players
        # setting up password
        self.games[id_new_game].board.option_password = packet.password
        # setting up privacy
        self.games[id_new_game].board.option_is_private = packet.is_private
        # setting up starting balance
        if packet.starting_balance != 0:
            self.games[id_new_game].board.starting_balance = \
                packet.starting_balance
        else:
            self.games[id_new_game].board.starting_balance = \
                getattr(settings, "MONEY_START", 1000)
        # sending CreateGameSuccess to host
        self.send_packet(game_uid=id_new_game,
                         packet=CreateGameSuccess(packet.player_token),
                         channel_name=packet.player_token)
        # sending updated room status
        self.games[id_new_game].send_packet_lobby(BroadcastUpdatedRoom(
            id_room=id_new_game, old_nb_players=0, new_nb_players=1,
            state="LOBBY", player=packet.player_token))
