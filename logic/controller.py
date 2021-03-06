import json
import time

import sqlalchemy.orm
from sqlalchemy import and_

from data.consts import CARD_FRONT_TEMPLATE, CARD_BACK_TEMPLATE
from logic import batchutils
from logic.statutils import prepareDeckDataPie, prepareDeckDataBar, prepareNoteDataPie
from logic.studysession import StudySession
from data.dbmodel import Card, Deck, Note, Review
from views.views import CardFormView, MainWindowView, CardListView, ErrorMessage, InfoMessage, LayoutEditorView, \
    NoteFormView, DeckListView, DeckFormView, NoteBrowserView, ExportFormView, ImportFormView, DeckStatsView, \
    NoteStatsView
from data import dbmodel as dbm


class Controller:
    """
    Controller manages the windows used by the app.
    """
    def __init__(self):
        self._mainWindow = MainWindowView()
        self._session: sqlalchemy.orm.Session = dbm.Session()
        self._studySession: StudySession = StudySession()
        # signals
        self._mainWindow.signalManageCards.connect(self.openCardList)
        self._mainWindow.signalManageDecks.connect(self.openDeckList)
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
        self._mainWindow.signalBatchImport.connect(self._onBatchImport)
        self._mainWindow.signalBatchExport.connect(self._onBatchExport)
        # init
        self.openMainDeckList()

    # MAIN WINDOW

    def openMainDeckList(self):
        """Updates deck list and opens it"""
        self._studySession.reset()
        self._mainWindow.setPage(0)
        self._mainWindow.updateDecksList([(deck.d_id, deck.d_name) for deck in self._session.query(Deck).all()])

    def openMainDetails(self, d_id: int):
        """Updates detail page and opens it"""
        self.prepareStudySession(d_id)
        if not self._studySession.isActive():
            self.openMainDeckList()
        else:
            deck = self._studySession.getDeck()
            notesTotalCount = self._session.query(Note).filter_by(d_id=deck.d_id).count()  # type: ignore
            self._mainWindow.updateDeckDetails(deck.d_name, notesTotalCount, self._studySession.getLen())  # type: ignore
            self._mainWindow.setPage(1)

    def openMainFlashcard(self, displayFront: bool):
        """Opens flashcard page and updates it"""
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
        """Prepares study session by loading deck data"""
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

    def _onDeckClicked(self, d_id: int):
        """Triggered when user select deck from the main window"""
        deck = self._session.query(Deck).filter_by(d_id=d_id).first()
        if deck:
            self.openMainDetails(deck.d_id)

    def _onDetailsStats(self):
        """Triggered when user opens stats on the main window"""
        if not self._studySession.isActive():
            return
        deck = self._studySession.getDeck()
        if deck:
            self.display_deck_stats(deck.d_id)

    def _onDetailsQuickAdd(self):
        """Triggered when user presses Quick Add button"""
        if self._studySession.isActive():
            self.addNote(self._studySession.getDeck().d_id)

    def _onFlashcardClose(self):
        """Triggered when user closes flashcard"""
        if self._studySession.isActive():
            self.openMainDetails(self._studySession.getDeck().d_id)

    def _onFlashcardShow(self):
        """Triggered when user presses the Show button for flashcard"""
        self.openMainFlashcard(displayFront=False)

    def _onFlashcardRate(self, rate: int):
        """Triggered when user rates a flashcard"""
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
        """Triggered when user opens stats for a flashcard"""
        if not self._studySession.isActive():
            return
        note = self._studySession.peekNextNote()
        if note:
            self.display_flashcard_stats(note.n_id)

    # IMPORT / EXPORT

    def _onBatchImport(self):
        """Triggered when user wants to open import"""
        importForm = ImportFormView()
        importForm.signalImport.connect(lambda: self.batchImport(importForm))
        importForm.exec()

    def batchImport(self, importForm: ImportFormView):
        """Handle import"""
        path = importForm.getData()
        if not path:
            error = ErrorMessage("Please choose which file to import")
            error.exec()
        else:
            try:
                with open(path, "r") as file:
                    data = file.read()
                    result = batchutils.convertFromJson(data)
            except:  # noinspection PyBroadException
                error = ErrorMessage("Malformed file")
                error.exec()
                return
            if not result:
                error = ErrorMessage("Malformed file")
                error.exec()
            else:
                card, deck, notes = result
                card.c_name = f"{card.c_name}_{int(time.time())}"
                self._session.add(card)
                self._session.commit()
                deck.d_name = f"{deck.d_name}_{int(time.time())}"
                deck.c_id = card.c_id
                self._session.add(deck)
                self._session.commit()
                for note in notes:
                    note.d_id = deck.d_id
                    self._session.add(note)
                self._session.commit()
                self._mainWindow.updateDecksList([(deck.d_id, deck.d_name) for deck in self._session.query(Deck).all()])

    def _onBatchExport(self):
        """Triggered when user wants to export"""
        decks = self._session.query(Deck.d_name).all()
        exportForm = ExportFormView(list(map(lambda t: t[0], decks)))
        exportForm.signalExport.connect(lambda: self.batchExport(exportForm))
        exportForm.exec()

    def batchExport(self, exportForm: ExportFormView):
        """Handle export"""
        deckName, filePath = exportForm.getData()
        if not deckName or not filePath:
            return
        deck = self._session.query(Deck).filter_by(d_name=deckName).first()
        if not deck:
            return
        card = self._session.query(Card).filter_by(c_id=deck.c_id).first()
        if not card:
            return
        notes = self._session.query(Note).filter_by(d_id=deck.d_id).all()
        jsonOut = batchutils.convertToJson(card, deck, notes)
        if not jsonOut:
            error = ErrorMessage("Data appears to be corrupted")
            error.exec()
        else:
            with open(filePath, "w") as file:
                file.write(jsonOut)
            info = InfoMessage("Exported deck to file successfully")
            info.exec()

    # TOOLBAR MANAGE CARDS

    def openCardList(self):
        """Open card list dialog"""
        cards: list[Card] = self._session.query(Card)
        cardList = CardListView([card.c_name for card in cards], [card.c_id for card in cards])
        cardList.signalAdd.connect(lambda: self.addCard(cardList))
        cardList.signalDelete.connect(lambda: self.deleteCard(cardList))
        cardList.signalEdit.connect(lambda: self.editCard(cardList))
        cardList.signalLayout.connect(lambda: self.editLayout(cardList))
        cardList.exec()

    def addCard(self, cardList: CardListView):
        """Open add card dialog from card list"""
        cardForm = CardFormView("New Card", ["Field1", "Field2"], True)
        cardForm.signalCancel.connect(cardForm.close)
        cardForm.signalSave.connect(lambda: self.addCardSave(cardList, cardForm))
        cardForm.exec()

    def addCardSave(self, cardList: CardListView, cardForm: CardFormView):
        """Save data from Add card dialog, refresh card list"""
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
            newCard = Card(c_name=name, c_fields=json.dumps(fields), c_layout_f=CARD_FRONT_TEMPLATE, c_layout_b=CARD_BACK_TEMPLATE)
            print(newCard.c_id)
            self._session.add(newCard)
            self._session.commit()
            info = InfoMessage("Added new card")
            newCards = self._session.query(Card.c_id, Card.c_name).all()
            cardList.refresh(list(map(lambda t: t[1], newCards)), list(map(lambda t: t[0], newCards)))
            info.exec()

    def deleteCard(self, cardList: CardListView):
        """Delete card from card list, refresh card list"""
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
        """Edit card from card list"""
        if not cardList.selectedIdx > -1:
            pass
        else:
            target = cardList.ids[cardList.selectedIdx]
            canEditFields = True if self._session.query(Deck).filter_by(c_id=target).count() == 0 else False
            card = self._session.query(Card).filter_by(c_id=target).one()
            editForm = CardFormView(card.c_name, json.loads(card.c_fields), canEditFields)
            editForm.signalCancel.connect(editForm.close)
            editForm.signalSave.connect(lambda: self.editCardSave(card.c_id, cardList, editForm))
            editForm.exec()

    def editCardSave(self, cid: int, cardList, cardForm):
        """Edit card from card, save card list"""
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
        """Edit layout of a card from card list"""
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
        """Edit layout of a card from card list, save layout"""
        card = self._session.query(Card).filter_by(c_id=cid).one()
        card.c_layout_f, card.c_layout_b = layoutEditor.getContents()
        self._session.commit()
        info = InfoMessage("Saved layout")
        info.exec()

    # TOOLBAR MANAGE DECKS

    def openDeckList(self):
        """Open deck list dialog"""
        decks: list[Deck] = self._session.query(Deck)
        deckList = DeckListView([deck.d_name for deck in decks], [deck.d_id for deck in decks])
        deckList.signalAdd.connect(lambda: self.addDeck(deckList))
        deckList.signalDelete.connect(lambda: self.deleteDeck(deckList))
        deckList.signalEdit.connect(lambda: self.editDeck(deckList))
        deckList.signalNotes.connect(lambda: self.viewNotes(deckList))
        deckList.exec()

    def addDeck(self, deckList: DeckListView):
        """Add deck new deck dialog"""
        cards = [card.c_name for card in self._session.query(Card).all()]
        if len(cards) == 0:
            error = ErrorMessage("Please add card templates first")
            error.exec()
        else:
            deckForm = DeckFormView("New Deck", cards)
            deckForm.signalCancel.connect(deckForm.close)
            deckForm.signalSave.connect(lambda: self.addDeckSave(deckList, deckForm))
            deckForm.exec()

    def addDeckSave(self, deckList: DeckListView, deckForm: DeckFormView):
        """Add new deck, refresh deck list"""
        deckName, cardName = deckForm.getData()
        card = self._session.query(Card).filter_by(c_name=cardName).first()
        if deckName == "" or cardName == "":
            error = ErrorMessage("Fields cannot be empty")
            error.exec()
        elif self._session.query(Deck).filter_by(d_name=deckName).first():
            error = ErrorMessage("Deck name must be unique")
            error.exec()
        elif not card:
            error = ErrorMessage(f"Couldn't find card {cardName}")
            error.exec()
        else:
            newDeck = Deck(d_name=deckName, c_id=card.c_id)
            self._session.add(newDeck)
            self._session.commit()
            info = InfoMessage("Added new deck")
            newDecks = self._session.query(Deck.d_id, Deck.d_name).all()
            deckList.refresh(list(map(lambda t: t[1], newDecks)), list(map(lambda t: t[0], newDecks)))
            self._mainWindow.updateDecksList([(deck.d_id, deck.d_name) for deck in self._session.query(Deck).all()])
            info.exec()

    def editDeck(self, deckList: DeckListView):
        """Edit deck from deck list"""
        selected = deckList.getSelectedId()
        if selected == -1:
            return
        deck = self._session.query(Deck).filter_by(d_id=selected).one()
        cards = list(map(lambda t: t[0], self._session.query(Card.c_name).all()))
        editForm = DeckFormView(deck.d_name, cards)
        editForm.signalCancel.connect(editForm.close)
        editForm.signalSave.connect(lambda: self.editDeckSave(deck.d_id, deckList, editForm))
        editForm.exec()

    def editDeckSave(self, d_id: int, deckList: DeckListView, editForm: DeckFormView):
        """Edit deck from deck list, refresh decks in deck list"""
        deckName, cardName = editForm.getData()
        nameCheck = self._session.query(Deck).filter(and_(Deck.d_name==deckName, Deck.d_id!=d_id)).first()
        if deckName == "" or cardName == "":
            error = ErrorMessage(f"Fields cannot be empty.")
            error.exec()
        elif nameCheck:
            error = ErrorMessage(f"Deck with this name already exists.")
            error.exec()
        else:
            deck = self._session.query(Deck).filter_by(d_id=d_id).one()
            newCard = self._session.query(Card.c_id, Card.c_fields).filter_by(c_name=cardName).one()
            if deck.c_id != newCard.c_id:  # edited card
                oldCard = self._session.query(Card.c_fields).filter_by(c_id=deck.c_id).one()
                oldCardFieldsLen = len(json.loads(oldCard[0]))
                newCardFieldsLen = len(json.loads(newCard[1]))
                if oldCardFieldsLen != newCardFieldsLen:
                    error = ErrorMessage(f"This card is incompatible, {newCardFieldsLen} fields instead of {oldCardFieldsLen}")
                    error.exec()
                    return
                else:
                    deck.c_id = newCard[0]
            deck.d_name = deckName
            self._session.commit()
            info = InfoMessage("Saved new deck settings.")
            newDecks = self._session.query(Deck.d_id, Deck.d_name).all()
            deckList.refresh(list(map(lambda t: t[1], newDecks)), list(map(lambda t: t[0], newDecks)))
            self._mainWindow.updateDecksList([(deck.d_id, deck.d_name) for deck in self._session.query(Deck).all()])
            info.exec()

    def deleteDeck(self, deckList: DeckListView):
        """Delete deck from deck list, refresh deck list"""
        selected = deckList.getSelectedId()
        if selected == -1:
            return
        deck = self._session.query(Deck).filter_by(d_id=selected).one()
        self._session.query(Note).filter_by(d_id=deck.d_id).delete()
        self._session.delete(deck)
        self._session.commit()
        info = InfoMessage("Deleted a deck")
        newDecks = self._session.query(Deck.d_id, Deck.d_name).all()
        deckList.refresh(list(map(lambda t: t[1], newDecks)), list(map(lambda t: t[0], newDecks)))
        self._mainWindow.updateDecksList([(deck.d_id, deck.d_name) for deck in self._session.query(Deck).all()])
        self._mainWindow.setPage(0)
        info.exec()

    def viewNotes(self, deckList: DeckListView):
        """View notes of a deck from deck list"""
        selected = deckList.getSelectedId()
        if selected == -1:
            return
        deck = self._session.query(Deck).filter_by(d_id=selected).one()
        card = self._session.query(Card).filter_by(c_id=deck.c_id).one()
        notes = self._session.query(Note.n_id, Note.n_data).filter_by(d_id=selected).all()
        notesData = list(map(lambda t: (t[0], json.loads(t[1])), notes))
        noteBrowser = NoteBrowserView(deck.d_name, json.loads(card.c_fields), notesData)
        noteBrowser.signalAdd.connect(lambda: self.viewNotesAdd(card, deck, noteBrowser))
        noteBrowser.signalEdit.connect(lambda: self.viewNotesEdit(card, deck, noteBrowser))
        noteBrowser.signalDelete.connect(lambda: self.viewNotesDelete(card, deck, noteBrowser))
        noteBrowser.exec()

    def viewNotesAdd(self, card: Card, deck: Deck, noteBrowser: NoteBrowserView):
        """View notes of a deck from deck list, add new note"""
        noteForm = NoteFormView(deck.d_name, json.loads(card.c_fields))
        noteForm.signalCancel.connect(noteForm.close)
        noteForm.signalSave.connect(lambda: self.viewNotesAddSave(card, deck, noteBrowser, noteForm))
        noteForm.exec()

    def viewNotesAddSave(self, card: Card, deck: Deck, noteBrowser: NoteBrowserView, noteForm: NoteFormView):
        """Add new note, refresh note browser"""
        data = noteForm.getData()
        if "" in data:
            error = ErrorMessage("Field cannot be empty.")
            error.exec()
        else:
            newNote = Note(n_data=json.dumps(data), d_id=deck.d_id)
            self._session.add(newNote)
            self._session.commit()
            info = InfoMessage("Added new note.")
            notes = self._session.query(Note.n_id, Note.n_data).filter_by(d_id=deck.d_id).all()
            notesData = list(map(lambda t: (t[0], json.loads(t[1])), notes))
            noteBrowser.refresh(json.loads(card.c_fields), notesData)
            info.exec()
            noteForm.close()

    def viewNotesEdit(self, card: Card, deck: Deck, noteBrowser: NoteBrowserView):
        """Edit note from note browser"""
        selected = noteBrowser.getSelectedId()
        note = self._session.query(Note).filter_by(n_id=selected).one()
        noteForm = NoteFormView(deck.d_name, json.loads(card.c_fields), json.loads(note.n_data))
        noteForm.signalCancel.connect(noteForm.close)
        noteForm.signalSave.connect(lambda: self.viewNotesEditSave(card, deck, noteBrowser, noteForm))
        noteForm.exec()

    def viewNotesEditSave(self, card: Card, deck: Deck, noteBrowser: NoteBrowserView, noteForm: NoteFormView):
        """Edit note from note browser, refresh note browser view"""
        selected = noteBrowser.getSelectedId()
        data = noteForm.getData()
        if "" in data:
            error = ErrorMessage("Field cannot be empty")
            error.exec()
        else:
            note = self._session.query(Note).filter_by(n_id=selected).one()
            note.n_data = json.dumps(data)
            self._session.commit()
            info = InfoMessage("Saved edited note.")
            notes = self._session.query(Note.n_id, Note.n_data).filter_by(d_id=deck.d_id).all()
            notesData = list(map(lambda t: (t[0], json.loads(t[1])), notes))
            noteBrowser.refresh(json.loads(card.c_fields), notesData)
            info.exec()
            noteForm.close()

    def viewNotesDelete(self, card: Card, deck: Deck, noteBrowser: NoteBrowserView):
        """Delete note from note browser, refresh note browser"""
        selected = noteBrowser.getSelectedId()
        note = self._session.query(Note).filter_by(n_id=selected).one()
        self._session.delete(note)
        self._session.commit()
        info = InfoMessage("Deleted note")
        notes = self._session.query(Note.n_id, Note.n_data).filter_by(d_id=deck.d_id).all()
        notesData = list(map(lambda t: (t[0], json.loads(t[1])), notes))
        noteBrowser.refresh(json.loads(card.c_fields), notesData)
        info.exec()

    # ADD NOTE FORM

    def addNote(self, d_id: int):
        """Add note"""
        deck = self._session.query(Deck).filter_by(d_id=d_id).one()
        card = self._session.query(Card).filter_by(c_id=deck.c_id).one()
        form = NoteFormView(deck.d_name, json.loads(card.c_fields))
        form.signalCancel.connect(form.close)
        form.signalSave.connect(lambda: self.addNoteSave(form, d_id))
        form.exec()

    def addNoteSave(self, form: NoteFormView, d_id: int):
        """Add note and save"""
        data = form.getData()
        if "" in data:
            error = ErrorMessage("Field can't be empty")
            error.exec()
        else:
            self._session.add(Note(n_data=json.dumps(data), d_id=d_id))
            self._session.commit()
            info = InfoMessage("Added new note")
            info.exec()
            form.close()
            self.openMainDetails(d_id) # refresh ui

    # STATS
    def display_deck_stats(self, d_id):
        """Display deck stats for a given deck"""
        notes = self._session.query(Note).filter_by(d_id=d_id).all()
        dataPie = prepareDeckDataPie(notes)
        dataBar = prepareDeckDataBar(notes)
        window = DeckStatsView(dataPie, dataBar)
        window.exec()

    def display_flashcard_stats(self, n_id):
        """Display note stats for a given note"""
        reviews = self._session.query(Review).filter_by(n_id=n_id).all()
        dataPie = prepareNoteDataPie(reviews)
        window = NoteStatsView(dataPie)
        window.exec()