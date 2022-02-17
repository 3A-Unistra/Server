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
Paquet envoyé lorsque le joueur sort de prison

**contenu du paquet :**
 * id du joueur allant en prison (*id_player*)

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
 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

PAquet envoyé *par un clinet* lorsque le joueur veut vendre une maison.

**contenu du paquet :**
 * id du joueur (*id_player*)
 * id de la maison (*id_house*)

 Paquet ActionSellHouseSucceed
 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

 Paquet envoyé à tout le monde lorsque la vente d'une maison a été couronné de succès.

 **contenu du paquet :**
  * id du joueur (*id_player*)
  * id de la maison (*id_house*)
