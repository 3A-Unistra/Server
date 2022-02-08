Packets
=======

Le contenu des paquets est au format JSON.

AppletPrepare
-------------

Paquet envoyé par le serveur au WebSocket du lobby, voir **Paquets démarrage**
A partir de ce moment là, la partie web devra démarrer l'applet unity et se déconnecter du WebSocket "lobby".
L'applet unity webgl devra se connecter au WebSocket de la partie et envoyer le paquet AppletReady.

*ce paquet ne contient pas d'informations*

AppletReady
-----------
(*envoyé par le client*).
Ce paquet est envoyé par le client quand il a chargé l'applet.
Le client est toujours en "Loading Screen (attente des joueurs)"
Quand le serveur a recu tous les AppletReady nécessaire il envoie le paquet GameStart.

*ce paquet ne contient pas d'informations*

GameStart
---------

Lorsque tous les joueurs sont prêts et ont chargé le jeu.
-> Enleve l'écran d'attente des joueurs

*ce paquet ne contient pas d'informations*


PlayerConnect
-------------

Lorsqu'un joueur se connecte, ou un bot en début de partie.

**contenu du paquet :**
 * indiquer si c'est un bot + niveau de difficultés du bot
 * identifiant du joueur si c'est un joueur

PlayerDisconnect
----------------

Lorsqu'un joueur se déconnecte, crash ou timeout.
*si ce paquet est reçu, le joueur en question doit être remplacé par un bot*

**contenu du paquet :**
 * identifiant du joueur
 * raison de la deconnexion

GameStartDice
-------------
Paquet à envoyer à chaque client pour que l'applet unity demande aux joueurs de lancer le dé.

*ce paquet ne contient pas d'informations*

GameStartDiceThrow
------------------
(*envoyé par le client*)
Envoyé lorque le client a appuyé sur le bouton pour lancer le dé. Si le serveur ne reçoit pas
 ce paquet après un timeout du paquet *GameStartDice*, le serveur lance le dé automatiquement.

**contenu du paquet :**
 * identifiant du joueur


GameStartDiceResults
--------------------
Paquet contenant le résultat du lancer de dé du joueur.
Si plusieurs joueurs de la partie ont un même résultat, il faut renvoyer un paquet *GameStartDice* à tout le monde.

**contenu du paquet :**
 * identifiant du joueur
 * résultat du lancer de dé

RoundStart
----------
Notifie les clients que la partie peut débuter.

*ce paquet ne contient pas d'informations*

RoundDiceThrow
--------------
(*envoyé par le client*). Envoyé lorque le client à qui c'est le tout appuye sur le bouton pour lancer le dé.

**contenu du paquet :**
 * identifiant du joueur.


RoundDiceResults
----------------
Paquet contenant le résultat du lancer de dé du joueur.

**contenu du paquet :**
 * identifiant du joueur
 * résultat du lancer de dé
