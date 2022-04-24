import json
from unittest import TestCase

from server.game_handler.data.packets import PacketUtils, ActionBuyHouse, \
    ExceptionPacket, GameStartDiceResults, PlayerPacket, \
    InternalCheckPlayerValidity, InternalPlayerDisconnect, PlayerValid, \
    PingPacket, AppletPrepare, AppletReady, GameStart, PlayerDisconnect, \
    PlayerReconnect, GameStartDice, GameStartDiceThrow, RoundStart, \
    RoundDiceChoice, RoundDiceResults, PlayerMove, RoundRandomCard, \
    PlayerUpdateBalance, PlayerEnterPrison, PlayerExitPrison


class TestPacket(TestCase):

    def setUp(self):
        self.json_str = '{"code": 4000, "name": "Exception"}'
        self.args_json_str = '{"name": "ActionBuyHouse", "player_token": ' \
                             '"test", "property_id": 1}'
        self.game_dice_json_str = '{"dice_result": [{"dice1": 2, "dice2": ' \
                                  '3, "player_token": ' \
                                  '"283e1f5e-3411-44c5-9bc5-037358c47100", ' \
                                  '"win": true}, {"dice1": 2, "dice2": 2, ' \
                                  '"player_token": ' \
                                  '"23b3a6c7-6990-44b1-b466-8f8c3da5ec7d", ' \
                                  '"win": false}], "name": ' \
                                  '"GameStartDiceResults"}'

        self.json_PlayerPacket = \
            '{"name": "PlayerPacket", ' \
            '"player_token": "23b3a6c7-6990-44b1-b466-8f8c3da5ec7d"}'
        self.json_InternalCheckPlayerValidity = \
            '{"name": "InternalCheckPlayerValidity", "player_token": ' \
            '"23b3a6c7-6990-44b1-b466-8f8c3da5ec7d", ' \
            '"valid": false}'
        self.json_InternalPlayerDisconnect = \
            '{"name": "InternalPlayerDisconnect", "player_token": ' \
            '"23b3a6c7-6990-44b1-b466-8f8c3da5ec7d", ' \
            '"reason": ""}'
        self.json_PlayerValid = '{"name": "PlayerValid"}'
        self.json_Exception = '{"code": 4100, "name": "Exception"}'
        self.json_Ping = \
            '{"name": "Ping", ' \
            '"player_token": "23b3a6c7-6990-44b1-b466-8f8c3da5ec7d"}'
        self.json_AppletPrepare = '{"name": "AppletPrepare"}'
        self.json_AppletReady = \
            '{"name": "AppletReady", ' \
            '"player_token": "23b3a6c7-6990-44b1-b466-8f8c3da5ec7d"}'
        self.json_GameStart = '{"game_name": "Test", "name": "GameStart", ' \
                              '"options": {}, "players": []}'
        self.json_PlayerDisconnect = \
            '{"name": "PlayerDisconnect", ' \
            '"player_token": "23b3a6c7-6990-44b1-b466-8f8c3da5ec7d", ' \
            '"reason": ""}'
        self.json_PlayerReconnect = \
            '{"name": "PlayerReconnect", ' \
            '"player_token": "23b3a6c7-6990-44b1-b466-8f8c3da5ec7d"}'
        self.json_GameStartDice = '{"name": "GameStartDice"}'
        self.json_GameStartDiceThrow = \
            '{"name": "GameStartDiceThrow", ' \
            '"player_token": "23b3a6c7-6990-44b1-b466-8f8c3da5ec7d"}'
        self.json_RoundStart = \
            '{"current_player": "23b3a6c7-6990-44b1-b466-8f8c3da5ec7d", ' \
            '"name": "RoundStart"}'
        self.json_RoundDiceChoice = \
            '{"choice": 0, "name": "RoundDiceChoice", ' \
            '"player_token": "23b3a6c7-6990-44b1-b466-8f8c3da5ec7d"}'
        self.json_RoundDiceResults = \
            '{"dice1": 2, "dice2": 3, ' \
            '"name": "RoundDiceResults", ' \
            '"player_token": "23b3a6c7-6990-44b1-b466-8f8c3da5ec7d", ' \
            '"result": 0}'
        self.json_PlayerMove = \
            '{"destination": 0, "instant": false, "name": "PlayerMove", ' \
            '"player_token": "23b3a6c7-6990-44b1-b466-8f8c3da5ec7d"}'
        self.json_RoundRandomCard = \
            '{"card_id": 1, "is_community": true, ' \
            '"name": "RoundRandomCard", ' \
            '"player_token": "23b3a6c7-6990-44b1-b466-8f8c3da5ec7d"}'
        self.json_PlayerUpdateBalance = \
            '{"name": "PlayerUpdateBalance", ' \
            '"new_balance": 0, "old_balance": 500, ' \
            '"player_token": "23b3a6c7-6990-44b1-b466-8f8c3da5ec7d", ' \
            '"reason": "test"}'
        self.json_PlayerEnterPrison = \
            '{"name": "PlayerEnterPrison", ' \
            '"player_token": "23b3a6c7-6990-44b1-b466-8f8c3da5ec7d"}'
        self.json_PlayerExitPrison = \
            '{"name": "PlayerExitPrison", ' \
            '"player_token": "23b3a6c7-6990-44b1-b466-8f8c3da5ec7d"}'

    def test_serialize(self):
        packet = ExceptionPacket()
        assert packet.serialize() == self.json_str

    def test_deserialize(self):
        packet = PacketUtils.deserialize_packet(json.loads(self.json_str))
        assert packet.name == 'Exception'

    def test_serialize_with_variables(self):
        packet = ActionBuyHouse(player_token="test", property_id=1)
        assert packet.serialize() == self.args_json_str

    def test_deserialize_with_variables(self):
        packet = PacketUtils.deserialize_packet(json.loads(self.args_json_str))
        assert isinstance(packet, ActionBuyHouse)
        assert packet.name == 'ActionBuyHouse'
        assert packet.player_token == 'test'
        assert packet.property_id == 1

    def test_serialize_game_start_dice_results(self):
        packet = GameStartDiceResults()
        packet.add_dice_result(
            player_token='283e1f5e-3411-44c5-9bc5-037358c47100',
            dice1=2,
            dice2=3,
            win=True)

        packet.add_dice_result(
            player_token='23b3a6c7-6990-44b1-b466-8f8c3da5ec7d',
            dice1=2,
            dice2=2,
            win=False)

        assert packet.serialize() == self.game_dice_json_str

    def test_deserialize_game_start_dice_results(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.game_dice_json_str))
        assert isinstance(packet, GameStartDiceResults)
        assert packet.name == 'GameStartDiceResults'
        assert len(packet.dice_result) == 2

        # Player tokens
        assert 'player_token' in packet.dice_result[0]
        assert 'player_token' in packet.dice_result[1]
        assert packet.dice_result[0][
                   'player_token'] == '283e1f5e-3411-44c5-9bc5-037358c47100'
        assert packet.dice_result[1][
                   'player_token'] == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'

        # Dice1
        assert 'dice1' in packet.dice_result[0]
        assert 'dice1' in packet.dice_result[1]
        assert packet.dice_result[0]['dice1'] == 2
        assert packet.dice_result[1]['dice1'] == 2

        # Dice2
        assert 'dice2' in packet.dice_result[0]
        assert 'dice2' in packet.dice_result[1]
        assert packet.dice_result[0]['dice2'] == 3
        assert packet.dice_result[1]['dice2'] == 2

        # Win
        assert 'win' in packet.dice_result[0]
        assert 'win' in packet.dice_result[1]
        assert packet.dice_result[0]['win'] is True
        assert packet.dice_result[1]['win'] is False

    def test_serialize_PlayerPacket(self):
        packet = PlayerPacket(
            name="PlayerPacket",
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d")
        assert packet.serialize() == self.json_PlayerPacket

    def test_deserialize_PlayerPacket(self):
        packet = PlayerPacket(name="PlayerPacket", player_token="")
        packet.deserialize(json.loads(self.json_PlayerPacket))
        assert isinstance(packet, PlayerPacket)
        assert packet.name == 'PlayerPacket'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'

    def test_serialize_InternalCheckPlayerValidity(self):
        packet = InternalCheckPlayerValidity(
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d")
        assert packet.serialize() == self.json_InternalCheckPlayerValidity

    def test_deserialize_InternalCheckPlayerValidity(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_InternalCheckPlayerValidity))
        assert isinstance(packet, InternalCheckPlayerValidity)
        assert packet.name == 'InternalCheckPlayerValidity'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'

    def test_serialize_InternalPlayerDisconnect(self):
        packet = InternalPlayerDisconnect(
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d")
        assert packet.serialize() == self.json_InternalPlayerDisconnect

    def test_deserialize_InternalPlayerDisconnect(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_InternalPlayerDisconnect))
        assert isinstance(packet, InternalPlayerDisconnect)
        assert packet.name == 'InternalPlayerDisconnect'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'

    def test_serialize_PlayerValid(self):
        packet = PlayerValid()
        assert packet.serialize() == self.json_PlayerValid

    def test_deserialize_PlayerValid(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_PlayerValid))
        assert isinstance(packet, PlayerValid)
        assert packet.name == 'PlayerValid'

    def test_serialize_Exception(self):
        packet = ExceptionPacket(code=4100)
        assert packet.serialize() == self.json_Exception

    def test_deserialize_Exception(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_Exception))
        assert isinstance(packet, ExceptionPacket)
        assert packet.name == 'Exception'
        assert packet.code == 4100

    def test_serialize_Ping(self):
        packet = PingPacket(
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d")
        assert packet.serialize() == self.json_Ping

    def test_deserialize_Ping(self):
        packet = PacketUtils.deserialize_packet(json.loads(self.json_Ping))
        assert isinstance(packet, PingPacket)
        assert packet.name == 'Ping'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'

    def test_serialize_AppletPrepare(self):
        packet = AppletPrepare()
        assert packet.serialize() == self.json_AppletPrepare

    def test_deserialize_AppletPrepare(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_AppletPrepare))
        assert isinstance(packet, AppletPrepare)
        assert packet.name == 'AppletPrepare'

    def test_serialize_AppletReady(self):
        packet = AppletReady(
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d")
        assert packet.serialize() == self.json_AppletReady

    def test_deserialize_AppletReady(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_AppletReady))
        assert isinstance(packet, AppletReady)
        assert packet.name == 'AppletReady'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'

    def test_serialize_GameStart(self):
        packet = GameStart(game_name="Test")
        assert packet.serialize() == self.json_GameStart

    def test_deserialize_GameStart(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_GameStart))
        assert isinstance(packet, GameStart)
        assert packet.name == 'GameStart'
        assert packet.game_name == 'Test'

    def test_serialize_PlayerDisconnect(self):
        packet = PlayerDisconnect(
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d")
        assert packet.serialize() == self.json_PlayerDisconnect

    def test_deserialize_PlayerDisconnect(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_PlayerDisconnect))
        assert isinstance(packet, PlayerDisconnect)
        assert packet.name == 'PlayerDisconnect'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'

    def test_serialize_PlayerReconnect(self):
        packet = PlayerReconnect(
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d")
        assert packet.serialize() == self.json_PlayerReconnect

    def test_deserialize_PlayerReconnect(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_PlayerReconnect))
        assert isinstance(packet, PlayerReconnect)
        assert packet.name == 'PlayerReconnect'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'

    def test_serialize_GameStartDice(self):
        packet = GameStartDice()
        assert packet.serialize() == self.json_GameStartDice

    def test_deserialize_GameStartDice(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_GameStartDice))
        assert isinstance(packet, GameStartDice)
        assert packet.name == 'GameStartDice'

    def test_serialize_GameStartDiceThrow(self):
        packet = GameStartDiceThrow(
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d")
        assert packet.serialize() == self.json_GameStartDiceThrow

    def test_deserialize_GameStartDiceThrow(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_GameStartDiceThrow))
        assert isinstance(packet, GameStartDiceThrow)
        assert packet.name == 'GameStartDiceThrow'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'

    def test_serialize_RoundStart(self):
        packet = RoundStart(
            current_player="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d"
        )
        assert packet.serialize() == self.json_RoundStart

    def test_deserialize_RoundStart(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_RoundStart))
        assert isinstance(packet, RoundStart)
        assert packet.name == 'RoundStart'
        assert packet.current_player == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'

    def test_serialize_RoundDiceChoice(self):
        packet = RoundDiceChoice(
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d")
        assert packet.serialize() == self.json_RoundDiceChoice

    def test_deserialize_RoundDiceChoice(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_RoundDiceChoice))
        assert isinstance(packet, RoundDiceChoice)
        assert packet.name == 'RoundDiceChoice'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'

    def test_serialize_RoundDiceResults(self):
        packet = RoundDiceResults(
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d",
            dice1=2, dice2=3)
        assert packet.serialize() == self.json_RoundDiceResults

    def test_deserialize_RoundDiceResults(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_RoundDiceResults))
        assert isinstance(packet, RoundDiceResults)
        assert packet.name == 'RoundDiceResults'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'
        assert packet.dice1 == 2
        assert packet.dice2 == 3

    def test_serialize_PlayerMove(self):
        packet = PlayerMove(
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d")
        assert packet.serialize() == self.json_PlayerMove

    def test_deserialize_PlayerMove(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_PlayerMove))
        assert isinstance(packet, PlayerMove)
        assert packet.name == 'PlayerMove'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'

    def test_serialize_RoundRandomCard(self):
        packet = RoundRandomCard(
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d",
            card_id=1, is_community=True)
        assert packet.serialize() == self.json_RoundRandomCard

    def test_deserialize_RoundRandomCard(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_RoundRandomCard))
        assert isinstance(packet, RoundRandomCard)
        assert packet.name == 'RoundRandomCard'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'
        assert packet.card_id == 1
        assert packet.is_community

    def test_serialize_PlayerUpdateBalance(self):
        packet = PlayerUpdateBalance(
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d",
            old_balance=500, new_balance=0, reason="test")
        assert packet.serialize() == self.json_PlayerUpdateBalance

    def test_deserialize_PlayerUpdateBalance(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_PlayerUpdateBalance))
        assert isinstance(packet, PlayerUpdateBalance)
        assert packet.name == 'PlayerUpdateBalance'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'
        assert packet.old_balance == 500
        assert packet.new_balance == 0
        assert packet.reason == "test"

    def test_serialize_PlayerEnterPrison(self):
        packet = PlayerEnterPrison(
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d")
        assert packet.serialize() == self.json_PlayerEnterPrison

    def test_deserialize_PlayerEnterPrison(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_PlayerEnterPrison))
        assert isinstance(packet, PlayerEnterPrison)
        assert packet.name == 'PlayerEnterPrison'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'

    def test_serialize_PlayerExitPrison(self):
        packet = PlayerExitPrison(
            player_token="23b3a6c7-6990-44b1-b466-8f8c3da5ec7d")
        assert packet.serialize() == self.json_PlayerExitPrison

    def test_deserialize_PlayerExitPrison(self):
        packet = PacketUtils.deserialize_packet(
            json.loads(self.json_PlayerExitPrison))
        assert isinstance(packet, PlayerExitPrison)
        assert packet.name == 'PlayerExitPrison'
        assert packet.player_token == '23b3a6c7-6990-44b1-b466-8f8c3da5ec7d'
