import json
from typing import List, Tuple, Optional

from data.dbmodel import Card, Deck, Note


def convertToJson(card: Card, deck: Deck, notes: List[Note]) -> str:
    if not deck.c_id == card.c_id:
        return ""
    fieldCount = len(json.loads(card.c_fields))
    outputDict = {
        "card" : {
            "c_name": card.c_name,
            "c_layout_f": card.c_layout_f,
            "c_layout_b": card.c_layout_b,
            "c_fields": card.c_fields,
        },
        "deck" : {
            "d_name": deck.d_name
        },
    }
    noteList = []
    for note in notes:
        dataCount = len(json.loads(note.n_data))
        if dataCount != fieldCount or note.d_id != deck.d_id:
            return ""
        noteDict = {
            "n_data": note.n_data
        }
        noteList.append(noteDict)
    outputDict["notes"] = noteList
    return json.dumps(outputDict)


def convertFromJson(jsonData: str) -> Optional[Tuple[Card, Deck, List[Note]]]:
    data = json.loads(jsonData)

    if "card" not in data or "deck" not in data or "notes" not in data:
        return None

    cData = data["card"]
    if "c_name" not in cData or "c_layout_f" not in cData or "c_layout_b" not in cData or "c_fields" not in cData:
        return None
    card = Card(c_name=cData["c_name"], c_layout_f=cData["c_layout_f"], c_layout_b=cData["c_layout_b"], c_fields=cData["c_fields"])

    fieldCount = len(json.loads(card.c_fields))

    dData = data["deck"]
    if "d_name" not in dData:
        return None
    deck = Deck(d_name=dData["d_name"])

    nList = data["notes"]
    notes: List[Note] = []
    for nData in nList:
        if "n_data" not in nData or len(json.loads(nData["n_data"])) != fieldCount:
            return None
        note = Note(n_data=nData["n_data"])
        notes.append(note)

    return card, deck, notes