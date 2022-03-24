from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import uuid
from enum import Enum
from threading import Thread
from queue import Queue

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
import pause

from server.game_handler.data import Board, Player
from server.game_handler.data.exceptions import \
    GameNotExistsException
from server.game_handler.data.packets import PlayerPacket, Packet, \
    InternalCheckPlayerValidity, GameStart, ExceptionPacket, AppletReady, \
    GameStartDice, GameStartDiceThrow, GameStartDiceResults, RoundStart, \
    PingPacket, PlayerDisconnect, InternalPlayerDisconnect, RoundDiceChoice, \
    RoundDiceChoiceResult, RoundDiceResults, PlayerExitPrison, \
    PlayerEnterPrison, PlayerMove, PlayerUpdateBalance, \
    GetInRoom, LaunchGame, AppletPrepare, GetInRoomSuccess, GetOutRoom, \
    GetOutRoomSuccess, CreateGame, CreateGameSuccess, BroadcastUpdatedRoom, \
    AddBot
from server.game_handler.data.squares import GoSquare
from server.game_handler.models import User

"""
States:
-> Démarrage -> démarrage timer remplacement joueur par un bot.
-> Attente de nb_joueurs AppletReady
-> Lorsque ce nombre est atteint => GameStart
-> On attends 2-3 secondes
-> On envoie un paquet GameStartDice

"""


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
        self.packets_queue.join()

        # Store all packets in temp array
        # If packet processing is taking too much time,
        # The queue will be locked for a too long period
        packets = []

        while not self.packets_queue.empty():
            packets.append(self.packets_queue.get(block=False))

        # Unblock
        self.packets_queue.task_done()

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

                # get current number of players for update
                nb_players = len(self.board.players)
                # all the checks are fine, add the player to the game
                self.board.add_player(
                    Player(user=user, channel_name=self.channel_layer,
                           bot=False))
                # send success of getting in room
                self.send_packet(channel_name=packet.player_token,
                                 packet=GetInRoomSuccess())

                # broadcast to lobby group
                update = BroadcastUpdatedRoom(id_room=self.uid,
                                              old_nb_players=nb_players,
                                              new_nb_players=nb_players+1,
                                              state="LOBBY")
                self.send_packet_lobby(update)

            elif isinstance(packet, GetOutRoom):
                # check if player is part of the current room
                if not self.board.player_exists(packet.player_token):
                    self.send_packet(channel_name=packet.player_token,
                                     packet=ExceptionPacket(code=4203))
                    return

                # if player is the host of the game
                if packet.player_token != self.host_player:
                    self.send_packet(channel_name=packet.player_token,
                                     packet=ExceptionPacket(code=4204))
                    return

                # if checks passed, kick out player
                nb_players = len(self.board.players)
                self.board.remove_player(
                    self.board.get_player(packet.player_token))
                # maybe broadcast to let every player in the room know this
                # player is leaving : this might also be done with the
                # broadcast of the updated room status
                self.send_packet(packet.player_token, GetOutRoomSuccess())

                # broadcast updated room status
                update = BroadcastUpdatedRoom(id_room=self.uid,
                                              old_nb_players=nb_players,
                                              new_nb_players=nb_players-1,
                                              state="LOBBY")
                self.send_packet_lobby(update)

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
                nb_players = len(self.board.players)
                update = BroadcastUpdatedRoom(id_room=self.uid,
                                              old_nb_players=nb_players,
                                              new_nb_players=nb_players,
                                              state="WAITING_PLAYERS")
                self.send_packet_lobby(update)

                # remove players from lobby group
                async_to_sync(
                    self.channel_layer.group_discard)("lobby",
                                                      packet.player_token)

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
                nb_players = len(self.board.players)
                self.board.add_player(Player(
                    bot_name=self.board.get_random_bot_name(),
                    bot_level=packet.bot_difficulty))

                # broadcast updated room status
                update = BroadcastUpdatedRoom(id_room=self.uid,
                                              old_nb_players=nb_players,
                                              new_nb_players=nb_players + 1,
                                              state="LOBBY")
                self.send_packet_lobby(update)

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

                # broadcast or send to all players? TODO:
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

                if packet.choice.value < 0 or packet.choice.value > 2:
                    return

                if packet.choice == RoundDiceChoiceResult.ROLL_DICES:
                    # TODO: add this to a function
                    # Ignore this packet, cant roll dices if player in jail
                    # and player.jail_turns >= (3)
                    if player.in_jail and player.jail_turns >= self.CONFIG.get(
                            'MAX_JAIL_TURNS'):
                        return

                    player.roll_dices()

                    # Broadcast roll_dices results
                    self.broadcast_packet(RoundDiceResults(
                        player_token=player.get_id(),
                        result=packet.choice,
                        dice1=player.current_dices[0],
                        dice2=player.current_dices[1]
                    ))

                    self.state = GameState.ACTION_START_WAIT
                    self.set_timeout(
                        seconds=self.CONFIG.get('ACTION_START_WAIT'))

                    # Check if player is in jail
                    if player.in_jail:
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

                        if player.doubles >= self.CONFIG.get(
                                'MAX_DOUBLES_JAIL'):
                            # send player to jail :D
                            player.enter_prison()
                            self.broadcast_packet(PlayerEnterPrison(
                                player_token=player.get_id()
                            ))
                            return
                    else:
                        player.doubles = 0

                    # Move player and check if he reached start
                    reached_start = self.board.move_player_with_dices(player)

                    # Broadcast new player position
                    self.broadcast_packet(PlayerMove(
                        player_token=player.get_id(),
                        destination=player.position
                    ))

                    case = self.board.squares[player.position]

                    # Player has reached start
                    if reached_start:
                        old_balance = player.score
                        player.score += self.CONFIG.get('MONEY_GO')

                        self.broadcast_packet(PlayerUpdateBalance(
                            old_balance=old_balance,
                            new_balance=player.score,
                            player_token=player.get_id(),
                            reason="reach_start"
                        ))

                        # Player case == 0 & double money option is enabled
                        if isinstance(case, GoSquare) and \
                                self.board.option_go_case_double_money:
                            old_balance = player.score
                            player.score += self.CONFIG.get('MONEY_GO')

                            self.broadcast_packet(PlayerUpdateBalance(
                                old_balance=old_balance,
                                new_balance=player.score,
                                player_token=player.get_id(),
                                reason="reach_start_exact"
                            ))

                        # TODO: HANDLE ALL CASES HERE

                if packet.choice == RoundDiceChoiceResult.JAIL_CARD:
                    pass

                if packet.choice == RoundDiceChoiceResult.JAIL_PAY:
                    pass

    def process_logic(self):
        # TODO: Check #34 in comments

        # Check pings
        if self.state > GameState.LOBBY:
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
                pass

    def proceed_stop(self):
        # Delete game
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
        state.ROUND_DICE_CHOICE_WAIT -> timeout_expired() -> TODO:
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

    def disconnect_player(self, player: Player, reason: str = ""):
        player.disconnect()
        # TODO: Maybe handle bot should make actions here? buy etc

        # Send to all players a disconnecting player packet
        self.broadcast_packet(PlayerDisconnect(
            reason=reason,
            player_token=player.get_id()
        ))

    def broadcast_packet(self, packet: Packet):
        async_to_sync(self.channel_layer.group_send)(
            self.uid, {"type": "game_update", "packet": packet.serialize()}
        )

    def send_packet_lobby(self, packet: Packet):
        """
        sends packet to lobby group.
        lobby group : all players that are connected to a game in lobby mode
        :param packet: packet to be sent
        """
        async_to_sync(self.channel_layer.send)(
            "lobby", {
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


class Engine:
    games: dict[str, Game]

    def __init__(self, **kwargs):
        self.games = {}

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

    def create_game(self, packet):

        if not isinstance(packet, CreateGame):
            return

        # if player is already in another game
        if self.player_exists(packet.player_token):
            return  # or maybe send error

        # adding a new game
        new_game = Game()
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
        self.games[id_new_game].board.starting_balance = \
            packet.starting_balance
        # sending CreateGameSuccess to host
        self.send_packet(game_uid=id_new_game,
                         packet=CreateGameSuccess(packet.player_token),
                         channel_name=packet.player_token)
        # sending updated room status
        self.games[id_new_game].send_packet_lobby(BroadcastUpdatedRoom(
            id_room=id_new_game, old_nb_players=0, new_nb_players=1,
            state="LOBBY"))
