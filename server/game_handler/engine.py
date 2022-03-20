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
from django.conf import settings
import pause

from server.game_handler.data import Board, Player, Card
from server.game_handler.data.cards import ChanceCard, CardActionType, \
    CommunityCard
from server.game_handler.data.exceptions import \
    GameNotExistsException
from server.game_handler.data.packets import PlayerPacket, Packet, \
    InternalCheckPlayerValidity, GameStart, ExceptionPacket, AppletReady, \
    GameStartDice, GameStartDiceThrow, GameStartDiceResults, RoundStart, \
    PingPacket, PlayerDisconnect, InternalPlayerDisconnect, RoundDiceChoice, \
    RoundDiceChoiceResult, RoundDiceResults, PlayerExitPrison, \
    PlayerEnterPrison, PlayerMove, PlayerUpdateBalance, RoundRandomCard, \
    PlayerPayDebt
from server.game_handler.data.player import PlayerDebt
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
    CONFIG: {}
    # reference to games dict
    games: {}

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
            if isinstance(packet, GameStart):
                # set state to waiting players
                # the server will wait AppletReady packets.
                self.state = GameState.WAITING_PLAYERS
                self.set_timeout(
                    seconds=self.CONFIG.get('WAITING_PLAYERS_TIMEOUT'))
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

        # send coherent informations to all players
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

                self.player_balance_update(player, player.money -
                                           self.CONFIG.get('JAIL_LEAVE_PRICE'),
                                           "jail_leave_pay")

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

        # Move player and check if he reached start
        passed_go = self.board.move_player_with_dices(player)

        # Broadcast new player position
        self.broadcast_packet(PlayerMove(
            player_token=player.get_id(),
            destination=player.position
        ))

        case = self.board.squares[player.position]

        # Player has reached start
        if passed_go:
            self.player_balance_update(player, player.money +
                                       self.CONFIG.get('MONEY_GO'),
                                       "pass_go")

            # Player case == 0 & double money option is enabled
            if isinstance(case, GoSquare) and \
                    self.board.option_go_case_double_money:
                self.player_balance_update(player, player.money +
                                           self.CONFIG.get('MONEY_GO'),
                                           "pass_go_exact")

        # Check destination case
        if isinstance(case, GoToJailSquare):
            player.enter_prison()
            player.position = self.board.prison_square_index
            self.broadcast_packet(PlayerEnterPrison(
                player_token=player.get_id()
            ))
        elif isinstance(case, TaxSquare):
            self.player_balance_update(player, player.money - case.tax_price,
                                       "tax_square")
        elif isinstance(case, FreeParkingSquare):
            self.player_balance_update(player, player.money + self.board
                                       .board_money, "parking_square")
            self.board.board_money = 0
        elif isinstance(case, OwnableSquare):
            if case.has_owner():
                # Pay rent :o
                rent = case.get_rent()
                self.player_balance_update(player, player.money - rent,
                                           "rent_pay")
                self.player_balance_update(case.owner, case.owner.money
                                           + rent, "rent_receive")
        elif isinstance(case, ChanceSquare):
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
                self.process_card_action(player=player, card=card)

        elif isinstance(case, CommunitySquare):
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
                self.process_card_action(player=player, card=card)

    def disconnect_player(self, player: Player, reason: str = ""):
        player.disconnect()
        # TODO: Maybe handle bot should make actions here? buy etc

        # Send to all players a disconnecting player packet
        self.broadcast_packet(PlayerDisconnect(
            reason=reason,
            player_token=player.get_id()
        ))

    def process_card_action(self, player: Player, card: Card):
        """
        All actions handled here # TODO:

        :param player: Player who drawn card
        :param card: Card to handle action
        """

        if not card.available:  # WTF?
            return

        if isinstance(card, ChanceCard):
            if card.action_type is CardActionType.LEAVE_JAIL:
                player.jail_cards['chance'] = True
                card.available = False

        if isinstance(card, CommunityCard):
            if card.action_type is CardActionType.LEAVE_JAIL:
                player.jail_cards['community'] = True
                card.available = False

    def player_balance_pay(self, player: Player, receiver: Optional[Player],
                           amount: int,
                           reason: str):

        # Player has enough money, no debt must be created
        if player.money >= amount:
            self.player_balance_update(player=player,
                                       new_balance=player.money - amount,
                                       reason=reason)

            if receiver is not None:
                self.player_balance_receive(player=receiver,
                                            amount=amount,
                                            reason=reason)
            return

        # Player has not enough money (debts are added)
        debt_amount = amount - player.money

        player.debts.append(PlayerDebt(
            creditor=receiver,
            amount=debt_amount
        ))

        # send packets
        self.player_balance_update(player=player,
                                   new_balance=0,
                                   reason=reason)

        if receiver is not None:
            self.player_balance_receive(player=receiver,
                                        amount=amount,
                                        reason=reason)

    def player_balance_receive(self, player: Player, amount: int,
                               reason: str):

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
                    debt.amount = debt.amount - amount
                    sent = amount
                    amount = 0
                else:
                    amount = amount - debt.amount
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
                    amount=sent
                ))

            # Send money after removing debts.
            for (creditor, amount) in updates:

                # Bank does not receive any money.
                if creditor is None:
                    continue

                # Recursive method.
                self.player_balance_receive(
                    player=creditor,
                    amount=amount,
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

        self.broadcast_packet(PlayerUpdateBalance(
            player_token=player.get_id(),
            old_balance=old_balance,
            new_balance=player.money,
            reason=reason
        ))

    def broadcast_packet(self, packet: Packet):
        async_to_sync(self.channel_layer.group_send)(
            self.uid, {"type": "game_update", "packet": packet.serialize()}
        )

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


class Engine:
    games: dict[str, Game]

    def __init__(self, **kwargs):
        self.games = {}

    def add_game(self, game: Game):
        """
        Add a game to active games list

        :param game: Game to add
        """
        if game.uid in self.games:
            return

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
