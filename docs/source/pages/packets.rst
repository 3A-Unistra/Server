Packets
=======

Le contenu des paquets est au format JSON.

.. code-block:: json
    :caption: Structure abstraite d'un paquet

    {
    "packet_name": "testpacket123"
    }

Paquets demarrage
-----------------

AppletPrepare
^^^^^^^^^^^^^

Paquet envoyé par le serveur au WebSocket du lobby, voir **Paquets démarrage**
A partir de ce moment là, la partie web devra démarrer l'applet unity et se déconnecter du WebSocket "lobby".
L'applet unity webgl devra se connecter au WebSocket de la partie et envoyer le paquet AppletReady.

*ce paquet ne contient pas d'informations*

AppletReady
^^^^^^^^^^^
(*envoyé par le client*).
Ce paquet est envoyé par le client quand il a chargé l'applet.
Le client est toujours en "Loading Screen (attente des joueurs)"
Quand le serveur a recu tous les AppletReady nécessaire il envoie le paquet GameStart.

*ce paquet ne contient pas d'informations*

Paquets début de jeu
--------------------

GameStart
^^^^^^^^^

Lorsque tous les joueurs sont prêts et ont chargé le jeu.
-> Enleve l'écran d'attente des joueurs

*ce paquet ne contient pas d'informations*


PlayerConnect
^^^^^^^^^^^^^

Lorsqu'un joueur se connecte, ou un bot en début de partie.

**contenu du paquet :**
 * indiquer si c'est un bot (*is_bot*)
 * niveau de difficulté du bot (*level_bot*, valeur par défaut -1)
 * identifiant du joueur si c'est un joueur (*id_player*, valeur par défaut -1)

.. code-block:: json
    :caption: exemple Paquet PlayerConnect

    {
    "packet_name": "PlayerConnect",
    "is_bot" : true,
    "level_bot" : 3,
    "id_player" : -1
    }


PlayerDisconnect
^^^^^^^^^^^^^^^^

Lorsqu'un joueur se déconnecte, crash ou timeout.
*si ce paquet est reçu, le joueur en question doit être remplacé par un bot*

**contenu du paquet :**
 * identifiant du joueur
 * raison de la deconnexion

GameStartDice
^^^^^^^^^^^^^
Paquet à envoyer à chaque client pour que l'applet unity demande aux joueurs de lancer le dé.

*ce paquet ne contient pas d'informations*

GameStartDiceThrow
^^^^^^^^^^^^^^^^^^
(*envoyé par le client*)
Envoyé lorque le client a appuyé sur le bouton pour lancer le dé. Si le serveur ne reçoit pas
 ce paquet après un timeout du paquet *GameStartDice*, le serveur lance le dé automatiquement.

**contenu du paquet :**
 * identifiant du joueur (*id_player*)


GameStartDiceResults
^^^^^^^^^^^^^^^^^^^^
Paquet contenant le résultat du lancer de dé du joueur.
Si plusieurs joueurs de la partie ont un même résultat, il faut renvoyer un paquet *GameStartDice* à tout le monde.

**contenu du paquet :**
 * identifiant du joueur (*id_player*)
 * résultat du lancer de dé (*dice_result*)

RoundStart
^^^^^^^^^^
Notifie les clients que la partie peut débuter.

*ce paquet ne contient pas d'informations*

RoundDiceThrow
^^^^^^^^^^^^^^
(*envoyé par le client*). Envoyé lorque le client à qui c'est le tout appuye sur le bouton pour lancer le dé.

**contenu du paquet :**
 * identifiant du joueur. (*id_player*)


RoundDiceResults
^^^^^^^^^^^^^^^^
Paquet contenant le résultat du lancer de dé du joueur. Envoyé à tout les joueurs, le résultat des lancers de dés étant publique.

**contenu du paquet :**
 * identifiant du joueur (*id_player*)
 * résultat du lancer de dé (*dice_result*)

Paquet début tour
-----------

RoundDiceChoice
^^^^^^^^^^^^^^^
(*envoyé par le client*).
Paquet indiquant au serveur que le joueur souhaite lancer un dé, en début de tour.
Seul le joueur dont c'est le tour peut envoyer ce paquet.

**contenu du paquet :**
 * identifiant du joueur (*id_player*)


PlayerMove
^^^^^^^^^^
Indique aux clients qu'un des joueurs se déplace.

**contenu du paquet : **
 * id du joueur qui se déplace (*id_moving_player*)
 * case de destination (*destination_case*)

RoundRandomCard
^^^^^^^^^^^^^^^

Si le joueur tombe sur une case communautaire ou une case de chance, ce paquet est envoyé à tout le monde.

**contenu du paquet :**
 * id du joueur (*id_player*)
 * indiquer si c'est une case communautaire ou de chance (*is_communautaire*)
 * contenu de la carte tiré aléatoirement (*card_content*)

PlayerUpdateBalance
^^^^^^^^^^^^^^^^^^^

Lorsque la somme d'argent d'un joueur modifie, ce paquet est envoyé à tout les clients pour les notifier de ce changement

**contenu du paquet :**
 * id du joueur dont la somme a changé (*id_player*)
 * Somme qu'il avait (*old_balance*)
 * Nouvel somme (*new_balance*)
 * raison

PlayerEnterPrison
^^^^^^^^^^^^^^^^^
Paquet envoyé lorsque le joueur entre en prison

**contenu du paquet :**
 * id du joueur allant en prison (*id_player*)


PlayonExitPrison
^^^^^^^^^^^^^^^^
Paquet envoyé lorsque le joueur sort de pri
