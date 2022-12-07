from dataCollection.actualData.countExits import countTotals
from dataCollection.airports.SanDiego import SanDiego
from dataCollection.airports.Chicago import Chicago


color = False
size = True
show = False
table = True
debug = False


dateList = ["11-22", "11-23", "11-25", "11-27", "11-28"]


def getResultsSAN():
    airport = SanDiego()

    dateList = [
        "SAN_11_22",
        "SAN_11_23",
        "SAN_11_25",
        "SAN_11_27",
        "SAN_11_28",
        "SAN_11_29",
        "SAN_11_30",
        "SAN_12_01",
        "SAN_12_02",
        "SAN_12_03",
    ]
    arrivalList = []
    departureList = []

    for date in dateList:
        arrivalList.append(f"results/{date}/arrivals")
        departureList.append(f"results/{date}/departures")

    countTotals(
        arrivalList,
        airport,
        False,
        color,
        size,
        show,
        table,
        debug,
        date=None,
        title="Arrivals",
        filename="allSANarrivals",
    )
    countTotals(
        departureList,
        airport,
        True,
        color,
        size,
        show,
        table,
        debug,
        date=None,
        title="Departures",
        filename="allSANdepartures",
    )


def getResultsORD():
    airport = Chicago()

    dateList = [
        "ORD_11_22",
        "ORD_11_23",
        "ORD_11_25",
        "ORD_11_27",
        "ORD_11_28",
        "ORD_11_29",
        "ORD_11_30",
        "ORD_12_01",
        "ORD_12_02",
        "ORD_12_03",
        "ORD_12_06",
    ]
    arrivalList = []
    departureList = []

    for date in dateList:
        arrivalList.append(f"results/{date}/arrivals")
        departureList.append(f"results/{date}/departures")

    countTotals(
        arrivalList,
        airport,
        False,
        color,
        size,
        show,
        table,
        debug,
        date=None,
        title="Arrivals",
        filename="allORDarrivals",
    )
    countTotals(
        departureList,
        airport,
        True,
        color,
        size,
        show,
        table,
        debug,
        date=None,
        title="Departures",
        filename="allORDdepartures",
    )


getResultsSAN()
print()
getResultsORD()
