"""
TODO : définir tout les paquets

 Créer un constructeur vide


 Créer un constructeur avec tous les arguments possibles pour chaque paquet


 Bien typer chaque variable


Implémenter les fonctions serialize/deserialize pour tout les paquets
"""

from packet import Packet


class AppletPrepare(Packet):
    def __init__(self, name: str):
        super(AppletPrepare, self).__init__(name)


class AppletReady(Packet):
    def __init__(self, name: str):
        super(AppletReady, self).__init__(name)


class GameStart(Packet):
    def __init__(self, name: str):
        super(GameStart, self).__init__(name)


class PlayerDisconnect(Packet):
    def __init__(self, name: str,  id_player: str, reason: str):
        super(PlayerDisconnect, self).__init__(name)
        self.id_player = id_player
        self.reason = reason

    def deserialize(self, obj: object):
        self.id_player = str(obj['id_player'])
        self.reason = str(obj['reason'])


class PlayerReconnect(Packet):
    def __init__(self, name: str, id_player: str, reason: str):
        super(PlayerReconnect, self).__init__(name)
        self.id_player = id_player
        self.reason = reason

    def deserialize(self, obj: object):
        self.id_player = str(obj['id_player'])
        self.reason = str(obj['reason'])


class GameStartDice(Packet):
    def __init__(self, name: str):
        super(GameStartDice, self).__init__(name)


class GameStartDiceThrow(Packet):
    def __init__(self, name: str, id_player: str):
        super(GameStartDiceThrow, self).__init__(name)
        self.id_player = id_player

    def deserialize(self, obj: object):
        self.id_player = str(obj['id_player'])


class GameStartDiceResults(Packet):
    def __init__(self, name: str,  id_player: str, dice_result: int):
        super(GameStartDiceResults, self).__init__(name)
        self.id_player = id_player
        self.dice_result = dice_result

    def deserialize(self, obj: object):
        self.id_player = str(obj['id_player'])
        self.dice_result = int(obj['reason'])


class RoundStart(Packet):
    def __init__(self, name: str):
        super(RoundStart, self).__init__(name)


class RoundDiceThrow(Packet):
    def __init__(self, name: str, id_player: str):
        super(RoundDiceThrow, self).__init__(name)
        self.id_player = id_player

    def deserialize(self, obj: object):
        self.id_player = str(obj['id_player'])


class RoundDiceChoice(Packet):
    def __init__(self, name: str,  id_player: str):
        super(RoundDiceChoice, self).__init__(name)
        self.id_player = id_player

    def deserialize(self, obj: object):
        self.id_player = str(obj['id_player'])


class PlayerMove(Packet):
    def __init__(self, name: str, id_moving_player: str,
                 destination_case: int):
        super(PlayerMove, self).__init__(name)
        self.id_moving_player = id_moving_player
        self.destination_case = destination_case

    def deserialize(self, obj: object):
        self.id_moving_player = str(obj['id_moving_player'])
        self.destination_case = int(obj['destination_case'])


class RoundRandomCard(Packet):
    def __init__(self, name: str, id_player: str,
                 is_communautaire: bool, card_content: str):
        super(RoundRandomCard, self).__init__(name)
        self.id_player = id_player
        self.is_communautaire = is_communautaire
        self.card_content = card_content

    def deserialize(self, obj: object):
        self.id_player = obj['id_player']
        self.is_communautaire = bool(obj['is_communautaire'])
        self.card_content = obj['card_content']
