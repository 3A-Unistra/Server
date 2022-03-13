Fonctionnalités
---------------

Ping - Heartbeat
^^^^^^^^^^^^^^^^

Le concept derrière le ping est de pouvoir être sûr qu'une connexion client-serveur
n'a pas été fermée du côté client (sans qu'on s'en apperçoive).
Le timeout est fixé à 10 secondes, c'est à dire qu'après 10 secondes, si le serveur n'a pas reçu
de signe de vie du client, alors la connexion sera fermée.

Dans notre architecture, chaque joueur a un bool ping, ainsi qu'une datetime ping_timeout.

Lors de la connexion du joueur (AppletReady), le mécanisme se met en route.
Etape setup: On set alors le timeout sur 10 secondes et ping=False.

A chaque tick on vérifie si l'un des joueurs connectés a un timeout expiré.
Si c'est le cas on procède à la vérification de la variable ping.
Si cette dernière est négative, on ferme la connexion, sinon on retourne à l'étape setup.


Paquets internes
^^^^^^^^^^^^^^^^

Les paquets internes servent à communiquer entre le PlayerConsumer et le Game Engine.
Ils ne sortent jamais de ce cadre là, et si quelqu'un essaye d'envoyer un paquet du genre,
il sera directement refusé avant même d'arriver au game engine.

Connexion / déconnexion
^^^^^^^^^^^^^^^^^^^^^^^

Cette fonctionnalité est sûrement une des plus complexes de l'architecture.
On doit gèrer la connexion/déconnexion en pleine partie, ainsi que le remplacement par un bot.

Connexion
+++++++++

Important: si on se connecte, il faut être sûr que le bot n'a pas encore joué.
Encore à voir, si le joueur peut quand même effectuer des échanges après que le bot ait joué?

Déconnexion
+++++++++++

Si le joueur se déconnecte, alors que c'est son tour, il faut que le bot prenne le relais.

Il y'a plusieurs types de déconnexions : celles qui viennent du client, ou celles du serveur.

Lorsqu'un joueur est déconnecté côté serveur, il faut éviter de renvoyer un paquet dans
la fonction disconnect du PlayerConsumer.

Lorsqu'un joueur est déconnecté côté client, il faut envoyer un InternalPlayerDisconnect,
et dans ce cas gèrer la déconnexion dans le serveur à la réception de ce dernier.