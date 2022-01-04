#! python3
# Character Encoding: UTF-8

'''
# tewlPDF
# a simple PDF manipulator with PyQt5 GUI

# Shortcut to recompile resources:
# pyrcc5 resources.qrc -o resources.py
'''

# TODO: add tooltips
# TODO: add slicing
# TODO: add cutting

# TODO: actual, proper, clean OOP - Command DD?

# Classes=windows: dragdrop, list, it's done

##############################################################################################################################

# Import all the required stuff
# Keeping it tidy, it gets up bloated anyway
from PyQt5.QtWidgets import (
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QWidget,
    QMainWindow,
    QApplication,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QInputDialog,
    QAbstractItemView,
    QFileDialog
)

from PyQt5.QtGui import QFont, QIcon, QFontDatabase
from PyQt5.QtCore import Qt
from pathlib import Path
from pikepdf import PasswordError, Pdf
import sys
import os
import time
import resources

# Required for auto-py-to-exe to work properly


def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Define some (semi) constans
APP_NAME = 'tewlPDF'
APP_VERSION = '0.3.1 dev WIP'  # TODO: 1.0 when done!
APP_AUTHOR = 'tewlwolow'

# Messages
STRING_DROP = 'DROP IT HERE'
STRING_DROP_FAIL = 'Didn\'t drop any PDF files.\nTry again!'
STRING_FINISHED = 'It\'s done!'

# STYLESHEET_CONTAINER finals
FONT_MAIN = ['Darker Grotesque', 55]
FONT_LIST = ['Zen Maru Gothic', 14]

# Define stylesheets
# Using paths from resource_rc cuz, again, auto-py-to-exe
STYLESHEET_CONTAINER = """
	MAIN_WINDOW {
		background-image: url(:tewl_container);
	}
"""
STYLESHEET_MAIN = 'background-image: url(:/tewl_bg_main); border: 2px solid black; border-radius: 50px; color: rgb(0, 0, 0)'
STYLESHEET_LIST = 'background-image: url(:/tewl_bg_main); border: 2px solid black; border-radius: 50px; color: rgb(0, 0, 0)'
STYLESHEET_HIGHLIGHT = 'background-image: url(:/tewl_bg_main); border: 2px solid black; border-radius: 50px; color: rgba(0, 0, 139, 130)'

# Define window structure


class FINISHED_SCREEN(QWidget):
    def __init__(self, main):
        super().__init__()

        def restart():
            main.finishedScreen.hide()
            main.welcomeScreen.show()

        self.layout = QGridLayout()
        self.text = QLabel(STRING_FINISHED)
        self.layout.addWidget(self.text)
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setFont(QFont(*FONT_MAIN))
        self.text.setStyleSheet(STYLESHEET_MAIN)
        self.backButton = QPushButton('Again')
        self.backButton.setFont(QFont(*FONT_LIST))
        self.backButton.clicked.connect(restart)
        self.layout.addWidget(self.backButton)
        self.setLayout(self.layout)


class FILELIST_SCREEN(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.layout = QHBoxLayout(self)

        self.listWidget = QListWidget(self)
        self.listWidget.setDragDropMode(
            QAbstractItemView.InternalMove)
        self.listWidget.setDragEnabled(True)
        self.listWidget.setFont(QFont(*FONT_LIST))
        self.listWidget.setStyleSheet(STYLESHEET_LIST)

        self.setLayout(self.layout)

    def setFiles(self, files):
        self.__files = files

    def getFiles(self):
        return self.__files

    def purgeFiles(self):
        self.__files = []

    def dragEnterEvent(self, event):
        # Bounce off mouse clicks
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        addedFiles = [u.toLocalFile() for u in event.mimeData().urls()
                      if u.toLocalFile().endswith('.pdf')]

        if len(addedFiles):
            newFiles = self.__files + addedFiles
            self.clearData()
            self.setFiles(newFiles)
            self.parseFiles()

    # Purge data between window switches
    def clearData(self):
        self.purgeFiles()
        self.listWidget.clear()
        self.layout.removeWidget(
            self.optionsWidget)
        self.optionsWidget.deleteLater()

    # Bounce back to welcome screen
    def goBack(self):
        self.hide()
        self.clearData()
        mainWindow.welcomeScreen.text.setText(STRING_DROP)
        mainWindow.welcomeScreen.show()

    # Define merging operation
    def mergePDF(self):
        # Get files once again; user might have reordered those
        self.__files = [str(self.listWidget.item(i).text())
                        for i in range(self.listWidget.count())]
        self.hide()
        saveDialog = QFileDialog.getSaveFileName(
            self,
            'Save merged PDF',
            'Merged Document.pdf',
            'Portable Document Files (*.pdf)')

        path = str(saveDialog[0])
        # If user chooses 'Cancel' on file dialog, bounce back to options window
        if not path:
            self.hide()
            self.show()
            return

        pdf = Pdf.new()
        for f in self.__files:
            # Fairly cumbersome loop for handling errors due to encrypted files
            while True:
                try:
                    src = Pdf.open(f)
                    break
                except PasswordError:
                    fileName = Path(f)
                    text, ok = QInputDialog.getText(
                        self, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                    if ok and text:
                        self.PDFpassword = str(text)
                        try:
                            src = Pdf.open(
                                f, password=self.PDFpassword)
                            break
                        except PasswordError:
                            continue
                    else:
                        self.goBack()
                        return

            pdf.pages.extend(src.pages)

        pdf.save(path)
        pdf.close()

        self.clearData()
        mainWindow.finishedScreen.show()

    # Define splitting operation
    def splitPDF(self):
        self.__files = [str(self.listWidget.item(i).text())
                        for i in range(self.listWidget.count())]
        self.hide()
        folderDialog = QFileDialog.getExistingDirectory(
            self, 'Select Folder')

        if not folderDialog:
            self.hide()
            self.show()
            return

        # Need a custom counter here in order not to end up overwriting the files
        n = 0
        for f in self.__files:
            while True:
                try:
                    src = Pdf.open(f)
                    break
                except PasswordError:
                    fileName = Path(f)
                    text, ok = QInputDialog.getText(
                        self, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                    if ok and text:
                        self.PDFpassword = str(text)
                        try:
                            src = Pdf.open(
                                f, password=self.PDFpassword)
                            break
                        except PasswordError:
                            continue
                    else:
                        self.goBack()
                        return
            for page in src.pages:
                dst = Pdf.new()
                dst.pages.append(page)
                path = str(folderDialog + '/' + f'{n:02d}.pdf')
                n += 1
                dst.save(path)
                dst.close()
            src.close()

        self.clearData()
        mainWindow.finishedScreen.show()

    def reversePDF(self):
        self.__files = [str(self.listWidget.item(i).text())
                        for i in range(self.listWidget.count())]
        self.hide()

        if len(self.__files) == 1:
            f = self.__files[0]
            fileName = Path(f)

            saveDialog = QFileDialog.getSaveFileName(
                self,
                'Save reversed PDF',
                fileName.stem + '_reversed',
                'Portable Document Files (*.pdf)')
            path = str(saveDialog[0])

            if not path:
                self.hide()
                self.show()
                return

            while True:
                try:
                    src = Pdf.open(f)
                    break
                except PasswordError:
                    text, ok = QInputDialog.getText(
                        self, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                    if ok and text:
                        self.PDFpassword = str(text)
                        try:
                            src = Pdf.open(
                                f, password=self.PDFpassword)
                            break
                        except PasswordError:
                            continue
                    else:
                        self.goBack()
                        return

            dst = Pdf.new()
            dst.pages.extend(src.pages)
            dst.pages.reverse()
            dst.save(path)
            dst.close()
            src.close()

        else:
            folderDialog = QFileDialog.getExistingDirectory(
                self, 'Select Folder')

            if not folderDialog:
                self.hide()
                self.show()
                return

            for f in self.__files:
                fileName = Path(f)
                while True:
                    try:
                        src = Pdf.open(f)
                        break
                    except PasswordError:
                        text, ok = QInputDialog.getText(
                            self, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                        if ok and text:
                            self.PDFpassword = str(text)
                            try:
                                src = Pdf.open(
                                    f, password=self.PDFpassword)
                                break
                            except PasswordError:
                                continue
                        else:
                            self.goBack()
                            return

                path = str(folderDialog + '/' +
                           f'{fileName.stem}_reversed.pdf')
                dst = Pdf.new()
                dst.pages.extend(src.pages)
                dst.pages.reverse()
                dst.save(path)
                dst.close()
                src.close()

        self.clearData()
        mainWindow.finishedScreen.show()

    # Create list objects for each valid file

    def parseFiles(self):
        for f in self.__files:
            i = QListWidgetItem(
                (QIcon(':/tewl_logo')), f, self.listWidget)

        if len(self.__files):
            # Advance if provided with valid files
			# Update doesn't work. Bummer
            self.hide()
            self.show()

            # Construct window content
            self.optionsWidget = QWidget(self)
            self.optionsWidget.layout = QVBoxLayout(
                self.optionsWidget)
            self.optionsWidget.setLayout(
                self.optionsWidget.layout)
            self.layout.addWidget(self.listWidget)
            self.layout.addWidget(
                self.optionsWidget)

            # Add buttons based on file context
            if len(self.__files) == 1:
                self.optionsWidget.splitButton = QPushButton(
                    'Split PDF')
                self.optionsWidget.splitButton.setFont(
                    QFont(*FONT_LIST))
                self.optionsWidget.splitButton.clicked.connect(
                    self.splitPDF)
                self.optionsWidget.splitButton.setToolTip(
                    'Split file into single-page PDFs')
                self.optionsWidget.layout.addWidget(
                    self.optionsWidget.splitButton)

                self.optionsWidget.reverseButton = QPushButton(
                    'Reverse PDF')
                self.optionsWidget.reverseButton.setFont(
                    QFont(*FONT_LIST))
                self.optionsWidget.reverseButton.clicked.connect(
                    self.reversePDF)
                self.optionsWidget.reverseButton.setToolTip(
                    'Reverse page order')
                self.optionsWidget.layout.addWidget(
                    self.optionsWidget.reverseButton)

                self.optionsWidget.backButton = QPushButton(
                    'Back')
                self.optionsWidget.backButton.setFont(
                    QFont(*FONT_LIST))
                self.optionsWidget.backButton.clicked.connect(
                    self.goBack)
                self.optionsWidget.backButton.setToolTip(
                    'Go back to welcome screen')
                self.optionsWidget.layout.addWidget(
                    self.optionsWidget.backButton)

            else:
                self.optionsWidget.mergeButton = QPushButton(
                    'Merge PDFs')
                self.optionsWidget.mergeButton.setFont(
                    QFont(*FONT_LIST))
                self.optionsWidget.mergeButton.clicked.connect(
                    self.mergePDF)
                self.optionsWidget.mergeButton.setToolTip(
                    'Merge files into one PDF')
                self.optionsWidget.layout.addWidget(
                    self.optionsWidget.mergeButton)

                self.optionsWidget.splitButton = QPushButton(
                    'Split PDFs')
                self.optionsWidget.splitButton.setFont(
                    QFont(*FONT_LIST))
                self.optionsWidget.splitButton.clicked.connect(
                    self.splitPDF)
                self.optionsWidget.splitButton.setToolTip(
                    'Split files into single-page PDFs')
                self.optionsWidget.layout.addWidget(
                    self.optionsWidget.splitButton)

                self.optionsWidget.reverseButton = QPushButton(
                    'Reverse PDFs')
                self.optionsWidget.reverseButton.setFont(
                    QFont(*FONT_LIST))
                self.optionsWidget.reverseButton.clicked.connect(
                    self.reversePDF)
                self.optionsWidget.reverseButton.setToolTip(
                    'Reverse page order')
                self.optionsWidget.layout.addWidget(
                    self.optionsWidget.reverseButton)

                self.optionsWidget.backButton = QPushButton(
                    'Back')
                self.optionsWidget.backButton.setFont(
                    QFont(*FONT_LIST))
                self.optionsWidget.backButton.clicked.connect(
                    self.goBack)
                self.optionsWidget.backButton.setToolTip(
                    'Go back to welcome screen')
                self.optionsWidget.layout.addWidget(
                    self.optionsWidget.backButton)


class WELCOME_SCREEN(QWidget):
    def __init__(self):
        super().__init__()

        # Define the contents of the welcome screen
        self.setWindowTitle('DragDrop')
        self.setAcceptDrops(True)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.text = QLabel(STRING_DROP)
        self.layout.addWidget(self.text)
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setStyleSheet(STYLESHEET_MAIN)
        self.text.setFont(QFont(*FONT_MAIN))

    def dragEnterEvent(self, event):
        # Define highlight style
        self.text.setStyleSheet(STYLESHEET_HIGHLIGHT)

        # Bounce off mouse clicks
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        # Go back to main style
        self.text.setStyleSheet(STYLESHEET_MAIN)

    # Get dropped files, pass data to filelist class and hide this window
    def dropEvent(self, event):
        self.text.setStyleSheet(STYLESHEET_MAIN)
        files = [u.toLocalFile() for u in event.mimeData().urls()
                 if u.toLocalFile().endswith('.pdf')]

        if len(files):
            mainWindow.filelistScreen.setFiles(files)
            mainWindow.filelistScreen.parseFiles()
            self.hide()
        else:
            self.text.setText(STRING_DROP_FAIL)
            self.update()


# Define main window
class MAIN_WINDOW(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_gui()

    def init_gui(self):
        self.setWindowTitle(APP_NAME + ' v.' +
                            APP_VERSION + ' by ' + APP_AUTHOR)
        self.setStyleSheet(STYLESHEET_CONTAINER)
        self.resize(1024, 768)
        self.setWindowIcon(QIcon(':/tewl_logo'))
        self.window = QWidget()
        self.layout = QGridLayout()
        self.setCentralWidget(self.window)
        self.window.setLayout(self.layout)

        # Define and show welcome screen
        self.welcomeScreen = WELCOME_SCREEN()
        self.layout.addWidget(self.welcomeScreen)
        self.welcomeScreen.show()

        # Define filelist screen
        self.filelistScreen = FILELIST_SCREEN()
        self.layout.addWidget(self.filelistScreen)
        self.filelistScreen.hide()

        # Define finished screen
        self.finishedScreen = FINISHED_SCREEN(self)
        self.layout.addWidget(self.finishedScreen)
        self.finishedScreen.hide()


# Initialise the programme
if __name__ == '__main__':
    app = QApplication([])
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton)

    QFontDatabase.addApplicationFont(':/tewl_h_font')
    QFontDatabase.addApplicationFont(':/tewl_p_font')

    mainWindow = MAIN_WINDOW()
    mainWindow.show()

    sys.exit(app.exec_())
