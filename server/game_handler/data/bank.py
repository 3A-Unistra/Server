class Bank:
    nb_house: int
    nb_hotel: int

    def __init__(self, nb_house: int, nb_hotel: int):
        self.nb_house = nb_house
        self.nb_hotel = nb_hotel

    def has_houses(self) -> bool:
        """
        :return: Bank has houses
        """
        return self.nb_house > 0

    def has_hotels(self) -> bool:
        """
        :return: Bank has hotels
        """
        return self.nb_hotel > 0

    def buy_house(self):
        self.nb_house -= 1

    def buy_hotel(self):
        self.nb_hotel -= 1

    def sell_house(self):
        self.nb_house += 1

    def sell_hotel(self):
        self.nb_hotel += 1
