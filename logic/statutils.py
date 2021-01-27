import time
from typing import List

from data.dbmodel import Note, Review


def prepareDeckDataPie(notes: List[Note]):
    maturity = {
        "New": 0,
        "Young": 0,
        "Adult": 0,
        "Old" :0
    }
    for note in notes:
        diff = note.n_last_r - note.n_next_r  # how mature is the note?
        oneDay = 60 * 60 * 24
        if diff <= oneDay:
            maturity["New"] += 1
        elif oneDay < diff <= oneDay * 7:
            maturity["Young"] += 1
        elif oneDay * 7 < diff <= oneDay * 31:
            maturity["Adult"] += 1
        else:
            maturity["Old"] += 1

    return maturity.items()


def prepareDeckDataBar(notes: List[Note]):
    daysFromNow = {}
    oneDay = 60 * 60 * 24
    for note in notes:
        waitTimeDays = max(0, note.n_next_r - int(time.time())) // oneDay
        if waitTimeDays in daysFromNow:
            daysFromNow[waitTimeDays] += 1
        else:
            daysFromNow[waitTimeDays] = 1
    preparedData = []
    for i in range(0, 31):
        if i in daysFromNow:
            preparedData.append(daysFromNow[i])
        else:
            preparedData.append(0)
    return preparedData


def prepareNoteDataPie(reviews: List[Review]):
    data = {}
    for review in reviews:
        ease = review.r_ease
        if ease in data:
            data[ease] += 1
        else:
            data[ease] = 1

    return map(lambda t: (str(t[0]), t[1]), data.items())