import time
from typing import Tuple, List

from PySide2 import QtCore
from PySide2.QtCore import QFile, QIODevice, QObject, Signal
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLineEdit, QVBoxLayout, QPushButton, QMessageBox, QWidgetItem, QListWidget, QDialog, \
    QPlainTextEdit, QTextBrowser, QStackedWidget, QLabel, QHBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, \
    QFileDialog

from data.consts import HTML_TEMPLATE
from data.dbmodel import Note, Review
from views.classes.stat_windows import DeckStatsWindow, NoteStatsWindow


def load_ui(path: str):
    """Loads .ui file"""
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
    """Display info box popup"""
    def __init__(self, message: str):
        self.msgBox = QMessageBox()
        self.msgBox.setIcon(QMessageBox.Information)
        self.msgBox.setText("Info")
        self.msgBox.setInformativeText(message)
        self.msgBox.setStandardButtons(QMessageBox.Ok)

    def exec(self):
        self.msgBox.exec_()


class ErrorMessage:
    """Display error box popup"""
    def __init__(self, message: str):
        self.msgBox = QMessageBox()
        self.msgBox.setIcon(QMessageBox.Warning)
        self.msgBox.setText("Error")
        self.msgBox.setInformativeText(message)
        self.msgBox.setStandardButtons(QMessageBox.Ok)

    def exec(self):
        self.msgBox.exec_()


class MainWindowView(QObject):
    signalOpenDeck = Signal(int)

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
        self.signalManageDecks = self._window.actionManageDecks.triggered
        self.signalBatchImport = self._window.actionBatchImport.triggered
        self.signalBatchExport = self._window.actionBatchExport.triggered
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

    def updateDecksList(self, decks: List[Tuple[int, str]]):
        for _ in range(self._containerDecks.count()):
            self._containerDecks.takeAt(0).widget().deleteLater()
        for (d_id, d_name) in decks:
            def _scope_fix(_d_id, _d_name):
                button = QPushButton(d_name)
                # noinspection PyUnresolvedReferences
                button.clicked.connect(lambda: self.signalOpenDeck.emit(_d_id))  # type: ignore
                self._containerDecks.addWidget(button)
            _scope_fix(d_id, d_name)

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
        self.signalDelete = self._buttonDelete.clicked
        self.signalEdit = self._buttonEdit.clicked
        self.signalLayout = self._buttonLayout.clicked
        self.signalAdd = self._buttonAdd.clicked
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
        self.signalCancel = self._window.buttonCancel.clicked
        self.signalSave = self._window.buttonSave.clicked
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
        self._labelDeck.setText(f"Adding to: {deck}")
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


class DeckListView:
    def __init__(self, names: List[str], ids: List[int]):
        self._template = "views/templates/deck_list.ui"
        self._window = load_ui(self._template)
        self._ids = ids[:]
        self._selectedIdx = -1
        # references
        self._listDecks: QListWidget = self._window.listDecks
        self._buttonDelete: QPushButton = self._window.buttonDelete
        self._buttonEdit: QPushButton = self._window.buttonEdit
        self._buttonNotes: QPushButton = self._window.buttonNotes
        self._buttonAdd: QPushButton = self._window.buttonAdd
        # signals
        self.signalDelete = self._buttonDelete.clicked
        self.signalEdit = self._buttonEdit.clicked
        self.signalNotes = self._buttonNotes.clicked
        self.signalAdd = self._buttonAdd.clicked
        # init
        self._setButtonsEnabled(False)
        self._listDecks.itemClicked.connect(self._selectedItem)
        self.refresh(names, ids)

    def _setButtonsEnabled(self, mode: bool) -> None:
        self._buttonDelete.setEnabled(mode)
        self._buttonEdit.setEnabled(mode)
        self._buttonNotes.setEnabled(mode)

    def _selectedItem(self) -> None:
        items = self._listDecks.selectedItems()
        if len(items) != 1:
            self._selectedIdx = -1
            self._setButtonsEnabled(False)
        else:
            self._selectedIdx = self._listDecks.indexFromItem(items[0]).row()
            self._setButtonsEnabled(True)

    def getSelectedId(self) -> int:
        if self._selectedIdx > -1:
            return self._ids[self._selectedIdx]
        else:
            return -1

    def refresh(self, deckNames: List[str], deckIds: List[int]) -> None:
        self._selectedIdx = -1
        self._setButtonsEnabled(False)
        self._listDecks.clear()
        for card in deckNames:
            self._listDecks.addItem(card)
        self._ids = deckIds[:]

    def close(self) -> None:
        self._window.close()

    def exec(self) -> None:
        self._window.exec_()


class DeckFormView:
    def __init__(self, deckName: str, cardName: List[str]):
        self._template = "views/templates/deck_form.ui"
        self._window = load_ui(self._template)
        # references
        self._entryDeckName: QLineEdit = self._window.entryDeckName
        self._comboTemplate: QComboBox = self._window.comboTemplate
        self._buttonCancel: QPushButton = self._window.buttonCancel
        self._buttonSave: QPushButton = self._window.buttonSave
        # signals
        self.signalCancel = self._buttonCancel.clicked
        self.signalSave = self._buttonSave.clicked
        # init
        self._entryDeckName.setText(deckName)
        self._comboTemplate.addItems(cardName)

    def getData(self) -> Tuple[str, str]:
        return self._entryDeckName.text(), str(self._comboTemplate.currentText())

    def close(self):
        self._window.close()

    def exec(self):
        self._window.exec_()


class NoteBrowserView:
    def __init__(self, deck: str, fields: List[str], data: List[Tuple[int, List[str]]]):
        self._template = "views/templates/note_browser.ui"
        self._window: QDialog = load_ui(self._template)
        self._data: List[Tuple[int, List[str]]] = []
        self._selectedIdx = -1
        # references
        self._labelDeckName: QLabel = self._window.labelDeckName
        self._tableNotes: QTableWidget = self._window.tableNotes
        self._buttonDelete: QPushButton = self._window.buttonDelete
        self._buttonEdit: QPushButton = self._window.buttonEdit
        self._buttonAdd: QPushButton = self._window.buttonAdd
        # signals
        self.signalDelete = self._buttonDelete.clicked
        self.signalEdit = self._buttonEdit.clicked
        self.signalAdd = self._buttonAdd.clicked
        self._tableNotes.clicked.connect(self._onClicked)
        # init
        self._labelDeckName.setText(deck)
        self._tableNotes.setSelectionBehavior(QTableWidget.SelectRows)
        self.refresh(fields, data)
        self._setButtonsEnabled(False)

    def _onClicked(self):
        self._selectedIdx = self._tableNotes.currentRow()
        self._setButtonsEnabled(True)

    def _setButtonsEnabled(self, state: bool):
        self._buttonDelete.setEnabled(state)
        self._buttonEdit.setEnabled(state)

    def refresh(self, fields: List[str], data: List[Tuple[int, List[str]]]):
        if not data:
            return
        self._data = list(map(lambda t: (t[0], t[1].copy()), data))  # deep copy
        self._tableNotes.clear()
        self._tableNotes.setColumnCount(len(fields))
        self._tableNotes.setRowCount(len(self._data))
        self._tableNotes.setHorizontalHeaderLabels(fields)
        for r in range(len(data)):
            n_id, n_data = data[r]
            for c in range(len(n_data)):
                item = QTableWidgetItem(n_data[c])
                item.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
                self._tableNotes.setItem(r, c, item)
        self._setButtonsEnabled(False)
        self._selectedIdx = -1

    def getSelectedId(self) -> int:
        if self._selectedIdx == -1:
            return -1
        else:
            return self._data[self._selectedIdx][0]

    def close(self):
        self._window.close()

    def exec(self):
        self._window.exec_()


class ExportFormView:
    def __init__(self, decks: List[str]):
        self._template = "views/templates/export_form.ui"
        self._window: QDialog = load_ui(self._template)
        self._chosen = ("", "")
        # references
        self._comboDeckSelector: QComboBox = self._window.comboDeckSelector
        self._entryFileLocation: QLineEdit = self._window.entryFileLocation
        self._buttonFileLocation: QPushButton = self._window.buttonFileLocation
        self._buttonCancel: QPushButton = self._window.buttonCancel
        self._buttonExport: QPushButton = self._window.buttonExport
        # signals
        self._buttonCancel.clicked.connect(self.close)
        self._buttonFileLocation.clicked.connect(self._onChooseFile)
        self.signalExport = self._buttonExport.clicked
        # init
        self._entryFileLocation.setReadOnly(True)
        self._comboDeckSelector.addItems(decks)

    def _onChooseFile(self):
        fileDialog = QFileDialog()
        self._chosen = fileDialog.getSaveFileName(filter="deck file (*.deck)")
        if self._chosen:
            self._entryFileLocation.setText(self._chosen[0])
        else:
            self._entryFileLocation.setText("Please choose export location")

    def getData(self) -> Tuple[str, str]:
        return str(self._comboDeckSelector.currentText()), self._chosen[0]

    def close(self):
        self._window.close()

    def exec(self):
        self._window.exec_()


class ImportFormView:
    def __init__(self):
        self._template = "views/templates/import_form.ui"
        self._window: QDialog = load_ui(self._template)
        self._chosen = ("", "")
        # references
        self._buttonChooseFile: QPushButton = self._window.buttonChooseFile
        self._entryFileLocation: QLineEdit = self._window.entryFileLocation
        self._buttonCancel: QPushButton = self._window.buttonCancel
        self._buttonImport:QPushButton = self._window.buttonImport
        # signals
        self._buttonChooseFile.clicked.connect(self._onChooseFile)
        self._buttonCancel.clicked.connect(self.close)
        self.signalImport = self._buttonImport.clicked
        # init
        self._entryFileLocation.setReadOnly(True)

    def _onChooseFile(self):
        fileDialog = QFileDialog()
        self._chosen = fileDialog.getOpenFileName(filter="deck file (*.deck)")
        if self._chosen:
            self._entryFileLocation.setText(self._chosen[0])
        else:
            self._entryFileLocation.setText("Please choose export location")

    def getData(self) -> str:
        return self._chosen[0]

    def close(self):
        self._window.close()

    def exec(self):
        self._window.exec_()


class DeckStatsView:
    def __init__(self, pieData, barData):
        self._window: QDialog = DeckStatsWindow()
        self.setDataPie(pieData)
        self.setDataBar(barData)

    def setDataPie(self, pieData):
        self._window.setPieChartData(pieData)

    def setDataBar(self, barData):
        self._window.setBarChartData(barData)

    def close(self):
        self._window.close()

    def exec(self):
        self._window.exec_()


class NoteStatsView:
    def __init__(self, pieData):
        self._window: QDialog = NoteStatsWindow()
        self.setNoteDataPie(pieData)

    def setNoteDataPie(self, pieData):
        self._window.setPieChartData(pieData)

    def close(self):
        self._window.close()

    def exec(self):
        self._window.exec_()