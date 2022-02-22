"""
TODO : définir tout les paquets

 Créer un constructeur vide


 Créer un constructeur avec tous les arguments possibles pour chaque paquet


 Bien typer chaque variable


Implémenter les fonctions serialize/deserialize pour tout les paquets
"""

import json


class AppletPrepare(Packet) :
    def __init__(self, name : str):
        super(AppletPrepare, self).__init__(name)

    def serialize(self) -> str:
        json.dumps(self.__dict__, skipkeys = True)

    def deserialize(self, received:str):
        json.loads(received)
