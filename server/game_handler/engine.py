import copy
import json
import os
from typing import List, Dict

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from server.game_handler.data import Player
from server.game_handler.data.cards import ChanceCard, CommunityCard, CardUtils
from server.game_handler.data.exceptions import \
    GameNotExistsException
from server.game_handler.data.packets import Packet, ExceptionPacket, \
    CreateGame, CreateGameSucceed, UpdateReason, BroadcastUpdateLobby, \
    BroadcastUpdateRoom, LeaveRoom, BroadcastNewRoomToLobby, \
    LeaveRoomSucceed, NewHost, StatusRoom, FriendConnected, FriendDisconnected

from django.conf import settings

from server.game_handler.data.player import get_player_avatar, \
    get_player_username
from server.game_handler.data.squares import Square, SquareUtils
from server.game_handler.game import Game, GameState, QueuePacket
from server.game_handler.models import User, UserFriend


class Engine:
    games: Dict[str, Game]
    squares: List[Square]
    chance_deck: List[ChanceCard]
    community_deck: List[CommunityCard]
    # dictionary of id and channel_name for player in Lobby
    connected_players: Dict

    def __init__(self):
        self.games = {}
        self.squares = []
        self.chance_deck = []
        self.community_deck = []
        self.connected_players = {}
        self.channel_layer = get_channel_layer()
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
        for game in self.games:
            if self.games[game].board.player_exists(player_token):
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
            squares=[copy.copy(square) for square in self.squares],
            chance_deck=[copy.copy(card) for card in self.chance_deck],
            community_deck=[copy.copy(card) for card in self.community_deck],
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

        print("remove_game(%s)" % uid)

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

    def leave_game(self, packet, game_token: str, channel_name: str):
        """
        in case the host wants to leave the game and he is the only one
        remaining, we need to handle the LeaveRoom packet here before sending
        it to the concerned game instance
        :param packet: must be LeaveRoom instance
        :param game_token:
        :param channel_name:
        """

        if not isinstance(packet, LeaveRoom):
            return

        # check if player is part of a room
        if not self.player_exists(packet.player_token):
            # ignore
            return

        game = self.games[game_token]

        if self.games[game_token].state == GameState.WAITING_PLAYERS:
            return

        # player leaves game group
        async_to_sync(
            game.channel_layer.group_discard)(game.uid,
                                              channel_name)

        if len(game.board.players) > 1 and \
                packet.player_token == game.host_player.get_id():

            for player in game.board.players:
                if not player.bot:
                    if player.get_id() != game.host_player.get_id():
                        game.host_player = player
                        game.host_channel = player.channel_name
                        game.send_packet_to_group(NewHost(
                            player_token=game.host_player.get_id()
                        ), game.uid)
                        break

        # if checks passed, kick out player
        piece = game.board.get_player(packet.player_token).piece
        avatar = get_player_avatar(packet.player_token)
        username = get_player_username(packet.player_token)
        game.board.remove_player(
        game.board.get_player(packet.player_token))

        game.send_lobby_packet(channel_name=channel_name,
                               packet=LeaveRoomSucceed(
                                   avatar_url=avatar,
                                   username=username
                               ))

        nb_players = game.board.get_online_real_players_count()

        if nb_players > 0:
            reason = UpdateReason.PLAYER_LEFT

            # broadcast updated room status
            # this should be sent to lobby and to game group
            update = BroadcastUpdateRoom(game_token=game.uid,
                                         nb_players=nb_players,
                                         reason=reason.value,
                                         player=packet.player_token,
                                         avatar_url=avatar,
                                         username=username,
                                         piece=piece
                                         )

            game.send_packet_to_group(update, game.uid)

        else:
            # Delete room
            self.remove_game(game_token)
            reason = UpdateReason.ROOM_DELETED

        update = BroadcastUpdateLobby(game_token=game.uid,
                                      reason=reason.value)
        game.send_packet_to_group(update, "lobby")

        # because the player left, he has to get the status of all the rooms
        self.send_all_lobby_status(channel_name=channel_name)

        # add player to the lobby group
        async_to_sync(
            game.channel_layer.group_add)("lobby", channel_name)

    def create_game(self, packet: Packet, channel_name: str):
        """
        creating a new game based on the CreateGame packet specification
         sent by a host
        :param packet: MUST BE CREATEGAME INSTANCE otherwise useless
        """
        print("[engine.create_game()] got in function")
        if not isinstance(packet, CreateGame):
            return

        # if player is already in another game
        if self.player_exists(packet.player_token):
            print("[engine.create_game()] player in another game")
            return  # or maybe send error

        try:  # get user from database
            user = User.objects.get(id=packet.player_token)
        except User.DoesNotExist:
            print("[engine.create_game()] user does not exists")
            return

        new_game = Game()
        self.add_game(new_game)
        if len(self.games) > getattr(settings, "MAX_NUMBER_OF_GAMES", 10):
            print("[engine.create_game()] too many games")
            self.send_packet(game_uid=new_game.uid,
                             packet=ExceptionPacket(code=4206),
                             channel_name=channel_name)
            self.remove_game(new_game.uid)
            return

        print("[engine.create_game()] created game instance")
        print("[engine.create_game() game uid: " + new_game.uid)

        board = new_game.board

        # adding host to the game
        player = Player(user=user,
                        channel_name=channel_name,
                        bot=False)
        board.add_player(player)

        new_game.host_player = player
        new_game.host_channel = channel_name
        board.set_nb_players(packet.max_nb_players)
        board.option_password = packet.password
        board.option_is_private = packet.is_private
        new_game.public_name = packet.game_name
        board.option_first_round_buy = packet.option_first_round_buy
        board.option_auction_enabled = packet.option_auction
        board.set_option_max_time(packet.option_max_time)
        board.set_option_max_rounds(packet.option_max_rounds)
        board.set_option_start_balance(packet.starting_balance)

        # sending CreateGameSuccess to host
        piece = board.assign_piece(player.user)
        new_game.send_lobby_packet(channel_name=channel_name,
                                   packet=CreateGameSucceed(
                                       game_token=new_game.uid,
                                       player_token=packet.player_token,
                                       piece=piece,
                                       avatar_url=get_player_avatar(
                                           packet.player_token),
                                       username=get_player_username(
                                           packet.player_token)))

        # this is sent to lobby no need to send it to game group, host is alone
        update = BroadcastNewRoomToLobby(
            game_token=new_game.uid,
            game_name=new_game.public_name,
            nb_players=len(board.players),
            max_nb_players=board.players_nb,
            is_private=board.option_is_private,
            has_password=(board.option_password != ""))

        # adding host to the game group
        async_to_sync(new_game.channel_layer.group_discard)("lobby",
                                                            channel_name)

        async_to_sync(new_game.channel_layer.group_add)(new_game.uid,
                                                        channel_name)

        new_game.send_packet_to_group(update, "lobby")

        new_game.send_lobby_packet(
            channel_name=channel_name,
            packet=StatusRoom(
                game_token=new_game.uid,
                game_name=new_game.public_name,
                nb_players=len(new_game.
                               board.players),
                max_nb_players=new_game.board.players_nb,
                players=[packet.player_token],
                players_username=[get_player_username(packet.player_token)],
                players_avatar_url=[get_player_avatar(packet.player_token)],
                option_auction=False,
                option_double_on_start=False,
                option_max_time=new_game.board.option_max_time,
                option_max_rounds=new_game.board.option_max_rounds,
                option_first_round_buy=False,
                starting_balance=new_game.board.starting_balance
            ))

    def send_all_lobby_status(self, channel_name: str):
        """
        send status of all the games that are in LOBBY state
        :param channel_name: player_token to send the status to
        """
        print("game length: %d" % len(self.games))
        for game in self.games:
            game_c = self.games[game]
            board = game_c.board
            print("Processing state %d for %s" % (
                game_c.state.value, game_c.public_name))
            if game_c.state == GameState.LOBBY:
                packet = BroadcastNewRoomToLobby(
                    game_token=game,
                    game_name=game_c.public_name,
                    nb_players=len(board.players),
                    max_nb_players=board.players_nb,
                    is_private=board.option_is_private,
                    has_password=(board.option_password != ""))
                game_c.send_lobby_packet(channel_name=channel_name,
                                         packet=packet)

    def send_friend_notification(self, channel_name: str, player_token: str):
        # fetch les amis du joueur dans la base de données
        # regarder si les joueurs sont connecté à un websocket
        # leur envoyer à eux un paquet FriendConnected
        # envoyer au channel un paquet FriendConnected par ami connecté

        # getting friends from database
        try:
            friends = UserFriend.objects.filter(user_id=player_token)
        except UserFriend.DoesNotExist:
            return

        for friend in friends:
            friend_token = friend.id
            # if friend is connected
            if friend_token in self.connected_players:
                # sending to player that his friend is connected
                packet = FriendConnected(friend_token=friend_token,
                                         username=get_player_username(
                                             friend_token),
                                         avatar_url=get_player_avatar(
                                             friend_token)
                                         )

                async_to_sync(self.channel_layer.send)(
                    channel_name, {
                        'type': 'lobby.callback',
                        'packet': packet.serialize()
                    })

                # sending to friend that the player is connected
                packet = FriendConnected(friend_token=player_token,
                                         username=get_player_username(
                                             player_token),
                                         avatar_url=get_player_avatar(
                                             player_token)
                                         )
                async_to_sync(self.channel_layer.send)(
                    self.connected_players[friend_token], {
                        'type': 'lobby.callback',
                        'packet': packet.serialize()
                    })

    def disconnect_player(self, player_token: str, channel_name: str):

        try:
            friends = UserFriend.objects.filter(user_id=player_token)
        except UserFriend.DoesNotExist:
            return

        for friend in friends:
            friend_token = friend.id
            # if friend is connected
            if friend_token in self.connected_players:
                # sending to friends that the player is gonna disconnect

                packet = FriendDisconnected(friend_token=player_token,
                                            username=get_player_username(
                                             player_token),
                                            avatar_url=get_player_avatar(
                                             player_token)
                                            )

                async_to_sync(self.channel_layer.send)(
                    self.connected_players[friend_token], {
                        'type': 'lobby.callback',
                        'packet': packet.serialize()
                    })

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

        self.leave_game(LeaveRoom(player_token=player_token,
                                  game_token=game_token),
                        game_token=game_token,
                        channel_name=channel_name)
