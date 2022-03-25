Packets
=======

Le contenu des paquets est au format JSON.

.. code-block:: json
    :caption: Structure abstraite d'un paquet

    {
    "name": "testpacket123"
    }

Paquets lobby
-------------

InternalInitConnection
^^^^^^^^^^^^^^^^^^^^^^
Paquet envoyé lorsque un joueur se connecte.

**contenu du paquet :**
 * id du joueur (*player_token*)

LaunchGame
^^^^^^^^^^
Paquet envoyé *par le client* lorsque le host du lobby lance la partie.

**contenu du paquet :**
 * id du joueur lançant la partie (*player_token*)

GetInRoom
^^^^^^^^^
Paquet envoyé *par le client* lorsqu'il veut rentrer dans une partie.

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id de la salle (*id_room*)
 * mot de passe (*password*)


GetInRoomSuccess
^^^^^^^^^^^^^^^^
Paquet envoyé au client pour signifier le succès de son entrée dans une partie

*ce paquet ne contient pas d'informations*


GetOutRoom
^^^^^^^^^^
Paquet envoyé *par le client* lorsque un joueur veut sortir d'un lobby de partie.

**contenu du paquet :**
 * id du joueur (*player_token*)


GetOutRoomSuccess
^^^^^^^^^^^^^^^^^
Paquet envoyé au client pour confirmer le succès de la sortie du lobby de partie

*ce paquet ne contient pas d'informations*



CreateGame
^^^^^^^^^^
Paquet envoyé *par le client* lorsqu'il veut créer une partie

**contenu du paquet :**
 * id du player créant la partie (*player_token*)
 * nombre de joueurs (*max_nb_players*)
 * partie privé ou public (*is_private*)
 * montant de base pour chaque joueur (*starting_balance*)
 * mot de passe (peut être un champ vide) (*password*)


CreateGameSuccess
^^^^^^^^^^^^^^^^^

Paquet envoyé par le serveur pour confirmer la création d'une partie

**contenu du packet :**
 * id du player (*player_token*)

AppletPrepare
^^^^^^^^^^^^^

Paquet envoyé par le serveur au WebSocket du lobby, voir **Paquets démarrage**
A partir de ce moment là, la partie web devra démarrer l'applet unity et se déconnecter du WebSocket "lobby".
L'applet unity webgl devra se connecter au WebSocket de la partie et envoyer le paquet AppletReady.

**contenu du paquet :**
 * id du joueur (*player_token*)

BroadcastUpdatedRoom
^^^^^^^^^^^^^^^^^^^^

Paquet envoyé lorsque qu'un lobby change de statut (soit le nombre de joueurs, soit la partie est lancé, etc).
Ce paquet est envoyé à tout les joueurs qui sont dans le lobby (pas in-game).

**contenu du paquet :**
 * id du lobby (*id_room*)
 * l'ancien nombre de joueurs (*old_nb_players*)
 * le nouveau nombre de joueurs (*new_nb_players*)
 * le statut de la partie (*state*)


AddBot
^^^^^^

Paquet envoyé *par le client* (le host) lorsqu'il ajoute un bot à la partie

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id du room (*id_room*)
 * difficulté du bot (*bot_difficulty*)


DeleteRoom
^^^^^^^^^^

Paquet envoyé *par le client* lorsqu'un joueur veut supprimer la partie (avant qu'elle soit lancée).
Ce paquet ne peut être envoyé que par l'hôte de la partie.

**contenu du paquet :**
 * id du joueur (*player_token*)


DeleteRoomSuccess
^^^^^^^^^^^^^^^^^
Paquet envoyé au client pour lui signaler le succès de la suppression d'une partie.
Les autres joueurs seront prévenus via un BroadcastUpdatedRoom avec le champ *state* à CLOSED.

*ce paquet ne contient pas d'informations*


Paquets demarrage
-----------------

PlayerPing
^^^^^^^^^^

Paquet heartbeat, envoyé toutes les 10 secondes.
C'est un paquet ping-pong, le serveur envoie, le client reçoit.
Si le serveur ne reçoit pas de paquet en retour après 10 secondes,
il ferme la connexion (broadcast PlayerDisconnect)

PlayerValid
^^^^^^^^^^^

Paquet envoyé lorsque le joueur a été validé par le serveur.
Lorsqu'on se connecte au WebSocket Game, on doit attendre ce paquet, avant de pouvoir envoyer d'autres
paquets (pendant ce temps les données échangées seront refusées par le serveur).

Si le client reçoit ce message, alors la connexion est valide.
Dans le cas contraire, le serveur ferme la connexion WebSocket avec le client.



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

**contenu du paquet :**

.. code-block:: json
    :caption: Informations dans la variable players du paquet GameStart
    {
      "name": "GameStart",
      "game_name": "GameExample",
      "players": [
        {
          "player_token": "",
          "name": "",
          "bot": false,
          "money": 0,
          "position": 0,
          "jail_turns": 0,
          "jail_cards": {
            "chance": false,
            "community": false
          },
          "in_jail": false,
          "bankrupt": false,
          "piece": 0
        }
      ]
    }




PlayerDisconnect
^^^^^^^^^^^^^^^^

Lorsqu'un joueur se déconnecte, crash ou timeout.
*si ce paquet est reçu, le joueur en question doit être remplacé par un bot*

**contenu du paquet :**
 * identifiant du joueur
 * raison de la deconnexion

PlayerReconnect
^^^^^^^^^^^^^^^^

Lorsqu'un joueur se reconnecte après un crash ou timeout.
*si ce paquet est reçu, il faut remettre le joueur à la place du bot*

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

Ce paquet est un ping-pong, le client l'envoie au serveur, puis le serveur renvoie en broadcast,
le paquet à tous les autres clients. (cela permet de voir qui a commencé de lancer les dés)

**contenu du paquet :**
 * identifiant du joueur (*player_token*)


GameStartDiceResults
^^^^^^^^^^^^^^^^^^^^
Paquet contenant le résultat du lancer de dé de tout les joueurs.
Si plusieurs joueurs de la partie ont un même résultat, il faut renvoyer un paquet *GameStartDice* à tout le monde.

**contenu du paquet :**
 * résultat du lancer de dé (*dice_result*) : liste de [{"player_token": bla, "dice1": 1, "dice2": 2, win: false}]

RoundStart
^^^^^^^^^^
Notifie les clients qu'une nouvelle manche démarre.

**contenu du paquet :**
 * identifiant du joueur qui joue. (*current_player*)

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

Exception
^^^^^^^^^
Paquet envoyé lorsque une erreur a lieu. Les codes d'erreurs seront spécifiés dans l'index d'erreurs.

**contenu du paquet :**
 * code d'erreurs (*error_code*)

Paquet début tour
-----------------

RoundDiceChoice
^^^^^^^^^^^^^^^
(*envoyé par le client*).
Paquet indiquant au serveur que ce que le joueur a choisi de faire,
entre trois possibilités : ROLL_DICES = 0, JAIL_PAY = 1, JAIL_CARD = 2.
Seul le joueur dont c'est le tour peut envoyer ce paquet.

**contenu du paquet :**
 * choice : int(enum(ROLL_DICES = 0, JAIL_PAY = 1, JAIL_CARD = 2))

PlayerMove
^^^^^^^^^^
Indique aux clients qu'un des joueurs se déplace.

**contenu du paquet : **
 * id du joueur qui se déplace (*player_token*)
 * case de destination (*destination*)

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
 * id du joueur dont la somme a changé (*player_token*)
 * Balance qu'il avait (*old_balance*)
 * Nouvelle balance (*new_balance*)
 * raison

PlayerEnterPrison
^^^^^^^^^^^^^^^^^
Paquet envoyé lorsque le joueur entre en prison

**contenu du paquet :**
 * id du joueur allant en prison (*player_token*)


PlayerExitPrison
^^^^^^^^^^^^^^^^
Paquet envoyé lorsque le joueur sort de prison

**contenu du paquet :**
 * id du joueur allant en prison (*player_token*)

Paquet d'actions durant le tour
-------------------------------
Paquets concernant les actions durant le tour. Le tour commmence en instaurant un timeout. Si le joueur ne sélectionne pas d'actions
 avant la fin du timeout, il est compté comme déconnecté.

Paquet ActionExchange
^^^^^^^^^^^^^^^^^^^^^
Paquet envoyé par client lorsque le joueur veut effectuer un échange avec un autre joueur.

**contenu du paquet**
 * id du joueur (*id_player*)

Paquet ActionExchangePlayerSelect
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

paquet *envoyé par le client* pour la sélection du joueur avec qui on veut faire l'échange. Ce paquet est relayé à tout les clients pour qu'ils puissent suivre l'échange en direct.

**contenu du paquet**
 * id du joueur qui initialise l'échange (*id_init_request*)
 * id du joueur avec qui l'échange veut être fait (*id_of_requested*)
 * contenu de l'échange (*content_trade*, peut être nul)


Paquet ActionExchangeTradeSelect
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ce paquet *envoyé par le client* spécifie la nature de l'échange. Il est relayé à tout les clients pour qu'ils puissent suivre l'échange en direct.

**contenu du paquet**
 * id du joueur qui initialise l'échange (*id_init_request*)
 * id du joueur avec qui l'échange veut être fait (*id_of_requested*, peut être nul)
 * contenu de l'échange (*content_trade*)

Paquet ActionExchangeSend
^^^^^^^^^^^^^^^^^^^^^^^^^

Ce paquet *envoyé par le client* est envoyé pour notifier qu'un échange va avoir lieu. Il est relayé à tout les clients pour
qu'ils puissent suivre l'échange en direct. Ceux qui ne sont pas concernés par l'échange recevront juste les paquets et montreront
 les animations nécessaire.

**contenu du paquet**
  * id du joueur qui initialise l'échange (*id_init_request*)
  * id du joueur avec qui l'échange veut être fait (*id_of_requested*)
  * contenu de l'échange (*content_trade*)

Paquet ActionExchangeDecline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par le client* si le joueur avec qui l'échange est censé être effectué refuse. Le paquet est relayé à tout le monde.

*Ce paquet ne contient pas d'informations*

Paquet ActionExchangeCounter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ce paquet est *envoyé par le client* dans le cas où le joueur avec qui l'échange est censé être effectué veut effectuer une contre proposition.
Le paquet est relayé à tout le monde. Pour la renégotiation de l'échange, le paquet *ActionExchangeTradeSelect* est utilisé.

*Ce paquet ne contient pas d'informations*

Paquet ActionExchangeAccept
^^^^^^^^^^^^^^^^^^^^^^^^^^^
paquetspaquetspaquets
Paquet envoyé *par le client* si le joueur avec qui l'échange est censé être effectué accepte. Le paquet est relayé à tout le monde.

*Ce paquet ne contient pas d'informations*

Paquet ActionExchangeCancel
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ce paquet est envoyé à tout le monde. Il notifie à tout les clients que l'échange a été annulé, soit parce que les ressources de la personne
a qui l'échange était demandé ne sont pas suffisantes, soit par demande du joueur qui a initialisé l'échange.

**contenu du paquet :**
 * raison de l'annulation (*reason*)


Paquet PlayerUpdateProperty
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé à tout le monde lorsqu'un joueur à un changement dans ses propriétés.

**contenu du paquet :**
 * id du joueur (*id_player*)
 * indiquer si c'est une propriétés en + ou en - (*is_added*)
 * indiquer la nature de la propriétés (*property*)

Paquet ActionAuctionProperty
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par le client* lorsqu'un joueur souhaite vendre une propriété aux enchères.

**contenu du paquet :**
 * id du joueur (*id_player*)
 * nature de la propriétés (*property*)
 * prix de base (*min_price*)

Paquet AuctionRound
^^^^^^^^^^^^^^^^^^^

Paquet envoyé à tout les clients pour leur indiquer qu'un tour d'enchères va débuter.

**contenu du paquet :**
 * nature de la propriété mise en enchères (*property*)
 * id du joueur mettant la propriétés en enchères (*id_seller*)
 * prix actuel (*current_price*)

Paquet AuctionBid
^^^^^^^^^^^^^^^^^

Paquet envoyé *par un client* lorsque ce dernier enchérit durant une enchères. Ce paquet est relayé à tout les clients pour
qu'ils puissent suivre l'enchère en direct.

**contenu du paquet :**
 * id du joueur (*id_bidder*)
 * prix proposé (*new_price*)

Paquet AuctionConcede
^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par un client* lorsque ce dernier ne souhaite pas participer à ce tour d'enchères. Ce paquet est relayé à tout
le monde pour qu'ils puissent suivre l'enchères en direct.

**contenu du paquet :**
 * id du joueur (*id_bidder*)

Paquet AuctionEnd
^^^^^^^^^^^^^^^^^

Paquet envoyé à tout le monde si personne n'enchérit pendant un tour d'enchères. Il signifie la fin des enchères.

*Ce paquet ne contient pas d'informations*


Paquet ActionBuyProperty
^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par un client* lorsque le joueur veut acheter une propriété.

**contenu du paquet :**
 * id du joueur (*id_player*)
 * nature de la propriété (*property*)

Paquet ActionBuyPropertySucceed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé à tout le monde si l'achat de la propriété par un joueur est un succès.

**contenu du paquet :**
 * id du joueur (*id_player*)
 * nature de la propriété (*property*)

Paquet ActionMortgageProperty
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par un client* lorsque le joueur veut hypothéquer une propriété.

**contenu du paquet :**
 * id du joueur (*id_player*)
 * nature de la propriété (*property*)

Paquet ActionMortgageSucceed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé à tout le monde lorsqu'une hypothèque a été couronné de succès.

**contenu du paquet :**
 * id du joueur (*id_player*)
 * nature de la propriété (*property*)

Paquet ActionUnmortgageProperty
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par un client* lorsque le joueur veut déshypothéquer une propriété.

**contenu du paquet :**
 * id du joueur (*id_player*)
 * nature de la propriété (*property*)

Paquet ActionUnmortgageSucceed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé à tout le monde lorsqu'un déshypothèquement a été couronné de succès.

**contenu du paquet :**
 * id du joueur (*id_player*)
 * nature de la propriété (*property*)


Paquet ActionBuyHouse
^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par un client* lorsque le joueur veut acheter une maison

**contenu du paquet :**
 * id du joueur (*id_player*)
 * id de la maison (*id_house*)

Paquet ActionBuyHouseSucceed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé à tout le monde lorsque l'achat d'une maison a été couronné de succès.

**contenu du paquet :**
 * id du joueur (*id_player*)
 * id de la maison (*id_house*)

Paquet ActionSellHouse
^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par un clinet* lorsque le joueur veut vendre une maison.

**contenu du paquet :**
 * id du joueur (*id_player*)
 * id de la maison (*id_house*)

Paquet ActionSellHouseSucceed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé à tout le monde lorsque la vente d'une maison a été couronné de succès.

**contenu du paquet :**
 * id du joueur (*id_player*)
 * id de la maison (*id_house*)
