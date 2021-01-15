from typing import Tuple, List

from PySide2.QtCore import QFile, QIODevice, QObject, Signal
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLineEdit, QVBoxLayout, QPushButton, QMessageBox, QWidgetItem, QListWidget, QDialog, \
    QPlainTextEdit, QTextBrowser, QStackedWidget, QLabel, QHBoxLayout

from data.consts import HTML_TEMPLATE


def load_ui(path: str):
    ui_file = QFile(path)
    if not ui_file.open(QIODevice.ReadOnly):
        print("Cannot open {}: {}".format(path, ui_file.errorString()))
    loader = QUiLoader()
    window = loader.load(ui_file)
    ui_file.close()
    if not window:
        print(loader.errorString())
    return window


class InfoMessage:
    def __init__(self, message: str):
        self.msgBox = QMessageBox()
        self.msgBox.setIcon(QMessageBox.Information)
        self.msgBox.setText("Info")
        self.msgBox.setInformativeText(message)
        self.msgBox.setStandardButtons(QMessageBox.Ok)

    def exec(self):
        self.msgBox.exec_()


class ErrorMessage:
    def __init__(self, message: str):
        self.msgBox = QMessageBox()
        self.msgBox.setIcon(QMessageBox.Warning)
        self.msgBox.setText("Error")
        self.msgBox.setInformativeText(message)
        self.msgBox.setStandardButtons(QMessageBox.Ok)

    def exec(self):
        self.msgBox.exec_()


class MainWindowView(QObject):
    signalOpenDeck = Signal(str)

    def __init__(self):
        super().__init__()
        self._template = "views/templates/main_window.ui"
        self._window = load_ui(self._template)
        self._stackedWidget: QStackedWidget = self._window.stackedWidget
        # Pages
        # main page
        self._containerDecks: QVBoxLayout = self._window.containerDecks
        # details page
        self._labelDeckName: QLabel = self._window.labelDeckName
        self._labelTotalNotes: QLabel = self._window.labelTotalNotes
        self._labelNotesToStudy: QLabel = self._window.labelNotesToStudy
        self._buttonDetailsCancel: QPushButton = self._window.buttonDetailsCancel
        self._buttonDetailsStats: QPushButton = self._window.buttonDetailsStats
        self._buttonDetailsQuickAdd: QPushButton = self._window.buttonDetailsQuickAdd
        self._buttonDetailsStudy: QPushButton = self._window.buttonDetailsStudy
        # flashcard page
        self._labelFlashcardName: QLabel = self._window.labelFlashcardName
        self._buttonFlashcardStats: QPushButton = self._window.buttonFlashcardStats
        self._buttonFlashcardClose: QPushButton = self._window.buttonFlashcardClose
        self._flashcardDisplay: QTextBrowser = self._window.flashcardDisplay
        self._buttonFlashcardShow: QPushButton = self._window.buttonFlashcardShow
        self._buttonFlashcardHard: QPushButton = self._window.buttonFlashcardHard
        self._buttonFlashcardOK: QPushButton = self._window.buttonFlashcardOK
        self._buttonFlashcardEasy: QPushButton = self._window.buttonFlashcardEasy
        # Signals
        # toolbar
        self.signalManageCards = self._window.actionManageCards.triggered
        self.manageDecksSignal = self._window.actionManageDecks.triggered
        self.manageNotesSignal = self._window.actionManageNotes.triggered
        # details page
        self.signalDetailsCancel = self._buttonDetailsCancel.clicked
        self.signalDetailsStats = self._buttonDetailsStats.clicked
        self.signalDetailsQuickAdd = self._buttonDetailsQuickAdd.clicked
        self.signalDetailsStudy = self._buttonDetailsStudy.clicked
        # flashcard page
        self.signalFlashcardStats = self._buttonFlashcardStats.clicked
        self.signalFlashcardClose = self._buttonFlashcardClose.clicked
        self.signalFlashcardShow = self._buttonFlashcardShow.clicked
        self.signalFlashcardHard = self._buttonFlashcardHard.clicked
        self.signalFlashcardOK = self._buttonFlashcardOK.clicked
        self.signalFlashcardEasy = self._buttonFlashcardEasy.clicked
        # Init
        self._window.show()

    def setPage(self, idx: int):
        if idx not in [0, 1, 2]:
            return
        self._stackedWidget.setCurrentIndex(idx)

    # noinspection PyUnresolvedReferences
    def updateDecksList(self, decks: List[Tuple[int, str]]):
        for _ in range(self._containerDecks.count()):
            self._containerDecks.takeAt(0).widget().deleteLater()
        for (d_id, d_name) in decks:
            button = QPushButton(d_name)
            button.clicked.connect(lambda: self.signalOpenDeck.emit(button.text()))  # type: ignore
            self._containerDecks.addWidget(button)

    def updateDeckDetails(self, name: str, notesTotal: int, notesToLearn: int):
        self._labelDeckName.setText(name)
        self._labelTotalNotes.setText(f"Total notes: {notesTotal}")
        self._labelNotesToStudy.setText(f"Notes to study: {notesToLearn}")
        self._buttonDetailsStudy.setEnabled(notesToLearn > 0)

    def updateFlashcard(self, name: str, front: str, back: str, fields: Tuple[List[str], List[str]], displayFront: bool):
        self._labelFlashcardName.setText(name)
        front = front if front else ""
        back = back if back else ""
        for (field, value) in fields:  # fill fields with data
            front = front.replace(f"{{{{{field}}}}}", f"{value}")
            back = back.replace(f"{{{{{field}}}}}", f"{value}")
        if displayFront:
            full = HTML_TEMPLATE.replace("{{Body}}", front)
            self._buttonFlashcardEasy.setVisible(False)
            self._buttonFlashcardOK.setVisible(False)
            self._buttonFlashcardHard.setVisible(False)
            self._buttonFlashcardShow.setVisible(True)
        else:
            full = HTML_TEMPLATE.replace("{{Body}}", back.replace("{{FrontSide}}", front))
            self._buttonFlashcardEasy.setVisible(True)
            self._buttonFlashcardOK.setVisible(True)
            self._buttonFlashcardHard.setVisible(True)
            self._buttonFlashcardShow.setVisible(False)
        self._flashcardDisplay.setHtml(full)


class CardListView:
    def __init__(self, cards: List[str], ids: List[int]):
        self._window: QDialog = load_ui("views/templates/card_list.ui")
        self._buttonDelete: QPushButton = self._window.buttonDelete
        self._buttonEdit: QPushButton = self._window.buttonEdit
        self._buttonLayout: QPushButton = self._window.buttonLayout
        self._buttonAdd: QPushButton = self._window.buttonAdd
        self._listCards: QListWidget = self._window.listCards
        self._setButtonsEnabled(False)
        for card in cards:
            self._listCards.addItem(card)
        self.ids = ids
        self.selectedIdx = -1
        self.deleteSignal = self._buttonDelete.clicked
        self.editSignal = self._buttonEdit.clicked
        self.layoutSignal = self._buttonLayout.clicked
        self.addSignal = self._buttonAdd.clicked
        self._listCards.itemClicked.connect(self.selectedItem)

    def _setButtonsEnabled(self, mode: bool) -> None:
        self._buttonDelete.setEnabled(mode)
        self._buttonEdit.setEnabled(mode)
        self._buttonLayout.setEnabled(mode)

    def selectedItem(self) -> None:
        items = self._listCards.selectedItems()
        if len(items) != 1:
            self.selectedIdx = -1
            self._setButtonsEnabled(False)
        else:
            self.selectedIdx = self._listCards.indexFromItem(items[0]).row()
            self._setButtonsEnabled(True)

    def refresh(self, newCards: List[str], newIds: List[int]) -> None:
        self.selectedIdx = -1
        self._setButtonsEnabled(False)
        self._listCards.clear()
        for card in newCards:
            self._listCards.addItem(card)
        self.ids = newIds

    def exec(self):
        self._window.exec_()


class CardFormView:
    def __init__(self, name: str, fields: List[str], modFieldCount: bool):
        self._name = name
        self._fields = fields[:]
        self._template = "views/templates/card_form.ui"
        # views
        self._window: QDialog = load_ui(self._template)
        self._nameEdit: QLineEdit = self._window.nameEdit
        self._fieldContainer: QVBoxLayout = self._window.fieldContainer
        self._buttonDeleteField: QPushButton = self._window.buttonDeleteField
        self._buttonAddField: QPushButton = self._window.buttonAddField
        # init views
        self._nameEdit.setText(name)
        for field in self._fields:
            newFieldWidget = QLineEdit(field)
            self._fieldContainer.addWidget(newFieldWidget)
        if not modFieldCount:
            self._buttonAddField.setEnabled(False)
            self._buttonDeleteField.setEnabled(False)
        else:
            self._buttonAddField.clicked.connect(self.addField)
            self._buttonDeleteField.clicked.connect(self.deleteField)
        self.cancelSignal = self._window.buttonCancel.clicked
        self.saveSignal = self._window.buttonSave.clicked
        self._window.show()

    def deleteField(self):
        minimum = 2
        itemCount = self._fieldContainer.count()
        if itemCount > minimum:
            item: QWidgetItem = self._fieldContainer.itemAt(itemCount - 1)
            item.widget().deleteLater()
            self._fieldContainer.removeItem(item)
        else:
            error = ErrorMessage(f"Minimum fields ({minimum})")
            error.exec()

    def addField(self):
        maximum = 6
        if self._fieldContainer.count() < maximum:
            newFieldWidget = QLineEdit("")
            self._fieldContainer.addWidget(newFieldWidget)
        else:
            error = ErrorMessage(f"Maximum fields ({maximum})")
            error.exec()

    def getFields(self) -> Tuple[str, List[str]]:
        cardName = self._nameEdit.text()
        cardFields = [self._fieldContainer.itemAt(idx).widget().text() for idx in range(self._fieldContainer.count())]
        return cardName, cardFields

    def exec(self):
        self._window.exec_()

    def close(self):
        self._window.close()


class LayoutEditorView:
    def __init__(self):
        self._template = "views/templates/layout_editor.ui"
        self._window: QDialog = load_ui(self._template)
        # References
        self._textBoxFront: QPlainTextEdit = self._window.textBoxFront
        self._textBoxBack: QPlainTextEdit = self._window.textBoxBack
        self._htmlPreview: QTextBrowser = self._window.htmlPreview
        self._buttonCancel: QPushButton = self._window.buttonCancel
        self._buttonSave: QPushButton = self._window.buttonSave
        self._buttonFlip: QPushButton = self._window.buttonFlip
        self._buttonFlip.clicked.connect(self.flipNote)
        self._textBoxFront.textChanged.connect(self.loadPreview)
        self._textBoxBack.textChanged.connect(self.loadPreview)
        self.saveSignal = self._buttonSave.clicked
        self.cancelSignal = self._buttonCancel.clicked
        self.showFront = True

    def setContents(self, front: str, back: str) -> None:
        self._textBoxFront.setPlainText(front)
        self._textBoxBack.setPlainText(back)

    def getContents(self) -> Tuple[str, str]:
        return self._textBoxFront.toPlainText(), self._textBoxBack.toPlainText()

    def flipNote(self) -> None:
        self.showFront = not self.showFront
        self.loadPreview()

    def loadPreview(self) -> None:
        front = self._textBoxFront.toPlainText()
        if self.showFront:
            full = HTML_TEMPLATE.replace("{{Body}}", front)
        else:
            back = self._textBoxBack.toPlainText()
            full = HTML_TEMPLATE.replace("{{Body}}", back.replace("{{FrontSide}}", front))
        self._htmlPreview.setHtml(full)

    def exec(self) -> None:
        self._window.exec_()

    def close(self) -> None:
        self._window.close()


class NoteFormView:
    def __init__(self, deck: str, fields: List[str], values: List[str] = None):
        self._template = "views/templates/note_form.ui"
        self._window = load_ui(self._template)
        # references
        self._labelDeck: QLabel = self._window.labelDeck
        self._containerFields: QVBoxLayout = self._window.containerFields
        self._buttonCancel: QPushButton = self._window.buttonCancel
        self._buttonSave: QPushButton = self._window.buttonSave
        # signals
        self.signalSave = self._buttonSave.clicked
        self.signalCancel = self._buttonCancel.clicked
        # init
        self._labelDeck.setText(f"Adding to: f{deck}")
        self._dataFields: List[QLineEdit] = []
        for i in range(len(fields)):
            newLine = QHBoxLayout()
            newLabel = QLabel(fields[i])
            newEntry = QLineEdit(values[i] if values else None)
            newLine.addWidget(newLabel)
            newLine.addWidget(newEntry)
            self._containerFields.addLayout(newLine)
            self._dataFields.append(newEntry)

    def getData(self):
        return list(map(QLineEdit.text, self._dataFields))

    def close(self):
        self._window.close()

    def exec(self):
        self._window.exec_()