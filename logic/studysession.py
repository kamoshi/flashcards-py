from typing import Optional, List

from data.dbmodel import Note, Deck, Card


class StudySession:
    def __init__(self):
        self._currentCard: Optional[Card] = None
        self._currentDeck: Optional[Deck] = None
        self._notesToStudy: list[Note] = []

    def reset(self) -> None:
        self._currentCard = None
        self._currentDeck = None
        self._notesToStudy = []

    def fill(self, card: Card, deck: Deck, notes: List[Note]) -> None:
        self._currentCard = card
        self._currentDeck = deck
        self._notesToStudy = notes[::-1]

    def isActive(self) -> bool:
        return self._currentDeck is not None and self._currentCard is not None

    def isFinished(self) -> bool:
        return self._notesToStudy == []

    def peekNextNote(self) -> Note:
        return self._notesToStudy[-1]

    def popNextNote(self) -> Note:
        return self._notesToStudy.pop()

    def getCard(self) -> Optional[Card]:
        return self._currentCard

    def getDeck(self) -> Optional[Deck]:
        return self._currentDeck

    def getLen(self) -> int:
        return len(self._notesToStudy)
