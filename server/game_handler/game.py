import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import uuid
from enum import Enum
from threading import Thread
from queue import Queue
from typing import Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import pause

from server.game_handler import models
from server.game_handler.data import Board, Player, Card
from server.game_handler.data.auction import Auction
from server.game_handler.data.cards import ChanceCard, CardActionType, \
    CommunityCard
from server.game_handler.data.exchange import Exchange, ExchangeState
from server.game_handler.data.packets import PlayerPacket, Packet, \
    InternalCheckPlayerValidity, GameStart, ExceptionPacket, AppletReady, \
    GameStartDice, GameStartDiceThrow, GameStartDiceResults, RoundStart, \
    PingPacket, PlayerDisconnect, InternalPlayerDisconnect, RoundDiceChoice, \
    RoundDiceChoiceResult, RoundDiceResults, PlayerExitPrison, \
    EnterRoom, LaunchGame, AppletPrepare, EnterRoomSucceed, \
    BroadcastUpdateRoom, PlayerEnterPrison, PlayerMove, \
    PlayerUpdateBalance, RoundRandomCard, PlayerPayDebt, \
    ActionEnd, ActionTimeout, ActionBuyProperty, \
    ActionMortgageProperty, ActionUnmortgageProperty, ActionBuyHouse, \
    ActionSellHouse, PlayerPropertyPacket, ActionBuyPropertySucceed, \
    ActionMortgageSucceed, ActionUnmortgageSucceed, ActionBuyHouseSucceed, \
    ActionSellHouseSucceed, ActionExchange, ActionExchangePlayerSelect, \
    ActionExchangeTradeSelect, ActionExchangeSend, ActionExchangeAccept, \
    ActionExchangeDecline, ActionExchangeCounter, \
    AddBot, UpdateReason, BroadcastUpdateLobby, StatusRoom, \
    ExchangeTradeSelectType, ActionExchangeTransfer, ExchangeTransferType, \
    ActionExchangeCancel, ActionAuctionProperty, AuctionBid, AuctionEnd, \
    ActionStart, PlayerDefeat, ChatPacket, PlayerReconnect, DeleteBot, \
    GameWin, GameEnd, AddBotSucceed, DeleteBotSucceed

from server.game_handler.models import User
from django.conf import settings
from server.game_handler.data.squares import GoSquare, TaxSquare, \
    FreeParkingSquare, OwnableSquare, ChanceSquare, CommunitySquare, \
    GoToJailSquare, PropertySquare


class GameState(Enum):
    # To stop thread
    STOP_THREAD = -2

    # Server is offline
    OFFLINE = -1

    # Lobby mode
    LOBBY = 0

    # Waiting that all players connecting (AppletReady)
    WAITING_PLAYERS = 1

    # Timeout between WAITING_PLAYERS and START_DICE
    STARTING = 2

    # Timeout, waiting for some time before displaying results
    START_DICE = 3

    # If reroll must be done, waiting some time before start_dice state
    START_DICE_REROLL = 4

    # START_DICE successful, wait some time before starting game
    FIRST_ROUND_START_WAIT = 5

    # Time before a new round is started
    ROUND_START_WAIT = 6

    # Time between start and displaying dice results
    ROUND_DICE_CHOICE_WAIT = 7

    # Time between RoundDiceResults and ActionStart (animations)
    ACTION_START_WAIT = 8

    # Time between ActionStart and ActionTimeout (actions)
    ACTION_TIMEOUT_WAIT = 9

    # When an auction was started (switches from ACTION_TIMEOUT_WAIT)
    ACTION_AUCTION = 10

    GAME_WIN_TIMEOUT = 11

    GAME_END_TIMEOUT = 12


@dataclass
class QueuePacket:
    packet: Packet
    channel_name: str


class Game(Thread):
    uid: str
    state: GameState
    board: Board
    packets_queue: Queue
    timeout: datetime
    start_date: datetime

    public_name: str
    CONFIG: {}
    # reference to games dict
    games: {}
    host_player: Player

    def __init__(self, **kwargs):
        self.uid = str(uuid.uuid4())
        super().__init__(daemon=True, name="Game_%s" % self.uid, **kwargs)
        self.channel_layer = get_channel_layer()
        self.state = GameState.OFFLINE
        self.packets_queue = Queue()
        self.CONFIG = getattr(settings, "ENGINE_CONFIG", None)
        self.tick_duration = 1.0 / self.CONFIG.get('TICK_RATE')
        self.board = Board()
        self.timeout = datetime.now()

    def run(self) -> None:
        # Starting game thread
        self.state = GameState.LOBBY
        # Set start date
        self.start_date = datetime.now()

        # while state is not stop thread
        while self.state is not GameState.STOP_THREAD:
            # get unix time in seconds before tick processing
            start = time.time()

            # process game tick
            self.tick()

            # sleep until(start + tick_duration)
            # To reduce tick loss if tick processing is too long
            pause.until(start + self.tick_duration)

        # execute last func before stop
        self.proceed_stop()

    def tick(self):
        """
        Main function: every tick, this function will be executed
        """

        # Blocking queue
        # self.packets_queue.join()

        # Store all packets in temp array
        # If packet processing is taking too much time,
        # The queue will be locked for a too long period
        packets = []

        while not self.packets_queue.empty():
            packets.append(self.packets_queue.get(block=False))

        # Unblock
        # self.packets_queue.task_done()

        # Process all packets in queue
        for packet in packets:
            self.process_packet(packet)

        # Do logic here
        self.process_logic()

    def process_packet(self, queue_packet: QueuePacket):
        packet: Packet = queue_packet.packet
        print("process_packet(%s)" % packet.serialize())

        # check player validity
        if isinstance(packet, InternalCheckPlayerValidity):
            # Only accept connection, if player exists and game is started

            player: Optional[Player] = None

            if not self.board.player_exists(packet.player_token):
                valid = False
            elif self.state.value <= GameState.LOBBY.value:
                valid = False
            # Player already online
            else:
                player = self.board.get_player(packet.player_token)
                valid = not player.online

            self.send_packet(
                channel_name=queue_packet.channel_name,
                packet=InternalCheckPlayerValidity(valid=valid))

            if not valid:
                return

            # Change channel_name
            player.channel_name = queue_packet.channel_name
            return

        # Before Player validity check
        if self.state is GameState.LOBBY and isinstance(packet, EnterRoom):

            try:  # get user from database
                user = User.objects.get(id=packet.player_token)
            except User.DoesNotExist:
                return

            if packet.password != "":
                if packet.password != self.board.option_password:
                    self.send_lobby_packet(channel_name=queue_packet.
                                           channel_name,
                                           packet=ExceptionPacket(
                                               code=4201))
                    return
            # if game is full
            if len(self.board.players) == self.board.players_nb:
                self.send_lobby_packet(channel_name=queue_packet.
                                       channel_name,
                                       packet=ExceptionPacket(code=4202))
                return

            # all the checks are fine, add the player to the game
            p = Player(user=user, channel_name=queue_packet.channel_name,
                       bot=False)
            self.board.add_player(p)

            # player leaves lobby group
            async_to_sync(self.channel_layer.group_discard)(
                "lobby", queue_packet.channel_name
            )

            nb_players = len(self.board.players)

            # send success of getting in room
            piece = self.board.assign_piece(user)
            self.send_lobby_packet(
                channel_name=queue_packet.channel_name,
                packet=EnterRoomSucceed(game_token=self.uid,
                                        piece=piece,
                                        avatar_url=p.user.avatar,
                                        username=p.user.name,
                                        host_token=self.host_player.get_id()
                                        )
            )

            reason = UpdateReason.NEW_PLAYER.value

            update = BroadcastUpdateRoom(game_token=self.uid,
                                         nb_players=nb_players,
                                         reason=reason,
                                         player=packet.player_token,
                                         avatar_url=p.user.avatar,
                                         username=p.user.name,
                                         piece=self.board.
                                         get_player(packet.player_token).piece
                                         )
            # sending to the people in the game
            self.send_packet_to_group(update, self.uid)

            # add player to this specific game group
            async_to_sync(self.channel_layer.group_add)(
                self.uid, queue_packet.channel_name
            )

            # sending status of room
            players_data = []
            for player in self.board.players:
                players_data.append({
                    "player_token": player.get_id(),
                    "username": player.user.name,
                    "avatar_url": player.user.avatar,
                    "piece": player.piece
                })

            status = StatusRoom(game_token=self.uid,
                                game_name=self.public_name,
                                nb_players=nb_players,
                                max_nb_players=self.board.players_nb,
                                players_data=players_data,
                                option_auction=self.
                                board.option_auction_enabled,
                                option_double_on_start=self.
                                board.option_go_case_double_money,
                                option_max_rounds=self.
                                board.option_max_rounds,
                                option_first_round_buy=self.
                                board.option_first_round_buy,
                                option_max_time=self.
                                board.option_max_time,
                                starting_balance=self.
                                board.starting_balance)
            self.send_lobby_packet(channel_name=queue_packet.channel_name,
                                   packet=status)

            # broadcast to lobby group
            # sent to lobby and to game group
            update = BroadcastUpdateLobby(game_token=self.uid,
                                          reason=reason)
            # sending to the lobby people
            self.send_packet_to_group(update, "lobby")
            return

        if isinstance(packet, PlayerPacket):
            if not self.board.player_exists(packet.player_token):
                return self.send_packet(
                    channel_name=queue_packet.channel_name,
                    # 4100 => invalid player
                    packet=ExceptionPacket(code=4100))

        if self.state is GameState.LOBBY:
            if isinstance(packet, StatusRoom):
                # broadcast StatusRoom to group

                # only host player can change options
                if queue_packet.channel_name != self.host_player.channel_name:
                    return

                if self.public_name != packet.game_name:
                    # send update to list of lobbies
                    self.send_packet_to_group(packet=BroadcastUpdateLobby(
                        game_token=self.uid,
                        reason=UpdateReason.NEW_GAME_NAME.value,
                        value=packet.game_name
                    ),
                        group_name="lobby")

                self.board.set_nb_players(packet.max_nb_players)
                self.public_name = packet.game_name
                self.board.option_go_case_double_money = \
                    packet.option_double_on_start
                self.board.option_first_round_buy = \
                    packet.option_first_round_buy
                self.board.option_auction_enabled = packet.option_auction
                self.board.set_option_max_time(packet.option_max_time)
                self.board.set_option_max_rounds(packet.option_max_rounds)
                self.board.set_option_start_balance(packet.starting_balance)

                double_on_start = self.board.option_go_case_double_money
                first_round_buy = self.board.option_first_round_buy

                # sending updated option to game group
                players_data = []
                for player in self.board.players:
                    players_data.append({
                        "player_token": player.get_id(),
                        "username": player.user.name,
                        "avatar_url": player.user.avatar,
                        "piece": player.piece
                    })

                self.send_packet_to_group(
                    group_name=self.uid,
                    packet=StatusRoom(
                        game_token=self.uid,
                        game_name=self.public_name,
                        nb_players=len(self.
                                       board.players),
                        max_nb_players=self.board.players_nb,
                        players_data=players_data,
                        option_auction=self.board.option_auction_enabled,
                        option_double_on_start=double_on_start,
                        option_max_time=self.board.option_max_time,
                        option_max_rounds=self.board.option_max_rounds,
                        option_first_round_buy=first_round_buy,
                        starting_balance=self.board.starting_balance
                    ))
                return

            if isinstance(packet, LaunchGame):
                print("received LaunchGame")
                player = self.board.get_player(packet.player_token)
                # check if player_token is the token of the game host
                if player != self.host_player:
                    return  # ignore the launch request

                # game cannot be launched with only one player
                if len(self.board.players) <= 1:
                    return

                print("Set state to GameState.WAITING_PLAYERS")
                # putting the game in waiting mode (waiting for AppletReady
                # from all the players)
                self.state = GameState.WAITING_PLAYERS

                # Send AppletPrepare to group (should disconnect at this pt)
                self.send_packet_to_group(AppletPrepare(), self.uid)

                # setting timeout to wait for the players to send AppletReady
                self.set_timeout(
                    seconds=self.CONFIG.get('WAITING_PLAYERS_TIMEOUT'))
                # broadcasting update to players
                reason = UpdateReason.LAUNCHING_GAME.value

                update = BroadcastUpdateLobby(game_token=self.uid,
                                              reason=reason)
                self.send_packet_to_group(update, "lobby")
                return

            elif isinstance(packet, AddBot):
                player = self.board.get_player(packet.player_token)

                # check if the host is the one sending the packet
                if player != self.host_player:
                    self.send_lobby_packet(channel_name=queue_packet.
                                           channel_name,
                                           packet=ExceptionPacket(code=4205))
                    return

                # check if game is not full
                if len(self.board.players) == self.board.players_nb:
                    self.send_lobby_packet(channel_name=queue_packet.
                                           channel_name,
                                           packet=ExceptionPacket(code=4202))
                    return

                # add bot to the game
                p = Player(bot=True, bot_name=self.board.get_random_bot_name(),
                           bot_level=packet.bot_difficulty)
                self.board.add_player(p)

                # broadcast updated room status
                nb_players = len(self.board.players)
                reason = UpdateReason.NEW_BOT.value

                self.send_packet_to_group(
                    packet=AddBotSucceed(bot_token=p.get_id()),
                    group_name=self.uid
                )

                # this should be sent to lobby and to game group
                update = BroadcastUpdateRoom(game_token=self.uid,
                                             nb_players=nb_players,
                                             reason=reason,
                                             player=p.get_id())
                self.send_packet_to_group(update, self.uid)
                update = BroadcastUpdateLobby(game_token=self.uid,
                                              reason=reason)
                self.send_packet_to_group(update, "lobby")
                return

            elif isinstance(packet, DeleteBot):

                token = packet.bot_token

                if token == "":
                    return

                if not self.board.player_exists(uid=token):
                    return

                bot = self.board.get_player(token)

                self.board.remove_player(player=bot)
                reason = UpdateReason.DELETE_BOT.value

                self.send_packet_to_group(
                    packet=DeleteBotSucceed(bot_token=bot.get_id()),
                    group_name=self.uid
                )

                # this should be sent to lobby and to game group
                update = BroadcastUpdateRoom(game_token=self.uid,
                                             nb_players=len(self.
                                                            board.players),
                                             reason=reason,
                                             player=bot.get_id())

                self.send_packet_to_group(update, self.uid)

                update = BroadcastUpdateLobby(game_token=self.uid,
                                              reason=reason)

                self.send_packet_to_group(update, "lobby")

                return

        else:
            # Heartbeat only in "game"
            if isinstance(packet, PingPacket):
                player = self.board.get_player(packet.player_token)
                if player is None:
                    return
                player.ping = True
                return

        if self.state is GameState.WAITING_PLAYERS:
            # WebGL app is ready to play
            if not isinstance(packet, AppletReady):
                return

            # AppletReady -> connect from client
            # Could be first connect as reconnect
            if isinstance(packet, AppletReady):
                player = self.board.get_player(packet.player_token)

                # Set player to connected (bot disabled)
                player.connect()

                # init ping heartbeat
                player.ping = True
                player.ping_timeout = datetime.now() + timedelta(
                    seconds=self.CONFIG.get('PING_HEARTBEAT_TIMEOUT'))

                # Add player to game group
                async_to_sync(self.channel_layer.group_add)(
                    self.uid, player.channel_name
                )

                # Waiting_players => first connection => not sending anything
                if self.state is not GameState.WAITING_PLAYERS:
                    self.broadcast_packet(PlayerReconnect(
                        player_token=player.get_id()
                    ))
                    # TODO: RECONNECT => Send global state to player
                    return

                return

        if isinstance(packet, InternalPlayerDisconnect):
            # Add player to game group
            player = self.board.get_player(packet.player_token)

            if player is None:
                return

            self.disconnect_player(player, reason="client_disconnect")
            return

        if self.state.value > GameState.WAITING_PLAYERS.value:
            # broadcast_chat
            if isinstance(packet, ChatPacket):
                # if the message is too long
                if len(packet.message) <= 128:
                    self.broadcast_packet(packet)
                return

        if self.state is GameState.START_DICE:

            if not isinstance(packet, GameStartDiceThrow):
                return

            player = self.board.get_player(packet.player_token)

            # Block spam (only accept one GameStartDiceThrow)
            # To avoid broadcast spam
            if player.start_dice_throw_received:
                return

            player.start_dice_throw_received = True

            self.broadcast_packet(GameStartDiceThrow(
                player_token=player.get_id()
            ))

            return

        if self.state is GameState.ROUND_DICE_CHOICE_WAIT:

            if not isinstance(packet, RoundDiceChoice):
                return

            player = self.board.get_player(packet.player_token)

            # Ignore packets sent by players other than current_player
            # (Cannot be a bankrupted player)
            if self.board.get_current_player() != player:
                return

            # Check if enum exists, if not ignore.
            if not RoundDiceChoiceResult.has_value(packet.choice):
                return

            choice = RoundDiceChoiceResult(packet.choice)

            # Ignore this packet, cant roll dices if player in jail
            # and player.jail_turns >= (3)
            if choice is RoundDiceChoiceResult.ROLL_DICES and \
                    player.in_jail and player.jail_turns \
                    >= self.CONFIG.get('MAX_JAIL_TURNS'):
                return

            # Ignore this packet if player has chosen jail_card_chance,
            # but doesnt have one.
            if player.in_jail and choice is RoundDiceChoiceResult \
                    .JAIL_CARD_CHANCE and not player.jail_cards['chance']:
                return

            # Ignore this packet if player has chosen jail_card_community,
            # but doesnt have one.
            if player.in_jail and choice is RoundDiceChoiceResult. \
                    JAIL_CARD_COMMUNITY and not player \
                    .jail_cards['community']:
                return

            self.proceed_dice_choice(player=player, choice=choice)
            return

        if self.state is GameState.ACTION_TIMEOUT_WAIT:
            if isinstance(packet, ActionEnd):
                player = self.board.get_player(packet.player_token)

                # Check if player is current player, else ignore
                if player != self.board.get_current_player():
                    return

                self.proceed_action_tour_end()

            if self.board.current_auction is None:
                self.proceed_exchange(packet)

            if self.board.current_exchange is None:
                self.proceed_auction(packet)

            if self.board.current_auction is None and self.board. \
                    current_exchange is None:
                # Process tour actions packets
                self.proceed_tour_actions(packet)

            return

        if self.state is GameState.ACTION_AUCTION:

            if self.board.current_auction is None:
                return

            self.proceed_auction(packet)

    def process_logic(self):
        # Check pings
        if self.state.value > GameState.LOBBY.value:
            self.proceed_heartbeat()

        # State is waiting that players connecting and send AppletReady
        if self.state is GameState.WAITING_PLAYERS:
            if self.board.get_online_players_count() == len(
                    self.board.players):
                # We can start the game
                self.start_game()
            elif self.timeout_expired():  # Check timeout
                if self.board.get_online_real_players_count() == 0:
                    # After timeout, if no one is connected
                    # Stop game
                    print("Stopping game after timeout with no players online")
                    self.state = GameState.STOP_THREAD
                    return
                else:
                    self.start_game()

        if self.state is GameState.ACTION_AUCTION:
            # board.current_auction could not be null
            if self.board.current_auction.timeout_expired():
                self.proceed_auction_end()
        elif self.timeout_expired():
            if self.state is GameState.STARTING:
                # x Seconds timeout before game start
                self.start_begin_dice()

            elif self.state is GameState.START_DICE:
                self.check_start_dice()

            elif self.state is GameState.START_DICE_REROLL:
                self.start_begin_dice()

            elif self.state is GameState.FIRST_ROUND_START_WAIT:
                self.start_round(first=True)

            elif self.state is GameState.ROUND_START_WAIT:
                self.start_round()

            # If player has not sent his choice to the server,
            # process to timeout choice
            elif self.state is GameState.ROUND_DICE_CHOICE_WAIT:
                player = self.board.get_current_player()
                choice = RoundDiceChoiceResult.ROLL_DICES

                # Player has X jail_turns, force pay.
                if player.in_jail and player.jail_turns >= self.CONFIG.get(
                        'MAX_JAIL_TURNS'):
                    choice = RoundDiceChoiceResult.JAIL_PAY

                self.proceed_dice_choice(player=player, choice=choice)
            elif self.state is GameState.ACTION_START_WAIT:
                # Action start wait
                self.state = GameState.ACTION_TIMEOUT_WAIT
                self.set_timeout(seconds=self.board.option_max_time)
                self.broadcast_packet(ActionStart())

            elif self.state is GameState.ACTION_TIMEOUT_WAIT:
                # Tour is ended
                self.proceed_action_tour_end()

            elif self.state is GameState.GAME_WIN_TIMEOUT:
                self.proceed_end_game()

            elif self.state is GameState.GAME_END_TIMEOUT:
                self.state = GameState.STOP_THREAD

    def proceed_stop(self):
        # Delete game
        self.state = GameState.STOP_THREAD

        if self.uid not in self.games:
            return

        del self.games[self.uid]

    def set_timeout(self, seconds: int):
        self.timeout = datetime.now() + timedelta(seconds=seconds)

    def timeout_expired(self) -> bool:
        return self.timeout < datetime.now()

    def get_remaining_timeout_seconds(self) -> float:
        """
        :return: Get remaining time in seconds before timeout occurs
        """
        return (self.timeout - datetime.now()).total_seconds()

    def start_game(self):
        """
        Set game in "game" mode, (game starting timeout)
        state.STARTING -> timeout_expired() -> start_begin_dice()
        """
        # Set bot names to all players
        self.board.set_bot_names()
        self.state = GameState.STARTING
        self.set_timeout(seconds=self.CONFIG.get('GAME_STARTING_TIMEOUT'))

        options = {
            'go_case_double_money': self.board.option_go_case_double_money,
            'auction_enabled': self.board.option_auction_enabled,
            'is_private': self.board.option_is_private,
            'max_rounds': self.board.option_max_rounds,
            'max_time': self.board.option_max_time,
            'first_round_buy': self.board.option_first_round_buy
        }

        # set money
        for player in self.board.players:
            player.money = self.board.starting_balance

        # send coherent information to all players
        players = []
        for player in self.board.get_online_players():
            players.append(player.get_coherent_infos())

        timeouts = {'WAITING_PLAYERS_TIMEOUT': self.CONFIG.get(
            'WAITING_PLAYERS_TIMEOUT'),
            'GAME_STARTING_TIMEOUT': self.CONFIG.get(
                'GAME_STARTING_TIMEOUT'),
            'START_DICE_WAIT': self.CONFIG.get('START_DICE_WAIT'),
            'START_DICE_REROLL_WAIT': self.CONFIG.get(
                'START_DICE_REROLL_WAIT'),
            'ROUND_START_WAIT': self.CONFIG.get('ROUND_START_WAIT'),
            'ROUND_DICE_CHOICE_WAIT': self.CONFIG.get(
                'ROUND_DICE_CHOICE_WAIT'),
            'ACTION_START_WAIT': self.CONFIG.get('ACTION_START_WAIT'),
            'ACTION_TIMEOUT_WAIT': self.board.option_max_time,
            'AUCTION_TOUR_WAIT': self.CONFIG.get('AUCTION_TOUR_WAIT'),
            'GAME_WIN_WAIT': self.CONFIG.get('GAME_WIN_WAIT'),
            'GAME_END_WAIT': self.CONFIG.get('GAME_END_WAIT')
        }

        self.broadcast_packet(
            GameStart(players=players, options=options, timeouts=timeouts))

    def proceed_end_game(self):
        self.broadcast_packet(GameEnd())

        game = models.Game()
        game.name = self.public_name
        game.duration = (datetime.now() - self.start_date).total_seconds()
        game.date = self.start_date
        game.save()

        sorted_players = []

        for player in self.board.get_online_players():
            sorted_players.append((self.board.get_score(player),
                                   player))

        sorted_players.sort(key=lambda x: x[0])
        rank = 1

        for score, player in sorted_players:
            bot = player.bot and player.online
            houses, hotels = self.board.get_player_buildings_count(player)

            if player.bankrupt_date is None:
                play_duration = game.duration
            else:
                play_duration = (player.bankrupt_date - self.start_date) \
                    .total_seconds()
            game_user = models.GameUser()
            game_user.user = player.user if not bot else None
            game_user.game = game
            game_user.rank = rank
            game_user.money = player.money
            game_user.houses = hotels
            game_user.hotels = hotels
            game_user.host = self.host_player == player
            game_user.bot = bot
            game_user.duration = play_duration
            game_user.save()
            rank += 1

        self.state = GameState.GAME_END_TIMEOUT
        self.set_timeout(seconds=self.CONFIG.get('GAME_END_WAIT'))

    def start_begin_dice(self, re_roll=False):
        """
        After starting timeout is expired,
        Start with game start dice.

        :param re_roll: Dices reroll or not

        state.START_DICE -> timeout_expired() -> check_start_dice()
        """
        self.state = GameState.START_DICE
        self.broadcast_packet(GameStartDice())
        self.set_timeout(seconds=self.CONFIG.get('START_DICE_WAIT'))

        for player in self.board.get_online_players():
            player.roll_dices()
            # The bot should send a packet here (GameStartDiceThrow)
            if player.bot:
                self.broadcast_packet(
                    GameStartDiceThrow(player_token=player.get_id()))

            if re_roll:
                player.start_dice_throw_received = False

    def check_start_dice(self):
        """
        After start dice wait, this function is executed.
        This checks if there are any duplicates scores in players dice results.
        Duplicates:
        >> state.START_DICE_REROLL -> timeout_expired() -> start_begin_dice()
        No duplicates:
        >> state.ROUND_START_WAIT -> timeout_expired() -> start_round(first=1)
        """
        highest = self.board.get_highest_dice()

        # Two players have the same dice score, reroll!
        if highest is None:
            self.state = GameState.START_DICE_REROLL
            self.set_timeout(seconds=self.CONFIG.get('START_DICE_REROLL_WAIT'))
            return

        dice_packet = GameStartDiceResults()

        for player in self.board.get_online_players():
            is_winner = player == highest
            dice_packet.add_dice_result(player_token=player.get_id(),
                                        dice1=player.current_dices[0],
                                        dice2=player.current_dices[1],
                                        win=is_winner)

        self.broadcast_packet(dice_packet)
        self.state = GameState.FIRST_ROUND_START_WAIT
        self.set_timeout(seconds=self.CONFIG.get('ROUND_START_WAIT'))
        self.board.set_current_player(highest)

    def start_round(self, first: bool = False):
        """
        Proceed to start new round, next player chosen, dices rolled
        and packet RoundStart sent.

        :param first: First round or not. Handles next_player()

        state.ROUND_DICE_CHOICE_WAIT -> timeout_expired()
                                                    -> proceed_dice_choice()
        """
        if first:
            # set remaining round players,
            # 3 remaining - 1 = 2 players remaining to get to next round
            self.board.remaining_round_players = len(
                self.board.get_non_bankrupt_players()) - 1
        else:
            player = self.board.get_current_player()

            # Check if player has no doubles and not bankrupt
            if player.doubles <= 0 or player.bankrupt:
                # remaining players - 1
                self.board.next_player()

        # Get current player
        current_player = self.board.get_current_player()
        current_player.roll_dices()

        # Accept new auction
        self.board.round_auction_done = False

        # TODO : AI should randomly do some actions
        # Check if player is in prison -> random between :
        # -> buy if he can or trie to dice
        # maybe execute AI random timeouts.
        round_dice_choice_wait = self.CONFIG.get('ROUND_DICE_CHOICE_WAIT')

        # Bot only waits 5 to 15 seconds
        if current_player.bot:
            round_dice_choice_wait = random.randint(5, 15)

        can_buy = \
            self.board.option_first_round_buy or self.board.current_round != 0

        # broadcast packet to all players
        self.broadcast_packet(RoundStart(
            current_player=current_player.get_id(),
            can_buy_property=can_buy
        ))

        # set timeout for dice choice wait
        self.state = GameState.ROUND_DICE_CHOICE_WAIT
        self.set_timeout(seconds=round_dice_choice_wait)

    def proceed_action_tour_end(self):
        """
        Process to tour end, cancel all actions and check if player is bankrupt
        """
        self.broadcast_packet(ActionTimeout())

        # set exchange to None
        self.board.current_exchange = None

        # Check if player is bankrupt
        self.check_current_player_bankrupt()

        # Check game status (if game is win or no players connected > return)
        if self.check_game_status():
            return

        # Set state to round_start_wait, this will execute round_start()
        self.state = GameState.ROUND_START_WAIT
        self.set_timeout(seconds=self.CONFIG.get('ROUND_START_WAIT'))

    def proceed_tour_actions(self, packet: Packet):
        """
        Proceed tour actions
        :param packet: Packet received
        """
        print("proceed_tour_actions(%s)" % packet.serialize())
        # No buy before 2nd round
        if not self.board.option_first_round_buy and \
                self.board.current_round == 0:
            return

        if not isinstance(packet, PlayerPropertyPacket):
            return

        # No tour actions for ActionAuctionProperty packet
        if isinstance(packet, ActionAuctionProperty):
            return

        # Get player
        player = self.board.get_player(packet.player_token)

        # Check if player is current player, else ignore
        if player != self.board.get_current_player():
            return

        # Its impossible to be bankrupted and be the current_player...
        if player.bankrupt:
            return

        square = self.board.get_property(packet.property_id)

        if square is None:
            # Ignore packet.
            return

        if isinstance(packet, ActionBuyProperty):
            # Check if player is on this property
            if player.position != packet.property_id:
                return

            if square.owner is not None or not player.has_enough_money(
                    square.buy_price):
                # Ignore packet.
                return

            # Set new owner
            square.owner = player

            # broadcast updates
            self.broadcast_packet(ActionBuyPropertySucceed(
                player_token=player.get_id(),
                property_id=square.id_
            ))

            self.player_balance_update(
                player=player,
                new_balance=player.money - square.buy_price,
                reason="action_buy_house"
            )
            return

        if isinstance(packet, ActionMortgageProperty):
            if square.owner != player or square.mortgaged:
                # Ignore packet.
                return

            # For property squares, you can only mortgage when no houses
            # or hotels are in the group
            if isinstance(square, PropertySquare):
                if self.board.get_house_count_by_owned_group(
                        square.color, player=player) > 0:
                    return

            # Mortgage property
            square.mortgaged = True

            # broadcast updates
            self.broadcast_packet(ActionMortgageSucceed(
                player_token=player.get_id(),
                property_id=square.id_
            ))

            self.player_balance_receive(
                player=player,
                amount=math.floor(0.5 * square.buy_price),
                reason="action_mortgage"
            )
            return

        if isinstance(packet, ActionUnmortgageProperty):
            if square.owner != player or not square.mortgaged:
                # Ignore packet.
                return

            price = math.floor(0.6 * square.buy_price)

            if not player.has_enough_money(price):
                return

            # Mortgage property
            square.mortgaged = False

            # broadcast updates
            self.broadcast_packet(ActionUnmortgageSucceed(
                player_token=player.get_id(),
                property_id=square.id_
            ))

            self.player_balance_update(
                player=player,
                new_balance=player.money - price,
                reason="action_unmortgage"
            )
            return

        if isinstance(packet, ActionBuyHouse):
            if not isinstance(square, PropertySquare) or \
                    square.owner != player or square.mortgaged:
                # Ignore packet.
                return

            # Cannot have more than 5 houses (hotel)
            if square.nb_house >= 5:
                return

            # True = hotel, False = house
            buy_hotel = square.nb_house == 4

            # check if bank has enough hotels
            if buy_hotel and not self.board.bank.has_hotels():
                return

            # check if bank has enough houses
            if not buy_hotel and not self.board.bank.has_houses():
                return

            # check if player has enough money
            if not player.has_enough_money(square.house_price):
                return

            group_squares = self.board.get_group_property_squares(
                color=square.color,
                player=player
            )

            # Check if player has all properties in group
            if len(group_squares) != \
                    self.board.total_properties_color_squares[
                        square.color]:
                return

            # Check if all properties in group are not mortgaged
            for g_square in group_squares:
                if g_square.mortgaged:
                    return

            square.nb_house += 1

            # Check if all houses are distributed equally (-1/+1)
            if not PropertySquare.is_distributed_equally(group_squares):
                square.nb_house -= 1
                return

            # All conditions passed ! Can proceed to buy house/hotel
            if buy_hotel:
                self.board.bank.buy_hotel()
            else:
                self.board.bank.buy_house()

            # broadcast updates
            self.broadcast_packet(ActionBuyHouseSucceed(
                player_token=player.get_id(),
                property_id=square.id_
            ))

            self.player_balance_update(
                player=player,
                new_balance=player.money - square.house_price,
                reason="action_buy_house"
            )

        if isinstance(packet, ActionSellHouse):
            if not isinstance(square, PropertySquare) or \
                    square.owner != player:
                # Ignore packet.
                return

            # Cannot sell a house if square has no houses
            if square.nb_house == 0:
                return

            # True = hotel, False = house
            sell_hotel = square.nb_house == 5

            group_squares = self.board.get_group_property_squares(
                color=square.color,
                player=player
            )

            square.nb_house -= 1

            # Check if all houses are distributed equally (-1/+1)
            if not PropertySquare.is_distributed_equally(group_squares):
                square.nb_house += 1
                return

            # All conditions passed ! Can proceed to buy house/hotel
            if sell_hotel:
                self.board.bank.sell_hotel()
            else:
                self.board.bank.sell_house()

            # broadcast updates
            self.broadcast_packet(ActionSellHouseSucceed(
                player_token=player.get_id(),
                property_id=square.id_
            ))

            self.player_balance_receive(
                player=player,
                amount=square.house_price,
                reason="action_sell_house"
            )

    def proceed_auction(self, packet: PlayerPacket):
        if not self.board.option_auction_enabled:
            return

        # No auction before 2nd round
        if not self.board.option_first_round_buy and \
                self.board.current_round == 0:
            return

        # Player has already started one action this round
        if self.board.round_auction_done:
            return

        player = self.board.get_player(packet.player_token)
        auction: Optional[Auction] = self.board.current_auction

        if player.bankrupt:
            return

        if isinstance(packet, ActionAuctionProperty):

            if auction is not None or packet.min_bid < 0:
                return

            if player != self.board.get_current_player():
                return

            current_square = self.board.squares[player.position]

            if not isinstance(current_square, OwnableSquare):
                return

            if current_square.owner is not None or current_square.mortgaged:
                return

            if not player.has_enough_money(packet.min_bid):
                return

            auction_tour_wait = self.CONFIG.get('AUCTION_TOUR_WAIT')

            auction = Auction(player=player,
                              tour_duration=auction_tour_wait,
                              highest_bet=packet.min_bid,
                              square=current_square)

            self.state = GameState.ACTION_AUCTION

            # Get remaining timeout seconds to pause main timeout
            auction.tour_remaining_seconds \
                = int(self.get_remaining_timeout_seconds())
            auction.set_timeout(seconds=auction_tour_wait)

            # setup new auction
            self.board.current_auction = auction

            self.broadcast_packet(ActionAuctionProperty(
                player_token=player.get_id(),
                property_id=current_square.id_,
                min_bid=auction.highest_bid
            ))
            return

        if auction is None or self.state is not GameState.ACTION_AUCTION:
            return

        if isinstance(packet, AuctionBid):

            # Bid should be greater than the highest bid to be accepted
            if not auction.bid(player=player, bid=packet.bid):
                return

            self.broadcast_packet(AuctionBid(
                player_token=player.get_id(),
                bid=packet.bid
            ))

    def proceed_auction_end(self):
        """
        After AUCTION_TIMEOUT has expired
        """

        auction: Optional[Auction] = self.board.current_auction

        if auction is None:
            return

        highest_bid = auction.highest_bid

        if highest_bid > 0:

            if not auction.highest_bidder.has_enough_money(highest_bid):
                highest_bid = -1
            else:
                auction.square.owner = auction.highest_bidder
                self.player_balance_update(
                    player=auction.highest_bidder,
                    new_balance=auction.highest_bidder.money - highest_bid,
                    reason="auction_pay"
                )

        bidder = auction.highest_bidder.get_id() if highest_bid > 0 else ""

        self.broadcast_packet(AuctionEnd(
            player_token=bidder,
            highest_bid=highest_bid,
            remaining_time=auction.tour_remaining_seconds
        ))

        # Only accept a new auction next round!
        self.board.round_auction_done = True
        self.board.current_auction = None

        # If current_player is disconnected, end tour
        if not self.board.get_current_player().online:
            self.proceed_action_tour_end()
            return

        # Recover old timeout
        self.set_timeout(seconds=auction.tour_remaining_seconds)
        self.state = GameState.ACTION_TIMEOUT_WAIT

    def proceed_exchange(self, packet: PlayerPacket):
        exchange: Optional[Exchange] = self.board.current_exchange
        player = self.board.get_player(packet.player_token)

        if player.bankrupt:
            return

        if isinstance(packet, ActionExchange):
            # Start an exchange with someone
            if exchange is not None:
                return

            # Check if player is the current player
            if self.board.get_current_player() != player:
                return

            self.board.current_exchange = Exchange(player)

            self.broadcast_packet(ActionExchange(
                player_token=player.get_id()
            ))
            return

        # All the following packages require an exchange
        if exchange is None:
            return

        if isinstance(packet, ActionExchangeCancel):
            if exchange.state is ExchangeState.STARTED:
                if exchange.player != player:
                    return
            elif exchange.state is ExchangeState.WAITING_SELECT:
                # Both can cancel
                if exchange.selected_player != player and \
                        exchange.player != player:
                    return
            elif exchange.state is ExchangeState.WAITING_RESPONSE:
                # Only player can cancel, selected_player can decline
                if exchange.player != player:
                    return
            elif exchange.state is ExchangeState.WAITING_COUNTER_SELECT:
                # Both can cancel
                if exchange.selected_player != player and \
                        exchange.player != player:
                    return
            elif exchange.state is ExchangeState.WAITING_COUNTER_RESPONSE:
                # Only selected_player can cancel, player can decline
                if exchange.selected_player != player:
                    return
            else:
                return

            self.board.current_exchange = None

            self.broadcast_packet(ActionExchangeCancel(
                player_token=player.get_id()
            ))
            return

        if isinstance(packet, ActionExchangePlayerSelect):
            # Select a player for current_exchange
            if exchange.state is not ExchangeState.STARTED:
                return

            # Check if player is the current player
            if self.board.get_current_player() != player:
                return

            # Not working with bankrupted players
            if player.bankrupt:
                return

            selected = self.board.get_player(packet.selected_player_token)

            if selected is None:
                return

            # Not working with bankrupted players
            if selected.bankrupt:
                return

            exchange.selected_player = selected

            self.broadcast_packet(ActionExchangePlayerSelect(
                player_token=player.get_id(),
                selected_player_token=selected.get_id()
            ))
            return

        if isinstance(packet, ActionExchangeTradeSelect):
            # Select a property for current_exchange

            # Player is selecting a property
            if exchange.state is ExchangeState.STARTED or \
                    exchange.state is ExchangeState.WAITING_SELECT:

                # Check if player is the current player
                if self.board.get_current_player() != player:
                    return

            # Selected_player is selecting a property
            elif exchange.state is ExchangeState.WAITING_COUNTER_SELECT:

                # Check if player is the selected player
                if exchange.selected_player != player:
                    return

            else:
                return

            # If no player was selected, cant select
            if packet.update_affects_recipient and \
                    exchange.selected_player is None:
                return

            owner = exchange.selected_player if \
                packet.update_affects_recipient else exchange.player

            exchange_type = ExchangeTradeSelectType(packet.exchange_type)

            # Check type of exchange
            if exchange_type is ExchangeTradeSelectType.PROPERTY:

                # Verify property_id
                selected_square = self.board.get_property(packet.value)

                # Cannot exchange mortgaged squares
                if selected_square is None or selected_square.mortgaged:
                    return

                if isinstance(selected_square, PropertySquare):
                    if selected_square.nb_house > 0:
                        return

                if selected_square.owner != owner:
                    return

                exchange.add_or_remove_square(
                    square=selected_square,
                    recipient=packet.update_affects_recipient
                )

                self.broadcast_packet(ActionExchangeTradeSelect(
                    player_token=owner.get_id(),
                    value=selected_square.id_,
                    exchange_type=ExchangeTradeSelectType.PROPERTY,
                    update_affects_recipient=packet.update_affects_recipient
                ))

            elif exchange_type is ExchangeTradeSelectType.MONEY:

                money = abs(packet.value)

                if not owner.has_enough_money(money):
                    return

                if packet.update_affects_recipient:
                    exchange.selected_player_money = money
                else:
                    exchange.player_money = money

                self.broadcast_packet(ActionExchangeTradeSelect(
                    player_token=owner.get_id(),
                    value=money,
                    exchange_type=ExchangeTradeSelectType.MONEY,
                    update_affects_recipient=packet.update_affects_recipient
                ))

            elif exchange_type is ExchangeTradeSelectType. \
                    LEAVE_JAIL_CHANCE_CARD:

                if not owner.jail_cards['chance']:
                    return

                card = self.board.chance_deck[
                    self.board.chance_card_indexes['leave_jail']]

                exchange.add_or_remove_card(
                    card=card,
                    recipient=packet.update_affects_recipient
                )

                exc_type = ExchangeTradeSelectType.LEAVE_JAIL_CHANCE_CARD

                self.broadcast_packet(ActionExchangeTradeSelect(
                    player_token=owner.get_id(),
                    value=card.id_,
                    exchange_type=exc_type,
                    update_affects_recipient=packet.update_affects_recipient
                ))

            elif exchange_type is ExchangeTradeSelectType. \
                    LEAVE_JAIL_COMMUNITY_CARD:

                if not owner.jail_cards['community']:
                    return

                card = self.board.community_deck[
                    self.board.community_card_indexes['leave_jail']]

                exchange.add_or_remove_card(
                    card=card,
                    recipient=packet.update_affects_recipient
                )

                exc_type = ExchangeTradeSelectType.LEAVE_JAIL_COMMUNITY_CARD

                self.broadcast_packet(ActionExchangeTradeSelect(
                    player_token=owner.get_id(),
                    value=card.id_,
                    exchange_type=exc_type,
                    update_affects_recipient=packet.update_affects_recipient
                ))

            return

        if isinstance(packet, ActionExchangeSend):

            if exchange is None or exchange.selected_player is None \
                    or not exchange.can_send():
                return

            if exchange.state is ExchangeState.STARTED or \
                    exchange.state is ExchangeState.WAITING_SELECT:

                # Check if player is the current player
                if exchange.player != player:
                    return

                exchange.state = ExchangeState.WAITING_RESPONSE

            elif exchange.state is ExchangeState.WAITING_COUNTER_SELECT:

                # Check if player is the selected_player
                if exchange.selected_player != player:
                    return

                exchange.state = ExchangeState.WAITING_COUNTER_RESPONSE

            else:
                return

            self.broadcast_packet(ActionExchangeSend(
                player_token=player.get_id(),
            ))

            return

        # Next states are actions responses: accept, decline, counter

        if exchange is None or exchange.selected_player is None:
            return

        if exchange.state is ExchangeState.WAITING_RESPONSE:

            # Check if player is the selected player
            if exchange.selected_player != player:
                return

        elif exchange.state is ExchangeState.WAITING_COUNTER_RESPONSE:

            # Check if player is the current player
            if exchange.player != player:
                return

        else:
            return

        if isinstance(packet, ActionExchangeAccept):
            self.broadcast_packet(ActionExchangeAccept(
                player_token=player.get_id(),
            ))

            self.process_exchange_transfers()

            self.board.current_exchange = None
            return

        if isinstance(packet, ActionExchangeDecline):
            self.broadcast_packet(ActionExchangeDecline(
                player_token=player.get_id(),
            ))

            self.board.current_exchange = None
            return

        if isinstance(packet, ActionExchangeCounter):

            if exchange.state is ExchangeState.WAITING_RESPONSE:
                exchange.state = ExchangeState.WAITING_COUNTER_SELECT
            elif exchange.state is ExchangeState.WAITING_COUNTER_RESPONSE:
                exchange.state = ExchangeState.WAITING_SELECT

            self.broadcast_packet(ActionExchangeCounter(
                player_token=player.get_id(),
            ))
            return

    def check_current_player_bankrupt(self):
        """
        Check if the current player is bankrupt, if this is the case, we remove
        it from the game.
        """

        current_player = self.board.get_current_player()

        if not current_player.is_bankrupt():
            return

        current_player.bankrupt = True

        # Reset all owned squares
        for square in self.board.get_owned_squares(current_player):
            square.owner = None

        # Reset cards
        self.board.use_chance_jail_card(current_player)
        self.board.use_community_jail_card(current_player)

        # Send PlayerDefeat
        self.broadcast_packet(PlayerDefeat(
            player_token=current_player.get_id()
        ))

    def check_game_status(self) -> bool:
        """
        Check's if game is win, check's if at least 1 player is still connected
        Checks if total_rounds < max_rounds
        :return Game is win or no players connected
        """
        if self.board.get_online_real_players_count() == 0:
            # TODO : END GAME ?
            return True

        # Win
        if len(self.board.get_non_bankrupt_players()) == 1:
            # One player remaining! Easy win!
            # TODO: proceed to win
            self.proceed_win()
            return True

        # Max rounds option is activated
        if self.board.option_max_rounds > 0:
            # Check if current_round is greater than option
            if self.board.compute_current_round() >= \
                    self.board.option_max_rounds:
                # TODO: proceed to check win.
                self.proceed_win(forced=True)
                return True

        return False

    def proceed_heartbeat(self):
        """
        Checking for all players if timeout expired, and if
        they have ping=False we force the player to disconnect. (timed out)
        Otherwise reset timeout, and ping=False
        """

        for player in self.board.get_online_real_players():
            if player.ping_timeout < datetime.now():
                if not player.ping:
                    self.disconnect_player(player, reason="ping_timeout")
                    continue

                player.ping = False

                # Set timeout for heartbeat
                player.ping_timeout = datetime.now() + timedelta(
                    seconds=self.CONFIG.get('PING_HEARTBEAT_TIMEOUT'))

                self.send_packet_to_player(player, PingPacket())

    def proceed_win(self, forced: bool = False):
        """
        :param forced: Not one non-bankrupt player remaining
        :return:
        """

        if forced:
            winner = self.board.get_highest_scorer()
        else:
            # The winner is the only and last non-bankrupt player
            winner = self.board.get_non_bankrupt_players()[0]

        if winner is None:  # hmmmm
            return

        self.broadcast_packet(GameWin(
            player_token=winner.get_id()
        ))

        self.state = GameState.GAME_WIN_TIMEOUT
        self.set_timeout(seconds=self.CONFIG.get('GAME_WIN_WAIT'))

    def proceed_dice_choice(self, player: Player,
                            choice: RoundDiceChoiceResult):
        """
        Logic: dice choice

        :param player: Player playing
        :param choice: Player's choice
        """
        player.roll_dices()

        # Broadcast roll_dices results
        self.broadcast_packet(RoundDiceResults(
            player_token=player.get_id(),
            result=choice,
            dice1=player.current_dices[0],
            dice2=player.current_dices[1]
        ))

        self.state = GameState.ACTION_START_WAIT
        self.set_timeout(seconds=self.CONFIG.get('ACTION_START_WAIT'))

        # Check if player is in jail
        if player.in_jail:

            if choice == RoundDiceChoiceResult.JAIL_CARD_CHANCE and \
                    player.jail_cards['chance']:
                # Exit prison & use card
                player.exit_prison()
                self.board.use_chance_jail_card(player)

                self.broadcast_packet(PlayerExitPrison(
                    player_token=player.get_id()
                ))
                return

            if choice == RoundDiceChoiceResult.JAIL_CARD_COMMUNITY and \
                    player.jail_cards['community']:
                # Exit prison & use card
                player.exit_prison()
                self.board.use_community_jail_card(player)

                self.broadcast_packet(PlayerExitPrison(
                    player_token=player.get_id()
                ))
                return

            if choice == RoundDiceChoiceResult.JAIL_PAY:
                player.exit_prison()

                self.broadcast_packet(PlayerExitPrison(
                    player_token=player.get_id()
                ))

                self.player_balance_pay(player=player,
                                        receiver=None,
                                        amount=self.CONFIG.get(
                                            'JAIL_LEAVE_PRICE'),
                                        reason="jail_leave_pay")
                return

            if player.dices_are_double():
                self.broadcast_packet(PlayerExitPrison(
                    player_token=player.get_id()
                ))
                player.exit_prison()
                return

            # Add a jail turn
            player.jail_turns += 1

            # Instantly pay if >= MAX_JAIL_TURNS
            if player.jail_turns >= self.CONFIG.get('MAX_JAIL_TURNS'):
                player.exit_prison()

                self.broadcast_packet(PlayerExitPrison(
                    player_token=player.get_id()
                ))

                self.player_balance_pay(player=player,
                                        receiver=None,
                                        amount=self.CONFIG.get(
                                            'JAIL_LEAVE_PRICE'),
                                        reason="jail_leave_pay")

            return

        if player.dices_are_double():
            player.doubles += 1

            if player.doubles >= self.CONFIG.get('MAX_DOUBLES_JAIL'):
                # send player to jail :D
                player.enter_prison()
                self.broadcast_packet(PlayerEnterPrison(
                    player_token=player.get_id()
                ))
                return
        else:
            player.doubles = 0

        # Move player
        self.move_player(player)

    def move_player(self, player: Player):
        """
        Move player to new position given by the dices

        Warning: Dices are not rolled in this function!
        :param player: Player moved
        """

        print("move_player(%s) dices: (%d, %d) current_pos: %d" %
              (player.get_name(),
               player.current_dices[0],
               player.current_dices[1],
               player.position))

        # Move player and check if he reached start
        passed_go = self.board.move_player_with_dices(player)

        print("move_player(%s) updated_pos: %d, passed_go %r" %
              (player.get_name(),
               player.position,
               passed_go))

        # Broadcast new player position
        self.broadcast_packet(PlayerMove(
            player_token=player.get_id(),
            destination=player.position
        ))

        self.proceed_move_player_actions(player=player, passed_go=passed_go)

    def proceed_move_player_actions(self, player: Player,
                                    passed_go: bool = False,
                                    backward: bool = False):
        """
        Proceed move player logic
        :param player: Player concerned
        :param passed_go: Player has passed go after moving
        :param backward: Player moved backward (passed_go != backward)
        """
        case = self.board.squares[player.position]

        # TODO: IMPLEMENT NEW CONFIG MADE BY AKI (Money GO)
        # Player has reached start
        if passed_go and not backward:
            amount = self.CONFIG.get('MONEY_GO')

            # Player case == 0 & double money option is enabled
            if isinstance(case, GoSquare) and \
                    self.board.option_go_case_double_money:
                amount *= 2

            self.player_balance_receive(player=player,
                                        amount=amount,
                                        reason="pass_go")

        # Check destination case
        if isinstance(case, GoToJailSquare):
            player.enter_prison()
            player.position = self.board.prison_square_index

            self.broadcast_packet(PlayerEnterPrison(
                player_token=player.get_id()
            ))
        elif isinstance(case, TaxSquare):
            # Receiver=None is bank
            self.player_balance_pay(player=player,
                                    receiver=None,
                                    amount=case.tax_price,
                                    reason="tax_square")

        elif isinstance(case, FreeParkingSquare):

            # change all debts targeting the bank (None) to this player
            self.board.retarget_player_bank_debts(new_target=player)

            # update balance
            self.player_balance_receive(player=player,
                                        amount=self.board.board_money,
                                        reason="parking_square")

            # set board money to 0
            self.board.board_money = 0
        elif isinstance(case, OwnableSquare):
            # Pay rent :o
            if not case.has_owner() or case.mortgaged:
                return
            # Dont pay rent to yourself
            if case.owner == player:
                return

            # Calculate rent
            rent = self.board.get_rent(case, player.current_dices)

            self.player_balance_pay(player=player,
                                    receiver=case.owner,
                                    amount=rent,
                                    reason="rent_pay",
                                    receiver_reason="rent_receive")
        elif isinstance(case, ChanceSquare) and not backward:
            card = self.board.draw_random_chance_card()

            if card is None:
                # TODO: Send exception packet
                pass
            else:
                self.broadcast_packet(RoundRandomCard(
                    player_token=player.get_id(),
                    card_id=card.id_,
                    is_community=False
                ))
                self.process_card_actions(player=player, card=card)

        elif isinstance(case, CommunitySquare) and not backward:
            card = self.board.draw_random_community_card()

            if card is None:
                # TODO: Send exception packet
                pass
            else:
                self.broadcast_packet(RoundRandomCard(
                    player_token=player.get_id(),
                    card_id=card.id_,
                    is_community=True
                ))
                self.process_card_actions(player=player, card=card)

    def disconnect_player(self, player: Player, reason: str = ""):
        # TODO: Maybe handle bot should make actions here? buy etc
        # Send to all players a disconnecting player packet
        self.broadcast_packet(PlayerDisconnect(
            reason=reason,
            player_token=player.get_id()
        ))

        player.disconnect()

        async_to_sync(self.channel_layer.group_discard)(
            self.uid, player.channel_name
        )

        # Waiting players => ignore players_count == 0
        if self.state is GameState.WAITING_PLAYERS:
            return

        if self.board.get_online_real_players_count() == 0:
            print("Player disconnected, stopping game.")
            self.state = GameState.STOP_THREAD
            return

        if self.board.get_online_players_count() == 1:
            # TODO: Player win?
            return

        # If player is actual player, end tour
        if self.board.get_current_player() == player:
            if self.board.current_auction is None:
                self.proceed_action_tour_end()
        return

    def process_card_actions(self, player: Player, card: Card):
        """
        All actions handled here

        :param player: Player who drawn card
        :param card: Card to handle action
        """

        print("process_card_actions(%s) => card: %d (%s) available? %r"
              % (player.get_name(),
                 card.id_, card.action_type.name, card.available))

        if not card.available:  # WTF?
            return

        if card.action_type is CardActionType.LEAVE_JAIL:
            if isinstance(card, ChanceCard):
                player.jail_cards['chance'] = True
                card.available = False
                return

            if isinstance(card, CommunityCard):
                player.jail_cards['community'] = True
                card.available = False
                return

        # Receive new injected money
        if card.action_type is CardActionType.RECEIVE_BANK:
            self.player_balance_receive(player=player,
                                        amount=card.action_value,
                                        reason="card_receive_bank")
            return

        # Give to bank = give money to board
        if card.action_type is CardActionType.GIVE_BOARD:
            self.player_balance_pay(player=player,
                                    receiver=None,
                                    amount=card.action_value,
                                    reason="card_give_board")
            return

        if card.action_type is CardActionType.MOVE_BACKWARD:
            self.board.move_player(player=player,
                                   cases=-card.action_value)

            # Broadcast new player position
            self.broadcast_packet(PlayerMove(
                player_token=player.get_id(),
                destination=player.position,
                instant=True
            ))

            # No actions for passed go
            self.proceed_move_player_actions(player=player,
                                             backward=True)
            return

        if card.action_type is CardActionType.GOTO_POSITION:
            passed_go = card.action_value < player.position
            player.position = card.action_value

            self.broadcast_packet(PlayerMove(
                player_token=player.get_id(),
                destination=card.action_value,
                instant=True
            ))

            # Move player actions
            self.proceed_move_player_actions(player=player,
                                             passed_go=passed_go)
            return

        if card.action_type is CardActionType.GOTO_JAIL:
            player.enter_prison()
            player.position = self.board.prison_square_index

            self.broadcast_packet(PlayerEnterPrison(
                player_token=player.get_id(),
            ))
            return

        if card.action_type is CardActionType.GIVE_ALL:
            # Give money to all players
            for receiver in self.board.players:
                if receiver == player or receiver.bankrupt:
                    continue
                self.player_balance_pay(player=player,
                                        receiver=receiver,
                                        amount=card.action_value,
                                        reason="card_give_all_send",
                                        receiver_reason="card_give_all"
                                                        "_receive")
            return

        if card.action_type is CardActionType.RECEIVE_ALL:
            # Receive money from all players
            for sender in self.board.players:
                if sender == player or sender.bankrupt:
                    continue

                self.player_balance_pay(player=sender,
                                        receiver=player,
                                        amount=card.action_value,
                                        reason="card_receive_all_send",
                                        receiver_reason="card_receive_all"
                                                        "_receive")
            return

        if card.action_type is CardActionType.CLOSEST_STATION:
            closest_company = self.board.find_closest_station_index(player)

            # Not possible
            if closest_company == -1:
                return

            passed_go = closest_company < player.position
            player.position = closest_company

            self.broadcast_packet(PlayerMove(
                player_token=player.get_id(),
                destination=closest_company,
                instant=True
            ))

            # Move player actions
            self.proceed_move_player_actions(player=player,
                                             passed_go=passed_go)

            return

        if card.action_type is CardActionType.CLOSEST_COMPANY:
            closest_company = self.board.find_closest_company_index(player)

            # Not possible
            if closest_company == -1:
                return

            passed_go = closest_company < player.position
            player.position = closest_company

            self.broadcast_packet(PlayerMove(
                player_token=player.get_id(),
                destination=closest_company,
                instant=True
            ))

            # Move player actions
            self.proceed_move_player_actions(player=player,
                                             passed_go=passed_go)

            return

        if card.action_type is CardActionType.GIVE_BOARD_HOUSES:
            houses, hotels = self.board.get_player_buildings_count(player)
            total = houses * card.action_value + hotels * card.alt

            self.player_balance_pay(player=player,
                                    receiver=None,
                                    amount=total,
                                    reason="card_give_board_houses_send",
                                    receiver_reason="card_give_board_houses"
                                                    "_receive")

    def process_exchange_transfers(self):
        """
        Process exchange transfers:
        - money
        - properties
        - cards
        TODO: Maybe split in more than 1 function
        """
        exchange = self.board.current_exchange

        if exchange is None:
            return

        # exchange money
        sender = None
        receiver = None

        if exchange.player_money > exchange.selected_player_money:
            money = exchange.player_money - exchange.selected_player_money
            sender = exchange.player
            receiver = exchange.selected_player
        elif exchange.player_money < exchange.selected_player_money:
            money = exchange.selected_player_money - exchange.player_money
            sender = exchange.selected_player
            receiver = exchange.player
        else:
            # if money == 0, do nothing
            money = 0

        if money != 0 and sender.has_enough_money(money):
            self.player_balance_pay(
                player=sender,
                receiver=receiver,
                amount=money,
                reason="exchange_money_pay",
                receiver_reason="exchange_money_receive"
            )

        # player to player_selected
        community_card = self.board.community_deck[
            self.board.community_card_indexes['leave_jail']]
        chance_card = self.board.chance_deck[
            self.board.chance_card_indexes['leave_jail']]

        for card in exchange.player_cards:
            if card != community_card and card != chance_card:
                continue
            community = False
            if isinstance(card, CommunityCard):
                # Process community card
                if not exchange.player.jail_cards['community']:
                    continue

                exchange.player.jail_cards['community'] = False
                exchange.selected_player.jail_cards['community'] = True
                community = True
            elif isinstance(card, ChanceCard):
                # Process chance card

                if not exchange.player.jail_cards['chance']:
                    continue

                exchange.player.jail_cards['chance'] = False
                exchange.selected_player.jail_cards['chance'] = True
            else:  # Not possible lol
                continue

            self.broadcast_packet(ActionExchangeTransfer(
                player_token=exchange.player.get_id(),
                player_to=exchange.selected_player.get_id(),
                transfer_type=ExchangeTransferType.CARD,
                value=community_card.id_ if community else chance_card.id_
            ))

        for square in exchange.player_squares:
            if square.mortgaged or square.owner != exchange.player:
                continue

            # redundant checks for security
            if isinstance(square, PropertySquare):
                if square.nb_house > 0:
                    continue

            square.owner = exchange.selected_player

            self.broadcast_packet(ActionExchangeTransfer(
                player_token=exchange.player.get_id(),
                player_to=exchange.selected_player.get_id(),
                transfer_type=ExchangeTransferType.PROPERTY,
                value=square.id_
            ))

        # player_selected to player

        for card in exchange.selected_player_cards:
            if card != community_card and card != chance_card:
                continue
            community = False
            if isinstance(card, CommunityCard):
                # Process community card
                if not exchange.selected_player.jail_cards['community']:
                    continue

                exchange.selected_player.jail_cards['community'] = False
                exchange.player.jail_cards['community'] = True
                community = True
            elif isinstance(card, ChanceCard):
                # Process chance card

                if not exchange.selected_player.jail_cards['chance']:
                    continue

                exchange.selected_player.jail_cards['chance'] = False
                exchange.player.jail_cards['chance'] = True
            else:  # Not possible lol
                continue

            self.broadcast_packet(ActionExchangeTransfer(
                player_token=exchange.selected_player.get_id(),
                player_to=exchange.player.get_id(),
                transfer_type=ExchangeTransferType.CARD,
                value=community_card.id_ if community else chance_card.id_
            ))

        for square in exchange.selected_player_squares:
            if square.mortgaged or square.owner != exchange.selected_player:
                continue

            # redundant checks for security
            if isinstance(square, PropertySquare):
                if square.nb_house > 0:
                    continue

            square.owner = exchange.player

            self.broadcast_packet(ActionExchangeTransfer(
                player_token=exchange.selected_player.get_id(),
                player_to=exchange.player.get_id(),
                transfer_type=ExchangeTransferType.PROPERTY,
                value=square.id_
            ))

    def player_balance_pay(self, player: Player, receiver: Optional[Player],
                           amount: int,
                           reason: str,
                           receiver_reason: str = "") -> int:
        """
        Players pays some amount to receiver.
        Checks if there's any debts.
        :param player: Sender
        :param receiver: Receiver
        :param amount: Amount to send
        :param reason: Sender's reason of balance update
        :param receiver_reason: Receiver's reason of balance update
        :return: Amount sent to receiver without debts
        """

        # Player has enough money, no debt must be created
        if player.money >= amount:
            print("player_balance_pay(%s) to (%s) player.money (%d) >= amount"
                  " (%d)"
                  % (player.get_name(),
                     receiver.get_name() if receiver is not None else "Bank",
                     player.money, amount))
            self.player_balance_update(player=player,
                                       new_balance=player.money - amount,
                                       reason=reason)

            if receiver is None:
                self.board.board_money += amount
            else:
                self.player_balance_receive(player=receiver,
                                            amount=amount,
                                            reason=receiver_reason)
            return amount

        # Player has not enough money (debts are added)
        money = player.money
        temp_amount = 0

        if receiver is not None and receiver.has_debts():
            print("player_balance_pay(%s) to (%s) receiver.has_debts()"
                  % (player.get_name(),
                     receiver.get_name() if receiver is not None else "Bank"))
            for debt in receiver.debts.copy():
                if amount == 0:
                    break

                # creditor should be the player who pays
                if debt.creditor != player:
                    continue

                if debt.amount == 0:
                    receiver.debts.remove(debt)
                    continue

                if debt.amount > amount:
                    debt.amount -= amount
                    temp_amount += amount
                    amount = 0
                    break
                else:
                    amount -= debt.amount
                    temp_amount += amount
                    receiver.debts.remove(debt)

        if temp_amount != 0:
            # broadcast information packet
            self.broadcast_packet(PlayerPayDebt(
                player_from=receiver.get_id(),
                player_to=player.get_id(),
                amount=temp_amount,
                reason="debt_rebalancing"
            ))

        if amount == 0:
            return 0

        debt_amount = amount - money

        player.add_debt(creditor=receiver,
                        amount=debt_amount,
                        reason=receiver_reason)

        # send packets
        self.player_balance_update(player=player,
                                   new_balance=0,
                                   reason=reason)

        if money == 0:
            return 0

        if receiver is None:
            self.board.board_money += money
        else:
            self.player_balance_receive(player=receiver,
                                        amount=money,
                                        reason=receiver_reason)
        return money

    def player_balance_receive(self, player: Player, amount: int,
                               reason: str):
        """
        Player receive's balance. Checking for debts.
        :param player: Receiver
        :param amount: Amount to receive
        :param reason: Reason of receive
        """
        # if amount is 0, no processing is required
        if amount == 0:
            return

        # Check if player has some debts.
        if player.has_debts():
            updates = []

            for debt in player.debts.copy():
                if amount == 0:
                    break

                if debt.amount == 0:
                    player.debts.remove(debt)
                    continue

                if debt.amount > amount:
                    debt.amount -= amount
                    sent = amount
                    amount = 0
                else:
                    amount -= debt.amount
                    sent = debt.amount
                    debt.amount = 0
                    # debt was settled
                    player.debts.remove(debt)

                # first update all debts, then send money.
                updates.append((debt.creditor, sent))

                # broadcast information packet
                self.broadcast_packet(PlayerPayDebt(
                    player_from=player.get_id(),
                    player_to=debt.creditor.get_id()
                    if debt.creditor is not None else "",  # "" == Bank
                    amount=sent,
                    reason=debt.reason
                ))

            # Send money after removing debts.
            for (creditor, send_amount) in updates:

                # Bank does not receive any money.
                if creditor is None:
                    # update board money when bank is creditor
                    self.board.board_money += send_amount
                    continue

                # Recursive method.
                self.player_balance_receive(
                    player=creditor,
                    amount=send_amount,
                    reason="debt_payment"
                )

        if amount == 0:
            # if amount is 0, then all debts that the player, were bigger than
            # the amount that the player should have received.
            return

        # send the remaining money to the player.
        self.player_balance_update(player=player,
                                   new_balance=player.money + amount,
                                   reason=reason)

    def player_balance_update(self, player: Player, new_balance: int,
                              reason: str):
        """
        Update player's balance to new_balance and broadcast
         PlayerUpdateBalance to all players.

        :param player: Player
        :param new_balance: Player's balance set to this value
        :param reason: Balance update reason
        """
        old_balance = player.money
        player.money = new_balance

        if new_balance == 0:
            new_balance = -player.get_total_debts()

        self.broadcast_packet(PlayerUpdateBalance(
            player_token=player.get_id(),
            old_balance=old_balance,
            new_balance=new_balance,
            reason=reason
        ))

    def broadcast_packet(self, packet: Packet):
        async_to_sync(self.channel_layer.group_send)(
            self.uid, {"type": "send.packet", "packet": packet.serialize()}
        )

    def send_packet_to_group(self, packet: Packet, group_name: str):
        """
        sends packet to lobby group.
        lobby group : all players that are connected to a game in lobby mode
        :param group_name: Name of the channels group
        :param packet: packet to be sent
        """
        print("send_packet_to_group(%s, %s)" % (packet.name, group_name))
        async_to_sync(self.channel_layer.group_send)(
            group_name, {
                'type': 'send.lobby.packet',
                'packet': packet.serialize()
            })

    def send_packet_to_player(self, player: Player, packet: Packet):
        if player.bot is True:
            return
        self.send_packet(player.channel_name, packet)

    def send_lobby_packet(self, channel_name: str, packet: Packet):
        """
        Send packet to lobby channel layer
        :param channel_name: Channel to send packet to
        :param packet: Packet to send
        """
        if channel_name is None:
            return

        async_to_sync(self.channel_layer.send)(
            channel_name, {
                'type': 'lobby.callback',
                'packet': packet.serialize()
            })

    def send_packet(self, channel_name: str, packet: Packet):
        """
        Send packet to channel layer

        :param channel_name: Channel to send packet to
        :param packet: Packet to send
        """
        if channel_name is None:
            return

        function_name = 'lobby.callback' if self.state == GameState.LOBBY \
            else 'player.callback'

        async_to_sync(self.channel_layer.send)(
            channel_name, {
                'type': function_name,
                'packet': packet.serialize()
            })
