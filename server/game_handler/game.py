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

from server.game_handler.data import Board, Player, Card
from server.game_handler.data.cards import ChanceCard, CardActionType, \
    CommunityCard
from server.game_handler.data.packets import PlayerPacket, Packet, \
    InternalCheckPlayerValidity, GameStart, ExceptionPacket, AppletReady, \
    GameStartDice, GameStartDiceThrow, GameStartDiceResults, RoundStart, \
    PingPacket, PlayerDisconnect, InternalPlayerDisconnect, RoundDiceChoice, \
    RoundDiceChoiceResult, RoundDiceResults, PlayerExitPrison, \
    GetInRoom, LaunchGame, AppletPrepare, GetInRoomSuccess, GetOutRoom, \
    GetOutRoomSuccess, BroadcastUpdateRoom, PlayerEnterPrison, PlayerMove, \
    PlayerUpdateBalance, RoundRandomCard, PlayerPayDebt, \
    AddBot, UpdateReason, BroadcastUpdateLobby, StatusRoom, NewHost

from server.game_handler.models import User
from django.conf import settings
from server.game_handler.data.squares import GoSquare, TaxSquare, \
    FreeParkingSquare, OwnableSquare, ChanceSquare, CommunitySquare, \
    GoToJailSquare


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

    def __init__(self, uid: str = str(uuid.uuid4()), **kwargs):
        super(Game, self).__init__(daemon=True, name="Game_%s" % uid, **kwargs)
        self.channel_layer = get_channel_layer()
        self.uid = uid
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

        if self.state > GameState.LOBBY:
            # Heartbeat only in "game"
            if isinstance(packet, PingPacket):
                player = self.board.get_player(packet.player_token)
                if player is None:
                    return

                player.ping = True
                return

            if isinstance(packet, InternalPlayerDisconnect):
                # TODO: HANDLE CLIENT SIDE DISCONNECT
                pass

        # check player validity
        if isinstance(packet, InternalCheckPlayerValidity):
            # Only accept connection, if player exists and game is started
            valid = self.board.player_exists(
                packet.player_token) and self.state > GameState.LOBBY
            self.send_packet(
                channel_name=queue_packet.channel_name,
                packet=InternalCheckPlayerValidity(valid=valid))
            if not valid:
                return

        if self.state is GameState.LOBBY:
            if isinstance(packet, GetInRoom):

                try:  # get user from database
                    user = User.objects.get(id=packet.player_token)
                except User.DoesNotExist:
                    return

                if packet.password != "":
                    if packet.password != self.board.option_password:
                        self.send_packet(channel_name=packet.player_token,
                                         packet=ExceptionPacket(code=4201))
                        return
                # if game is full
                if len(self.board.players) == self.board.players_nb:
                    self.send_packet(channel_name=packet.player_token,
                                     packet=ExceptionPacket(code=4202))
                    return

                # all the checks are fine, add the player to the game
                self.board.add_player(
                    Player(user=user, channel_name=self.channel_layer,
                           bot=False))

                # player leaves lobby group
                async_to_sync(
                    self.channel_layer.group_discard)("lobby",
                                                      packet.player_token)
                # add player to this specific game group
                async_to_sync(
                    self.channel_layer.group_add)(self.uid,
                                                  packet.player_token)

                nb_players = len(self.board.players)

                # send success of getting in room
                piece = self.board.assign_piece(packet.player_token)
                self.send_packet(channel_name=packet.player_token,
                                 packet=GetInRoomSuccess(piece))

                # sending status of room
                player_uid = []
                for player in self.board.players:
                    player_uid.append(player.get_id())
                status = StatusRoom(game_token=self.uid,
                                    name=self.public_name,
                                    nb_players=nb_players,
                                    max_nb_players=self.board.players_nb,
                                    players=player_uid,
                                    option_auction=self.
                                    board.option_auction_enabled,
                                    option_double_on_start=self.
                                    board.option_go_case_double_money,
                                    option_maxnb_rounds=self.
                                    board.option_maxnb_rounds,
                                    option_first_round_buy=self.
                                    board.option_first_round_buy,
                                    option_max_time=self.
                                    board.option_max_time,
                                    starting_balance=self.
                                    board.starting_balance)
                self.send_packet(packet.player_token, status)

                # broadcast to lobby group
                reason = UpdateReason.NEW_PLAYER.value
                # sent to lobby and to game group
                update = BroadcastUpdateRoom(game_token=self.uid,
                                             nb_players=nb_players,
                                             reason=reason,
                                             player=packet.player_token)
                # sending to the people in the game
                self.send_packet_to_group(update, self.uid)
                update = BroadcastUpdateLobby(game_token=self.uid,
                                              nb_players=nb_players,
                                              reason=reason,
                                              nb_player_max=self.
                                              board.players_nb)
                # sending to the lobby people
                self.send_packet_to_group(update, "lobby")
                return

            elif isinstance(packet, GetOutRoom):
                # check if player is part of the current room

                # if player is the host of the game
                # someone else randomly takes over
                # -->first non-host player connected
                if packet.player_token == self.host_player:
                    # host is alone
                    if len(self.board.players) == 1:
                        # TODO: delete game
                        pass
                    for i in range(len(self.board.players)):
                        # reassigning host
                        if self.board.players[i] != self.host_player:
                            self.host_player = self.board.players[i]
                            self.send_packet_to_player(self.host_player,
                                                       NewHost())
                            break

                # player leaves game group
                async_to_sync(
                    self.channel_layer.group_discard)(self.uid,
                                                      packet.player_token)
                # add player to the lobby group
                async_to_sync(
                    self.channel_layer.group_add)(self.uid,
                                                  packet.player_token)

                # if checks passed, kick out player
                self.board.remove_player(
                    self.board.get_player(packet.player_token))

                self.send_packet(packet.player_token, GetOutRoomSuccess())

                nb_players = len(self.board.players)
                # broadcast updated room status
                reason = UpdateReason.PLAYER_LEFT.value
                # this should be sent to lobby and to game group
                update = BroadcastUpdateRoom(game_token=self.uid,
                                             nb_players=nb_players,
                                             reason=reason,
                                             player=packet.player_token)
                self.send_packet_to_group(update, self.uid)
                update = BroadcastUpdateLobby(game_token=self.uid,
                                              nb_players=nb_players,
                                              reason=reason,
                                              nb_player_max=self.
                                              board.players_nb)
                self.send_packet_to_group(update, "lobby")
                return

            elif isinstance(packet, LaunchGame):
                # check if player_token is the token of the game host
                if packet.player_token != self.host_player:
                    return  # ignore the launch request

                self.broadcast_packet(packet=AppletPrepare())
                # putting the game in waiting mode (waiting for AppletReady
                # from all the players)
                self.state = GameState.WAITING_PLAYERS
                # setting timeout to wait for the players to send AppletReady
                self.set_timeout(
                    seconds=self.CONFIG.get('WAITING_PLAYERS_TIMEOUT'))
                # broadcasting update to players
                reason = UpdateReason.LAUNCHING_GAME.value
                nb_players = len(self.board.players)

                # this should be sent to lobby and to game group
                update = BroadcastUpdateRoom(game_token=self.uid,
                                             nb_players=nb_players,
                                             reason=reason,
                                             player=packet.player_token)
                self.send_packet_to_group(update, self.uid)
                update = BroadcastUpdateLobby(game_token=self.uid,
                                              nb_players=nb_players,
                                              reason=reason,
                                              nb_player_max=self.
                                              board.players_nb)
                self.send_packet_to_group(update, "lobby")
                return

            elif isinstance(packet, AddBot):
                # check if the host is the one sending the packet
                if packet.player_token != self.host_player:
                    self.send_packet(channel_name=packet.player_token,
                                     packet=ExceptionPacket(code=4205))
                    return

                # check if game is not full
                if len(self.board.players) == self.board.players_nb:
                    self.send_packet(channel_name=packet.player_token,
                                     packet=ExceptionPacket(code=4202))
                    return

                # add bot to the game
                p = Player(bot=True, bot_name=self.board.get_random_bot_name(),
                           bot_level=packet.bot_difficulty)
                self.board.add_player(p)

                # broadcast updated room status
                nb_players = len(self.board.players)
                reason = UpdateReason.NEW_BOT.value

                # this should be sent to lobby and to game group
                update = BroadcastUpdateRoom(game_token=self.uid,
                                             nb_players=nb_players,
                                             reason=reason,
                                             player=packet.player_token)
                self.send_packet_to_group(update, self.uid)
                update = BroadcastUpdateLobby(game_token=self.uid,
                                              nb_players=nb_players,
                                              reason=reason,
                                              nb_player_max=self.
                                              board.players_nb)
                self.send_packet_to_group(update, "lobby")
                return

        else:
            # If state is not lobby
            # Check for packet validity
            if isinstance(packet, PlayerPacket):
                if not self.board.player_exists(packet.player_token):
                    return self.send_packet(
                        channel_name=queue_packet.channel_name,
                        # 4100 => invalid player
                        packet=ExceptionPacket(code=4100))

        if self.state is GameState.WAITING_PLAYERS:
            # WebGL app is ready to play
            if isinstance(packet, AppletReady):
                # Player could not be null -> we are checking before, if this
                # player exists.
                player = self.board.get_player(packet.player_token)

                # Set player to connected (bot disabled)
                player.connect()

                # init ping heartbeat
                player.ping = True
                player.ping_timeout = datetime.now() + timedelta(
                    seconds=self.CONFIG.get('PING_HEARTBEAT_TIMEOUT'))
                return

        if self.state is GameState.START_DICE:

            if isinstance(packet, GameStartDiceThrow):
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
            if isinstance(packet, RoundDiceChoice):
                player = self.board.get_player(packet.player_token)

                # Ignore packets sent by players other than current_player
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

    def process_logic(self):
        # TODO: Check #34 in comments

        # Check pings
        if self.state.value > GameState.LOBBY.value:
            self.proceed_heartbeat()

        # State is waiting that players connecting and send AppletReady
        if self.state is GameState.WAITING_PLAYERS:
            if self.board.get_online_players_count() == self.board.players_nb:
                # We can start the game
                self.start_game()
            elif self.timeout_expired():  # Check timeout
                if self.board.get_online_real_players_count() == 0:
                    # After timeout, if no one is connected
                    # Stop game
                    self.state = GameState.STOP_THREAD
                    return
                else:
                    self.start_game()

        if self.timeout_expired():
            if self.state is GameState.STARTING:
                # x Seconds timeout before game start
                self.start_begin_dice()

            if self.state is GameState.START_DICE:
                self.check_start_dice()

            if self.state is GameState.START_DICE_REROLL:
                self.start_begin_dice()

            if self.state is GameState.FIRST_ROUND_START_WAIT:
                self.start_round(first=True)

            if self.state is GameState.ROUND_START_WAIT:
                self.start_round()

            # If player has not sent his choice to the server,
            # process to timeout choice
            if self.state is GameState.ROUND_DICE_CHOICE_WAIT:
                player = self.board.get_current_player()
                choice = RoundDiceChoiceResult.ROLL_DICES

                # Player has X jail_turns, force pay.
                if player.in_jail and player.jail_turns >= self.CONFIG.get(
                        'MAX_JAIL_TURNS'):
                    choice = RoundDiceChoiceResult.JAIL_PAY

                self.proceed_dice_choice(player=player, choice=choice)

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

    def start_game(self):
        """
        Set game in "game" mode, (game starting timeout)
        state.STARTING -> timeout_expired() -> start_begin_dice()
        """
        # Set bot names to all players
        self.board.set_bot_names()
        self.state = GameState.STARTING
        self.set_timeout(seconds=self.CONFIG.get('GAME_STARTING_TIMEOUT'))

        # send coherent information to all players
        players = []
        for player in self.board.get_online_players():
            players.append(player.get_coherent_infos())

        self.broadcast_packet(GameStart(players=players))

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
            is_winner = player.get_id() is highest.get_id()
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
        if not first:
            self.board.next_player()

        # Get current player
        current_player = self.board.get_current_player()
        current_player.roll_dices()

        # TODO : AI should randomly do some actions
        # Check if player is in prison -> random between :
        # -> buy if he can or trie to dice
        # maybe execute AI random timeouts.

        # broadcast packet to all players
        packet = RoundStart(current_player=current_player.get_id())
        self.broadcast_packet(packet)

        # set timeout for dice choice wait
        self.state = GameState.ROUND_DICE_CHOICE_WAIT
        self.set_timeout(seconds=self.CONFIG.get('ROUND_DICE_CHOICE_WAIT'))

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

            if choice == RoundDiceChoiceResult.JAIL_CARD_COMMUNITY and \
                    player.jail_cards['community']:
                # Exit prison & use card
                player.exit_prison()
                self.board.use_community_jail_card(player)

                self.broadcast_packet(PlayerExitPrison(
                    player_token=player.get_id()
                ))

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

            if player.dices_are_double():
                self.broadcast_packet(PlayerExitPrison(
                    player_token=player.get_id()
                ))
                player.exit_prison()
                return

            player.jail_turns += 1
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
        # Move player and check if he reached start
        passed_go = self.board.move_player_with_dices(player)

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
            self.board.board_money += case.tax_price
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
            if case.has_owner():
                # Pay rent :o
                self.player_balance_pay(player=player,
                                        receiver=case.owner,
                                        amount=case.get_rent(),
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
        player.disconnect()
        # TODO: Maybe handle bot should make actions here? buy etc

        # Send to all players a disconnecting player packet
        self.broadcast_packet(PlayerDisconnect(
            reason=reason,
            player_token=player.get_id()
        ))

    def process_card_actions(self, player: Player, card: Card):
        """
        All actions handled here # TODO:

        :param player: Player who drawn card
        :param card: Card to handle action
        """

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
            # No actions for passed go
            self.proceed_move_player_actions(player=player,
                                             backward=True)
            return

        if card.action_type is CardActionType.GOTO_POSITION:
            passed_go = card.action_value < player.position
            player.position = card.action_value
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
                if receiver == player:
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
                if sender == player:
                    continue

                self.player_balance_pay(player=sender,
                                        receiver=player,
                                        amount=card.action_value,
                                        reason="card_receive_all_send",
                                        receiver_reason="card_receive_all"
                                                        "_receive")

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
            self.uid, {"type": "game_update", "packet": packet.serialize()}
        )

    def send_packet_to_group(self, packet: Packet, group_name: str):
        """
        sends packet to lobby group.
        lobby group : all players that are connected to a game in lobby mode
        :param packet: packet to be sent
        """
        async_to_sync(self.channel_layer.send)(
            group_name, {
                'type': 'send.lobby.packet',
                'packet': packet.serialize()
            })

    def send_packet_to_player(self, player: Player, packet: Packet):
        if player.bot is True:
            return
        self.send_packet(player.channel_name, packet)

    def send_packet(self, channel_name: str, packet: Packet):
        """
        Send packet to channel layer

        :param channel_name: Channel to send packet to
        :param packet: Packet to send
        """
        if channel_name is None:
            return

        async_to_sync(self.channel_layer.send)(
            channel_name, {
                'type': 'player.callback',
                'packet': packet.serialize()
            })
