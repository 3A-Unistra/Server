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

LaunchGame
^^^^^^^^^^
Paquet envoyé *par le client* lorsque le host du lobby lance la partie.

**contenu du paquet :**
 * id du joueur lançant la partie (*player_token*)

EnterRoom
^^^^^^^^^
Paquet envoyé *par le client* lorsqu'il veut rentrer dans une partie.

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id de la salle (*game_token*)
 * mot de passe (*password*)


EnterRoomSucceed
^^^^^^^^^^^^^^^^
Paquet envoyé au client pour signifier le succès de son entrée dans une partie

**contenu du paquet :**
 * id du pion que le joueur aura (*piece*)
 * username du joueur (*username*)
 * url de l'avatar du joueur (*avatar_url*)
 * id du host (*host_token*)


LeaveRoom
^^^^^^^^^
Paquet envoyé *par le client* lorsque un joueur veut sortir d'un lobby de partie.

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id de la partie (*game_token*)


LeaveRoomSucceed
^^^^^^^^^^^^^^^^
Paquet envoyé au client pour confirmer le succès de la sortie du lobby de partie

*ce paquet ne contient pas d'informations*

CreateGame
^^^^^^^^^^
Paquet envoyé *par le client* lorsqu'il veut créer une partie

**contenu du paquet :**
 * id du player créant la partie (*player_token*)
 * nombre de joueurs (*max_nb_players*)
 * mot de passe (peut être un champ vide) (*password*)
 * nom de la partie (*game_name*)
 * partie privé ou public (*is_private*)
 * montant de base pour chaque joueur (*starting_balance*)
 * activer/désactiver enchère (*option_auctions*)
 * activer désactiver doublage d’argent sur la case GO (*option_double_on_start*)
 * temps max pour les actions d'un tour (*option_max_time*)
 * nombre de tour maximum (*option_max_rounds*)
 * acheter dès le premier tour (*option_first_round_buy*)


CreateGameSucceed
^^^^^^^^^^^^^^^^^

Paquet envoyé par le serveur pour confirmer la création d'une partie

**contenu du packet :**
 * id du player (*player_token*)
 * id du pion que le joueur aura (*piece*)
 * username du joueur (*username*)
 * lien de l'avatar du joueur (*avatar_url*)

AppletPrepare
^^^^^^^^^^^^^

Paquet envoyé par le serveur au WebSocket du lobby, voir **Paquets démarrage**
A partir de ce moment là, la partie web devra démarrer l'applet unity et se déconnecter du WebSocket "lobby".
L'applet unity webgl devra se connecter au WebSocket de la partie et envoyer le paquet AppletReady.

**contenu du paquet :**
 * id du joueur (*player_token*)

BroadcastUpdateLobby
^^^^^^^^^^^^^^^^^^^^
Ce paquet est envoyé au joueur du lobby général lorsque le statut d'un lobby en particulier change. Il est aussi utilisé
 pour donner les infos de tous les lobbys lors de la connexion initial d'un joueur.

**contenu du paquet :**
 * id du lobby (*game_token*)
 * raison de l'update (nv joueur, joueur supprimé, etc) (*reason* (integer!))

.. code-block:: python
    :caption: Enum UpdateReason

    class UpdateReason(Enum):
        NEW_CONNECTION = 0
        NEW_PLAYER = 1
        PLAYER_LEFT = 2
        ROOM_DELETED = 3
        ROOM_CREATED = 4
        HOST_LEFT = 5
        LAUNCHING_GAME = 6
        NEW_BOT = 7
        DELETE_BOT = 8
    }

:

BroadcastUpdateRoom
^^^^^^^^^^^^^^^^^^^
Ce paquet est envoyé au joueur connecté à une salle lorsque le statut de ladite salle change.

**contenu du paquet :**
 * id du lobby (*game_token*)
 * le nombre de joueur (*nb_players*)
 * le joueur ajouté ou supprimé (peut-être un champ vide) (*player*)
 * username du joueur (*username*)
 * url de l'avatar du joueur (*avatar_url*)
 * raison de l'update (nv joueur, joueur supprimé, etc) (*reason* (integer!))

.. code-block:: python
    :caption: Enum UpdateReason

    class UpdateReason(Enum):
        NEW_CONNECTION = 0
        NEW_PLAYER = 1
        PLAYER_LEFT = 2
        ROOM_DELETED = 3
        ROOM_CREATED = 4
        HOST_LEFT = 5
        LAUNCHING_GAME = 6
        NEW_BOT = 7
        DELETE_BOT = 8
    }

:

BroadcastNewRoomToLobby
^^^^^^^^^^^^^^^^^^^^^^^
Ce paquet est envoyé aux clients lorsque une nouvelle salle d'attente est créée. Il est aussi utilisé pour envoyer
 l'état de toute les salles présentes lors d'une nouvelle connexion.

**contenu du paquet :**
 * id de la salle (*game_token*)
 * nom de la salle (*game_name*)
 * nombre de joueurs (*nb_players*)
 * nombre de joueurs max (*max_nb_players*)
 * privé ou non (*is_private*)
 * mdp ou non (*has_password*)

StatusRoom
^^^^^^^^^^

Ce paquet est envoyé lorsqu'un joueur rejoint une salle. Ce paquet comporte tout les détails de la partie.


**contenu du paquet :**
 * id du lobby (*game_token*)
 * nom de la partie (*game_name*)
 * le nombre de joueur (*nb_players*)
 * le nombre de joueurs max (*max_nb_players*)
 * la liste des joueurs (*players*)
 * la liste des username (*players_username*)
 * la liste des url des avatars (*players_avatar_url*)
 * la liste des pions (*players_piece*)
 * raison de l'update (nv joueur, joueur supprimé, etc) (*reason* (integer!))
 * option enchère activé ou désactivé (*option_auction*)
 * option double on start (*option_double_on_start*)
 * temps maximum par tour (*option_max_time*)
 * nombre de rounds maximum (*option_maxnb_rounds*)
 * possibilité d'acheter au premier tour activé/désactivé (*option_first_round_buy*)
 * argent de base (*starting_balance*)


AddBot
^^^^^^

Paquet envoyé *par le client* (le host) lorsqu'il ajoute un bot à la partie

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id du room (*game_token*)
 * difficulté du bot (*bot_difficulty*)


AddBotSucceed
^^^^^^^^^^^^^

Paquet envoyé pour confirmer qu'un bot a bien été ajouté

**contenu du paquet :**
 * id du bot (*bot_token*)

DeleteBot
^^^^^^^^^
Paquet envoyé *par le client* lorsque le host veut supprimer un bot.

**contenu du paquet :**
 * id du bot (*bot_token*)

DeleteBotSucceed
^^^^^^^^^^^^^^^^

paquet envoyé pour confirmer qu'un bot est bien supprimé

**contenu du paquet :**
 * id du bot (*bot_token*)

NewHost
^^^^^^^

Paquet envoyé à un joueur de la salle d'attente lorsque le host de la partie demande à sortir, ou s'il se deconnecte

*ce paquet ne contient pas d'informations*


FriendConnected
^^^^^^^^^^^^^^^

Paquet envoyé à un joueur pour le notifier qu'un de ses amis est connecté.
Lors de la connexion d'un joueur, tout ses amis connectés sont notifiés, et il reçoit également
un paquet FriendConnected par ami connecté qu'il a.

**contenu du paquet :**
 * id de l'ami connecté : *friend_token*
 * username de l'ami connecté *username*
 * avatar de l'ami connecté *avatar_url*

FriendDisconnected
^^^^^^^^^^^^^^^^^^

Paquet envoyé à un joueur pour le notifier qu'un de ses amis n'est plus connecté.

**contenu du paquet :**
 * id de l'ami connecté : *friend_token*
 * username de l'ami connecté *username*
 * avatar de l'ami connecté *avatar_url*



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

PlayerDefeat
^^^^^^^^^^^^

Lorsqu'un joueur a perdu (solde négatif a la fin de son tour)

**contenu du paquet :**
 * identifiant du joueur (*player_token*)

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
 * si possible d'acheter une propriété (*can_buy_property*)

RoundDiceResults
^^^^^^^^^^^^^^^^
Paquet contenant le résultat du lancer de dé du joueur. Envoyé à tout les joueurs, le résultat des lancers de dés étant publique.

**contenu du paquet :**
 * identifiant du joueur (*player_token*)
 * result : int(enum(ROLL_DICES = 0, JAIL_PAY = 1, JAIL_CARD_CHANCE = 2, JAIL_CARD_COMMUNITY = 3))
 * résultat dé 1 : (*dice1*)
 * résultat dé 2 : (*dice2*)

Exception
^^^^^^^^^
Paquet envoyé lorsque une erreur a lieu. Les codes d'erreurs seront spécifiés dans l'index d'erreurs.

**contenu du paquet :**
 * code d'erreur (*code*)

Paquet début tour
-----------------

RoundDiceChoice
^^^^^^^^^^^^^^^
(*envoyé par le client*).
Paquet indiquant au serveur que ce que le joueur a choisi de faire,
entre trois possibilités : ROLL_DICES = 0, JAIL_PAY = 1, JAIL_CARD = 2.
Seul le joueur dont c'est le tour peut envoyer ce paquet.

**contenu du paquet :**
 * id du joueur qui a choisi (*player_token*)
 * choice : int(enum(ROLL_DICES = 0, JAIL_PAY = 1, JAIL_CARD_CHANCE = 2, JAIL_CARD_COMMUNITY = 3))

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
 * id du joueur (*player_token*)
 * indiquer si c'est une case communautaire ou de chance (*is_community*)
 * id de la carte tirée aléatoirement (*card_id*)

PlayerUpdateBalance
^^^^^^^^^^^^^^^^^^^

Lorsque la somme d'argent d'un joueur modifie, ce paquet est envoyé à tout les clients pour les notifier de ce changement

**contenu du paquet :**
 * id du joueur dont la somme a changé (*player_token*)
 * Balance qu'il avait (*old_balance*)
 * Nouvelle balance (*new_balance*)
 * raison (*reason*)

PlayerPayDebt
^^^^^^^^^^^^^

Lorsqu'un joueur rembourse sa dette.

**contenu du paquet :**
 * id du joueur qui rembourse sa dette (*player_token*)
 * id ou vide (banque) du receveur (*player_to*)
 * montant de la dette remboursé (*amount*)
 * raison (str) (*reason*)

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

Paquet ActionStart
^^^^^^^^^^^^^^^^^^
Paquet envoyé par le serveur lorsque l'action tour démarre

*Ce paquet ne contient pas d'informations*

Paquet ActionEnd
^^^^^^^^^^^^^^^^
Paquet envoyé par client lorsque le joueur a effectué toutes ses actions.

**contenu du paquet**
 * id du joueur (*player_token*)

Paquet ActionTimeout
^^^^^^^^^^^^^^^^^^^^
Paquet envoyé par serveur lorsque le joueur a envoyé ActionEnd ou le timeout des actions est passé.

*ce paquet ne contient pas d'informations*

Paquet ActionExchange
^^^^^^^^^^^^^^^^^^^^^
Paquet envoyé par client lorsque le joueur veut effectuer un échange avec un autre joueur.

**contenu du paquet**
 * id du joueur (*player_token*)

Paquet ActionExchangePlayerSelect
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

paquet *envoyé par le client* pour la sélection du joueur avec qui on veut faire l'échange. Ce paquet est relayé à tout les clients pour qu'ils puissent suivre l'échange en direct.

**contenu du paquet**
 * id du joueur (*player_token*)
 * id du joueur selectionné (*selected_player_token*)


Paquet ActionExchangeTradeSelect
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ce paquet *envoyé par le client* spécifie la nature de l'échange. Il est relayé à tout les clients pour qu'ils puissent suivre l'échange en direct.

**contenu du paquet**
 * id du joueur (*player_token*)
 * type d'échange (*exchange_type*) (PROPERTY = 0, MONEY = 1, LEAVE_JAIL_COMMUNITY_CARD = 2, LEAVE_JAIL_CHANCE_CARD = 3)
 * valeur (id propriété etc) (*value*)
 * concerne le joueur selectionné ou pas (*update_affects_recipient*)


Paquet ActionExchangeSend
^^^^^^^^^^^^^^^^^^^^^^^^^

Ce paquet *envoyé par le client* est envoyé pour notifier qu'un échange va avoir lieu. Il est relayé à tout les clients pour
qu'ils puissent suivre l'échange en direct. Ceux qui ne sont pas concernés par l'échange recevront juste les paquets et montreront
 les animations nécessaire.

**contenu du paquet**
  * id du joueur (*player_token*)

Paquet ActionExchangeDecline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par le client* si le joueur avec qui l'échange est censé être effectué refuse. Le paquet est relayé à tout le monde.

**contenu du paquet**
  * id du joueur (*player_token*)

Paquet ActionExchangeCounter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ce paquet est *envoyé par le client* dans le cas où le joueur avec qui l'échange est censé être effectué veut effectuer une contre proposition.
Le paquet est relayé à tout le monde. Pour la renégotiation de l'échange, le paquet *ActionExchangeTradeSelect* est utilisé.

**contenu du paquet**
  * id du joueur (*player_token*)

Paquet ActionExchangeAccept
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Paquet envoyé *par le client* si le joueur avec qui l'échange est censé être effectué accepte. Le paquet est relayé à tout le monde.

**contenu du paquet**
  * id du joueur (*player_token*)

Paquet ActionExchangeCancel
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ce paquet est envoyé à tout le monde. Il notifie à tout les clients que l'échange a été annulé, soit parce que les ressources de la personne
a qui l'échange était demandé ne sont pas suffisantes, soit par demande du joueur qui a initialisé l'échange.

**contenu du paquet :**
 * Personne qui a annulé l'échange (*player_token*)

Paquet ActionExchangeTransfer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ce paquet est envoyé à tout le monde. Il notifie à tout les clients qu'un transfert de carte ou de propriété a été effectué.
Le joueur "player_token" donne une propriété au joueur "to".

**contenu du paquet :**
 * id joueur envoyeur (*player_token*)
 * id joueur receveur (*player_to*)
 * Type (PROPERTY = 0, CARD = 1) (*transfer_type*)
 * valeur, donc id d'une propriété/carte (*value*)

Paquet ActionAuctionProperty
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par le client* lorsqu'un joueur souhaite vendre une propriété aux enchères.

**contenu du paquet :**
 * id du joueur (*player_token*)
 * Seulement envoyé par le serveur, id de la propriété mis en enchère (*property_id*)
 * enchère de base (*min_bid*)

Paquet AuctionBid
^^^^^^^^^^^^^^^^^

Paquet envoyé *par un client* lorsque ce dernier enchérit durant une enchères. Ce paquet est relayé à tout les clients pour
qu'ils puissent suivre l'enchère en direct.

**contenu du paquet :**
 * id du joueur (*player_token*)
 * enchère proposée (*bid*)

Paquet AuctionEnd
^^^^^^^^^^^^^^^^^

Paquet envoyé à tout le monde si personne n'enchérit pendant un tour d'enchères. Il signifie la fin des enchères.

**contenu du paquet :**
 * id du gagnant (*player_token*)
 * montant que le joueur a enchérit (*highest_bid*)
 * temps restant pour le round action (*remaining_time*)

Paquet ActionBuyProperty
^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par un client* lorsque le joueur veut acheter une propriété.

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id de la maison (*property_id*)

Paquet ActionBuyPropertySucceed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé à tout le monde si l'achat de la propriété par un joueur est un succès.

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id de la maison (*property_id*)

Paquet ActionMortgageProperty
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par un client* lorsque le joueur veut hypothéquer une propriété.

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id de la maison (*property_id*)

Paquet ActionMortgageSucceed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé à tout le monde lorsqu'une hypothèque a été couronné de succès.

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id de la maison (*property_id*)

Paquet ActionUnmortgageProperty
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par un client* lorsque le joueur veut déshypothéquer une propriété.

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id de la maison (*property_id*)

Paquet ActionUnmortgageSucceed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé à tout le monde lorsqu'un déshypothèquement a été couronné de succès.

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id de la maison (*property_id*)


Paquet ActionBuyHouse
^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par un client* lorsque le joueur veut acheter une maison

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id de la maison (*property_id*)

Paquet ActionBuyHouseSucceed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé à tout le monde lorsque l'achat d'une maison a été couronné de succès.

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id de la maison (*property_id*)

Paquet ActionSellHouse
^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé *par un clinet* lorsque le joueur veut vendre une maison.

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id de la maison (*property_id*)

Paquet ActionSellHouseSucceed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Paquet envoyé à tout le monde lorsque la vente d'une maison a été couronné de succès.

**contenu du paquet :**
 * id du joueur (*player_token*)
 * id de la maison (*property_id*)

Paquet GameWin
^^^^^^^^^^^^^^

Paquet envoyé à tout le monde lorsque le jeu a été gagné

**contenu du paquet :**
 * id du joueur qui a gagné (*player_token*)

Paquet GameEnd
^^^^^^^^^^^^^^

Paquet envoyé à tout le monde lorsque tous les clients doivent quitter la room.
(il s'arrête après 3/4 secondes)

*ce paquet ne contient pas d'informations*

Paquets internes
----------------

Paquets internes au serveur (non liés au cli-serv)

InternalInitConnection
^^^^^^^^^^^^^^^^^^^^^^
Paquet envoyé lorsque un joueur se connecte.

**contenu du paquet :**
 * id du joueur (*player_token*)

InternalLobbyDisconnect
^^^^^^^^^^^^^^^^^^^^^^^

Paquet interne pour gérer la déconnexion  d'un joueur dans le lobby. Ce paquet retire le joueur de la
salle d'attente dans laquelle il est.

**contenu du paquet :**
 * id du joueur (*player_token*)