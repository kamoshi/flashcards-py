import json
import time

import sqlalchemy.orm
from sqlalchemy import and_

from logic.studysession import StudySession
from data.dbmodel import Card, Deck, Note, Review
from views.views import CardFormView, MainWindowView, CardListView, ErrorMessage, InfoMessage, LayoutEditorView, \
    NoteFormView
from data import dbmodel as dbm


class Controller:
    def __init__(self):
        self._mainWindow = MainWindowView()
        self._session: sqlalchemy.orm.Session = dbm.Session()
        self._studySession: StudySession = StudySession()
        # signals
        self._mainWindow.signalManageCards.connect(self.openCardList)
        self._mainWindow.signalOpenDeck.connect(self._onDeckClicked)
        self._mainWindow.signalDetailsCancel.connect(self.openMainDeckList)
        self._mainWindow.signalDetailsStats.connect(self._onDetailsStats)
        self._mainWindow.signalDetailsQuickAdd.connect(self._onDetailsQuickAdd)
        self._mainWindow.signalDetailsStudy.connect(lambda: self.openMainFlashcard(displayFront=True))
        self._mainWindow.signalFlashcardClose.connect(self._onFlashcardClose)
        self._mainWindow.signalFlashcardStats.connect(self._onFlashcardStats)
        self._mainWindow.signalFlashcardShow.connect(self._onFlashcardShow)
        self._mainWindow.signalFlashcardEasy.connect(lambda: self._onFlashcardRate(rate=5))
        self._mainWindow.signalFlashcardOK.connect(lambda: self._onFlashcardRate(rate=3))
        self._mainWindow.signalFlashcardHard.connect(lambda: self._onFlashcardRate(rate=1))
        # init
        self.openMainDeckList()

    # MAIN WINDOW

    def openMainDeckList(self):
        self._studySession.reset()
        self._mainWindow.setPage(0)
        self._mainWindow.updateDecksList([(deck.d_id, deck.d_name) for deck in self._session.query(Deck).all()])

    def openMainDetails(self, d_id: int):
        self.prepareStudySession(d_id)
        if not self._studySession.isActive():
            self.openMainDeckList()
        else:
            deck = self._studySession.getDeck()
            notesTotalCount = self._session.query(Note).filter_by(d_id=deck.d_id).count()  # type: ignore
            self._mainWindow.updateDeckDetails(deck.d_name, notesTotalCount, self._studySession.getLen())  # type: ignore
            self._mainWindow.setPage(1)

    def openMainFlashcard(self, displayFront: bool):
        if not self._studySession.isFinished():
            deck = self._studySession.getDeck()
            card = self._studySession.getCard()
            note = self._studySession.peekNextNote()
            fields, values = json.loads(card.c_fields), json.loads(note.n_data)  # type: ignore
            # noinspection PyTypeChecker
            self._mainWindow.updateFlashcard(deck.d_name, card.c_layout_f, card.c_layout_b, list(zip(fields, values)), displayFront)  # type: ignore
            self._mainWindow.setPage(2)
        elif self._studySession.isActive():
            self.openMainDetails(self._studySession.getDeck().d_id)  # type: ignore
        else:
            self.openMainDeckList()

    def prepareStudySession(self, d_id: int):
        deck = self._session.query(Deck).filter_by(d_id=d_id).first()
        if not deck:
            self._studySession.reset()
            return
        card = self._session.query(Card).filter_by(c_id=deck.c_id).first()
        if not card:
            self._studySession.reset()
            return
        timeNow = int(time.time())
        notes = self._session.query(Note).filter(and_(Note.d_id == deck.d_id, Note.n_next_r <= timeNow)).all()
        self._studySession.fill(card, deck, notes)

    def _onDeckClicked(self, d_name: str):
        deck = self._session.query(Deck).filter_by(d_name=d_name).first()
        if deck:
            self.openMainDetails(deck.d_id)

    def _onDetailsStats(self):
        print("Details stats")
        # TODO: details stats

    def _onDetailsQuickAdd(self):
        if self._studySession.isActive():
            self.addNote(self._studySession.getDeck().d_id)

    def _onFlashcardClose(self):
        if self._studySession.isActive():
            self.openMainDetails(self._studySession.getDeck().d_id)

    def _onFlashcardShow(self):
        self.openMainFlashcard(displayFront=False)

    def _onFlashcardRate(self, rate: int):
        note = self._studySession.popNextNote()
        review = Review(r_ease=rate, n_id=note.n_id)
        self._session.add(review)
        last_r, next_r = note.n_last_r, note.n_next_r
        currentT = int(time.time())
        if last_r == 0 or next_r == 0:  # this is the first review
            note.n_last_r = max(currentT, 0)
            note.n_next_r = max((currentT + int(60*60 * (rate/3))), 0)
        else:
            note.n_last_r = currentT
            note.n_next_r = currentT + int((next_r-last_r) * (rate/3))
        self._session.commit()
        self.openMainFlashcard(displayFront=True)

    def _onFlashcardStats(self):
        print("Flashcard stats")
        # TODO: flashcard stats

    # TOOLBAR MANAGE CARDS

    def openCardList(self):
        cards: list[Card] = self._session.query(Card)
        cardList = CardListView([card.c_name for card in cards], [card.c_id for card in cards])
        cardList.addSignal.connect(lambda: self.addCard(cardList))
        cardList.deleteSignal.connect(lambda: self.deleteCard(cardList))
        cardList.editSignal.connect(lambda: self.editCard(cardList))
        cardList.layoutSignal.connect(lambda: self.editLayout(cardList))
        cardList.exec()

    def addCard(self, cardList: CardListView):
        cardForm = CardFormView("New Card", ["Field1", "Field2"], True)
        cardForm.cancelSignal.connect(cardForm.close)
        cardForm.saveSignal.connect(lambda: self.addCardSave(cardList, cardForm))
        cardForm.exec()

    def addCardSave(self, cardList: CardListView, cardForm: CardFormView):
        name, fields = cardForm.getFields()
        if name == "" or "" in fields:
            error = ErrorMessage("Fields cannot be empty")
            error.exec()
        elif len(fields) != len(set(fields)):
            error = ErrorMessage("Field names must be unique")
            error.exec()
        elif self._session.query(Card).filter_by(c_name=name).first():
            error = ErrorMessage("Card name must be unique")
            error.exec()
        else:
            newCard = Card(c_name=name, c_fields=json.dumps(fields))
            print(newCard.c_id)
            self._session.add(newCard)
            self._session.commit()
            info = InfoMessage("Added new card")
            newCards = self._session.query(Card.c_id, Card.c_name).all()
            cardList.refresh(list(map(lambda t: t[1], newCards)), list(map(lambda t: t[0], newCards)))
            info.exec()

    def deleteCard(self, cardList: CardListView):
        if not cardList.selectedIdx > -1:
            pass
        else:
            target = cardList.ids[cardList.selectedIdx]
            if self._session.query(Deck).filter_by(c_id=target).first():
                error = ErrorMessage("Cannot delete a card that is currently used")
                error.exec()
            else:
                card = self._session.query(Card).filter_by(c_id=target).one()
                self._session.delete(card)
                self._session.commit()
                newCards = self._session.query(Card.c_id, Card.c_name).all()
                cardList.refresh(list(map(lambda t: t[1], newCards)), list(map(lambda t: t[0], newCards)))
                info = InfoMessage("Deleted a card")
                info.exec()

    def editCard(self, cardList: CardListView):
        if not cardList.selectedIdx > -1:
            pass
        else:
            target = cardList.ids[cardList.selectedIdx]
            canEditFields = True if self._session.query(Deck).filter_by(c_id=target).count() == 0 else False
            card = self._session.query(Card).filter_by(c_id=target).one()
            editForm = CardFormView(card.c_name, json.loads(card.c_fields), canEditFields)
            editForm.cancelSignal.connect(editForm.close)
            editForm.saveSignal.connect(lambda: self.editCardSave(card.c_id, cardList, editForm))
            editForm.exec()

    def editCardSave(self, cid: int, cardList, cardForm):
        name, fields = cardForm.getFields()
        if name == "" or "" in fields:
            error = ErrorMessage("Fields cannot be empty")
            error.exec()
        elif len(fields) != len(set(fields)):
            error = ErrorMessage("Field names must be unique")
            error.exec()
        elif self._session.query(Card).filter(and_(Card.c_name == name, Card.c_id != cid)).first():
            error = ErrorMessage("Card name must be unique")
            error.exec()
        else:
            card = self._session.query(Card).filter_by(c_id=cid).one()
            card.c_name = name
            card.c_fields = json.dumps(fields)
            self._session.commit()
            info = InfoMessage("Edited a card")
            newCards = self._session.query(Card.c_id, Card.c_name).all()
            cardList.refresh(list(map(lambda t: t[1], newCards)), list(map(lambda t: t[0], newCards)))
            info.exec()

    def editLayout(self, cardList: CardListView):
        if not cardList.selectedIdx > -1:
            pass
        else:
            target = cardList.ids[cardList.selectedIdx]
            card = self._session.query(Card).filter_by(c_id=target).one()
            layoutFront = card.c_layout_f if card.c_layout_f else ""
            layoutBack = card.c_layout_b if card.c_layout_b else ""
            editForm = LayoutEditorView()
            editForm.setContents(layoutFront, layoutBack)
            editForm.cancelSignal.connect(editForm.close)
            editForm.saveSignal.connect(lambda: self.editLayoutSave(editForm, target))
            editForm.exec()

    def editLayoutSave(self, layoutEditor: LayoutEditorView, cid: int):
        card = self._session.query(Card).filter_by(c_id=cid).one()
        card.c_layout_f, card.c_layout_b = layoutEditor.getContents()
        self._session.commit()
        info = InfoMessage("Saved layout")
        info.exec()

    # TOOLBAR MANAGE DECKS
    # TODO: Add, Delete decks; view notes

    # ADD NOTE FORM
    def addNote(self, d_id: int):
        deck = self._session.query(Deck).filter_by(d_id=d_id).one()
        card = self._session.query(Card).filter_by(c_id=deck.c_id).one()
        form = NoteFormView(deck.d_name, json.loads(card.c_fields))
        form.signalCancel.connect(form.close)
        form.signalSave.connect(lambda: self.addNoteSave(form, d_id))
        form.exec()

    def addNoteSave(self, form: NoteFormView, d_id: int):
        data = form.getData()
        if "" in data:
            error = ErrorMessage("Field can't be empty")
            error.exec()
        else:
            self._session.add(Note(n_data=json.dumps(data), d_id=d_id))
            info = InfoMessage("Added new note")
            info.exec()
            form.close()
            self.openMainDetails(d_id) # refresh ui