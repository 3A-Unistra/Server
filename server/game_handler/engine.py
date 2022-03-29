import json
import os
from typing import List, Dict

from asgiref.sync import async_to_sync

from server.game_handler.data import Player
from server.game_handler.data.cards import ChanceCard, CommunityCard, CardUtils
from server.game_handler.data.exceptions import \
    GameNotExistsException
from server.game_handler.data.packets import Packet, ExceptionPacket, \
    CreateGame, CreateGameSuccess, DeleteRoom, \
    DeleteRoomSuccess, UpdateReason, BroadcastUpdateLobby, \
    BroadcastUpdateRoom, GetOutRoom

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
        game.board.squares = self.squares.copy()
        game.board.chance_deck = self.chance_deck.copy()
        game.board.community_deck = self.community_deck.copy()

        # search card indexes
        game.board.search_card_indexes()
        # search square indexes
        game.board.search_square_indexes()

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

        game_token = packet.game_token

        if game_token not in self.games:
            self.send_packet(game_uid=game_token,
                             packet=ExceptionPacket(code=4207),
                             channel_name=packet.player_token)
            return

        # if player sending it isn't host of the game
        if packet.player_token != self.games[game_token].host_player:
            self.send_packet(game_uid=game_token,
                             packet=ExceptionPacket(code=4206),
                             channel_name=packet.player_token)
            return

        nb_players = len(self.games[game_token].board.players)

        # everyone goes back to lobby group and leaves game group
        for player in self.games[game_token].board.players:
            current = self.games[game_token]
            async_to_sync(
                    current.channel_layer.group_discard)(current.uid,
                                                         player.channel_name)
            async_to_sync(
                current.channel_layer.group_add)("lobby",
                                                 player.channel_name)

        # sending update to lobby group
        reason = UpdateReason.ROOM_DELETED.value
        self.games[game_token].send_packet_to_group(BroadcastUpdateLobby(
            game_token=game_token,
            nb_players=nb_players,
            reason=reason,
            nb_player_max=self.games[game_token].board.players_nb), "lobby")

        self.games[game_token].send_packet_to_group(BroadcastUpdateRoom(
            game_token=game_token,
            nb_players=nb_players,
            reason=reason,
            player=packet.player_token),
            packet.game_token)

        # sending success
        self.send_packet(game_uid=game_token, packet=DeleteRoomSuccess(),
                         channel_name=packet.player_token)

        self.remove_game(game_token)

    def leave_game(self, packet):
        """
        in case the host wants to leave the game and he is the only one
        remaining, we need to handle the GetOutRoom packet here before sending
        it to the concerned game instance
        :param packet: must be GetOutRoom instance
        """

        if not isinstance(packet, GetOutRoom):
            return

        # check if player is part of a room
        if not self.player_exists(packet.player_token):
            # ignore
            return

        game_token = packet.game_token

        if len(self.games[game_token].board.players) == 1:
            self.delete_room(DeleteRoom(player_token=packet.player_token,
                             game_token=game_token))

            async_to_sync(self.games[game_token].channel_layer.
                          group_add)("lobby", packet.player_token)

            async_to_sync(self.games[game_token].channel_layer.
                          group_discard)(game_token,
                                         packet.player_token)

            return

        self.games[game_token].packets_queue.put(packet)

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
        new_game.board.add_player(Player(
            channel_name=packet.player_token, bot=False))

        new_game.host_player = packet.player_token
        new_game.board.players_nb = packet.max_nb_players
        new_game.board.option_password = packet.password
        new_game.board.option_is_private = packet.is_private
        new_game.public_name = packet.name
        new_game.board.option_first_round_buy = packet.option_first_round_buy
        new_game.board.option_auction_enabled = packet.option_auction
        new_game.board.set_option_max_time(packet.option_max_time)
        new_game.board.set_option_maxnb_rounds(packet.option_maxnb_rounds)
        new_game.board.set_option_start_balance(packet.starting_balance)

        # sending CreateGameSuccess to host
        piece = new_game.board.assign_piece(packet.player_token)
        self.send_packet(game_uid=id_new_game,
                         packet=CreateGameSuccess(packet.player_token, piece),
                         channel_name=packet.player_token)
        # sending updated room status
        reason = UpdateReason.ROOM_CREATED.value

        # this is sent to lobby no need to send it to game group, host is alone
        update = BroadcastUpdateLobby(
            game_token=id_new_game,
            nb_players=1,
            reason=reason,
            nb_player_max=packet.max_nb_players)
        new_game.send_packet_to_group(update, "lobby")
        # adding host to the game group
        async_to_sync(
            new_game.channel_layer.group_discard)(new_game.uid,
                                                  packet.player_token)

    def send_all_lobby_status(self, player_token: str):
        """
        send status of all the games that are in LOBBY state
        :param player_token: player_token to send the status to
        """
        for game in self.games:
            if self.games[game].state == GameState.LOBBY:
                packet = BroadcastUpdateLobby(
                    game_token=game,
                    nb_players=len(self.games[game].board.players),
                    reason=UpdateReason.NEW_CONNECTION.value,
                    nb_player_max=self.games[game].board.players_nb)
                self.games[game].send_packet(player_token, packet)

    def disconnect_player(self, player_token: str):

        # find out if the player is in a game and which one
        in_game = False
        game_token = ""
        for game in self.games:
            if self.games[game].board.player_exists(player_token):
                game_token = game
                in_game = True
                break

        if not in_game:
            # this has been handled in the lobby consumer, should not happen
            return

        self.leave_game(GetOutRoom(player_token=player_token,
                                   game_token=game_token))
