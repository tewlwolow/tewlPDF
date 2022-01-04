#! python3
# Character Encoding: UTF-8

'''
# tewlPDF
# a simple PDF manipulator with PyQt5 GUI
'''

# TODO: add tooltips
# TODO: add slicing
# TODO: add cutting

# TODO: actual, proper, clean OOP - Command DD?

# Classes=windows: dragdrop, list, working, it's done

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

from PyQt5.QtGui import QFont, QIcon
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
STRING_WELCOME = 'Drop it here'
STRING_WELCOME_FAIL = 'Didn\'t drop any PDF files.\nTry again!'

# STYLESHEET_CONTAINER finals
FONT_MAIN = ['Campora', 43]
FONT_LIST = ['Linux Biolinum G', 12, QFont.Bold]

# Define stylesheets
# Using paths from resource_rc cuz, again, auto-py-to-exe
STYLESHEET_CONTAINER = """
    MAIN_WINDOW {
        background-image: url(:tewl_container); 
    }
"""
STYLESHEET_MAIN = 'background-image: url(:/tewl_bg_main); border: 2px solid black; color: rgb(0, 0, 0)'
STYLESHEET_LIST = 'background-image: url(:/tewl_bg_list); border: 2px solid black; color: rgb(0, 0, 0)'
STYLESHEET_HIGHLIGHT = 'background-image: url(:/tewl_bg_main); border: 2px solid black; color: rgba(0, 0, 139, 130)'

# Define window structure

class WELCOME_SCREEN(QWidget):
    def __init__(self, filelistScreen):
        super().__init__()

        # Define the contents of the welcome screen
        self.setWindowTitle('DragDrop')
        self.setAcceptDrops(True)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.text = QLabel(STRING_WELCOME)
        self.layout.addWidget(self.text)
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setStyleSheet(STYLESHEET_MAIN)
        self.text.setFont(QFont(*FONT_MAIN))
        self.show()

        # Catch the second screen and initialise it
        self.filelistScreen = filelistScreen
        self.filelistScreen.setAcceptDrops(True)
        self.filelistScreenLayout = QHBoxLayout(self.filelistScreen)

        # Create the list widget to hold filenames inside the second screen
        self.filelistScreen.listWidget = QListWidget(self.filelistScreen)
        self.filelistScreen.listWidget.setDragDropMode(
            QAbstractItemView.InternalMove)
        self.filelistScreen.listWidget.setDragEnabled(True)
        self.filelistScreen.listWidget.setFont(QFont(*FONT_LIST))
        self.filelistScreen.listWidget.setStyleSheet(STYLESHEET_LIST)

        # Set the layout and hide for now
        self.filelistScreen.setLayout(self.filelistScreenLayout)
        self.filelistScreen.hide()

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

    # Main step to dynamically create data and define operations
    def dropEvent(self, event):

        # Catche dropped files
        self.files = [u.toLocalFile() for u in event.mimeData().urls()
                      if u.toLocalFile().endswith('.pdf')]

        # Create list objects for each valid file
        for f in self.files:
            i = QListWidgetItem(
                (QIcon(resource_path(':/tewl_logo'))), f, self.filelistScreen.listWidget)

        if len(self.files):
            # Advance if provided with valid files
            self.hide()
            self.filelistScreen.show()

            # Purge data between window switches
            def clearData():
                self.filelistScreen.listWidget.clear()
                self.filelistScreenLayout.removeWidget(self.filelistScreen.optionsWidget)
                self.filelistScreen.optionsWidget.deleteLater()

            # Bounce back to welcome screen
            def goBack():
                self.filelistScreen.hide()
                clearData()
                self.text.setText(STRING_WELCOME)
                self.text.setStyleSheet(STYLESHEET_MAIN)
                self.show()

            # Bounce back to welcome screen without clearing data after finished operation
            def reRun():
                self.backButton.deleteLater()
                self.filelistScreen.hide()
                self.text.setText(STRING_WELCOME)
                self.text.setStyleSheet(STYLESHEET_MAIN)
                self.show()

            # Show the finished operation window
            def finishedWindow():
                time.sleep(1)
                self.text.setText('It\'s done!')
                self.text.setStyleSheet(STYLESHEET_MAIN)
                self.backButton = QPushButton('Again')
                self.backButton.setFont(QFont(*FONT_LIST))
                self.backButton.clicked.connect(reRun)
                self.layout.addWidget(self.backButton)

            # Show window while operation is taking place
            def loaderWindow():
                self.filelistScreen.hide()
                self.text.setText('Working...')
                self.text.setStyleSheet(STYLESHEET_MAIN)
                self.show()

            # Define merging operation
            def mergePDF():
                # Get files once again; user might have reordered those
                self.files = [str(self.filelistScreen.listWidget.item(i).text())
                              for i in range(self.filelistScreen.listWidget.count())]
                loaderWindow()
                saveDialog = QFileDialog.getSaveFileName(
                    self,
                    'Save merged PDF',
                    'Merged Document.pdf',
                    'Portable Document Files (*.pdf)')

                path = str(saveDialog[0])
                # If user chooses 'Cancel' on file dialog, bounce back to options window
                if not path:
                    self.hide()
                    self.filelistScreen.show()
                    return
                clearData()

                pdf = Pdf.new()
                for f in self.files:
                    # Fairly cumbersome loop for handling errors due to encrypted files
                    while True:
                        try:
                            src = Pdf.open(f)
                            break
                        except PasswordError:
                            fileName = Path(f)
                            text, ok = QInputDialog.getText(
                                self.filelistScreen, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                            if ok and text:
                                self.PDFpassword = str(text)
                                try:
                                    src = Pdf.open(
                                        f, password=self.PDFpassword)
                                    break
                                except PasswordError:
                                    continue
                            else:
                                goBack()
                                return

                    pdf.pages.extend(src.pages)

                pdf.save(path)
                pdf.close()
                finishedWindow()

            # Define splitting operation
            def splitPDF():
                self.files = [str(self.filelistScreen.listWidget.item(i).text())
                              for i in range(self.filelistScreen.listWidget.count())]
                loaderWindow()
                folderDialog = QFileDialog.getExistingDirectory(
                    self, 'Select Folder')

                if not folderDialog:
                    self.hide()
                    self.filelistScreen.show()
                    return
                clearData()

                # Need a custom counter here in order not to end up overwriting the files
                n = 0
                for f in self.files:
                    while True:
                        try:
                            src = Pdf.open(f)
                            break
                        except PasswordError:
                            fileName = Path(f)
                            text, ok = QInputDialog.getText(
                                self.filelistScreen, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                            if ok and text:
                                self.PDFpassword = str(text)
                                try:
                                    src = Pdf.open(
                                        f, password=self.PDFpassword)
                                    break
                                except PasswordError:
                                    continue
                            else:
                                goBack()
                                return
                    for page in src.pages:
                        dst = Pdf.new()
                        dst.pages.append(page)
                        path = str(folderDialog + '/' + f'{n:02d}.pdf')
                        n += 1
                        dst.save(path)
                        dst.close()
                    src.close()

                finishedWindow()

            def reversePDF():
                self.files = [str(self.filelistScreen.listWidget.item(i).text())
                              for i in range(self.filelistScreen.listWidget.count())]
                loaderWindow()

                if len(self.files) == 1:
                    f = self.files[0]
                    fileName = Path(f)

                    saveDialog = QFileDialog.getSaveFileName(
                        self,
                        'Save reversed PDF',
                        fileName.stem + '_reversed',
                        'Portable Document Files (*.pdf)')
                    path = str(saveDialog[0])

                    if not path:
                        self.hide()
                        self.filelistScreen.show()
                        return
                    clearData()

                    while True:
                        try:
                            src = Pdf.open(f)
                            break
                        except PasswordError:
                            text, ok = QInputDialog.getText(
                                self.filelistScreen, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                            if ok and text:
                                self.PDFpassword = str(text)
                                try:
                                    src = Pdf.open(
                                        f, password=self.PDFpassword)
                                    break
                                except PasswordError:
                                    continue
                            else:
                                goBack()
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
                        self.filelistScreen.show()
                        return
                    clearData()

                    for f in self.files:
                        fileName = Path(f)
                        while True:
                            try:
                                src = Pdf.open(f)
                                break
                            except PasswordError:
                                text, ok = QInputDialog.getText(
                                    self.filelistScreen, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                                if ok and text:
                                    self.PDFpassword = str(text)
                                    try:
                                        src = Pdf.open(
                                            f, password=self.PDFpassword)
                                        break
                                    except PasswordError:
                                        continue
                                else:
                                    goBack()
                                    return

                        path = str(folderDialog + '/' +
                                   f'{fileName.stem}_reversed.pdf')
                        dst = Pdf.new()
                        dst.pages.extend(src.pages)
                        dst.pages.reverse()
                        dst.save(path)
                        dst.close()
                        src.close()

                finishedWindow()

            # Construct window content
            self.filelistScreen.optionsWidget = QWidget(self.filelistScreen)
            self.filelistScreen.optionsWidget.layout = QVBoxLayout(
                self.filelistScreen.optionsWidget)
            self.filelistScreen.optionsWidget.setLayout(
                self.filelistScreen.optionsWidget.layout)
            self.filelistScreenLayout.addWidget(self.filelistScreen.listWidget)
            self.filelistScreenLayout.addWidget(self.filelistScreen.optionsWidget)

            # Add buttons based on file context
            if len(self.files) == 1:
                self.filelistScreen.optionsWidget.splitButton = QPushButton(
                    'Split PDF')
                self.filelistScreen.optionsWidget.splitButton.setFont(
                    QFont(*FONT_LIST))
                self.filelistScreen.optionsWidget.splitButton.clicked.connect(
                    splitPDF)
                self.filelistScreen.optionsWidget.splitButton.setToolTip(
                    'Split file into single-page PDFs')
                self.filelistScreen.optionsWidget.layout.addWidget(
                    self.filelistScreen.optionsWidget.splitButton)

                self.filelistScreen.optionsWidget.reverseButton = QPushButton(
                    'Reverse PDF')
                self.filelistScreen.optionsWidget.reverseButton.setFont(
                    QFont(*FONT_LIST))
                self.filelistScreen.optionsWidget.reverseButton.clicked.connect(
                    reversePDF)
                self.filelistScreen.optionsWidget.reverseButton.setToolTip(
                    'Reverse page order')
                self.filelistScreen.optionsWidget.layout.addWidget(
                    self.filelistScreen.optionsWidget.reverseButton)

                self.filelistScreen.optionsWidget.backButton = QPushButton('Back')
                self.filelistScreen.optionsWidget.backButton.setFont(
                    QFont(*FONT_LIST))
                self.filelistScreen.optionsWidget.backButton.clicked.connect(goBack)
                self.filelistScreen.optionsWidget.backButton.setToolTip(
                    'Go back to welcome screen')
                self.filelistScreen.optionsWidget.layout.addWidget(
                    self.filelistScreen.optionsWidget.backButton)

            else:
                self.filelistScreen.optionsWidget.mergeButton = QPushButton(
                    'Merge PDFs')
                self.filelistScreen.optionsWidget.mergeButton.setFont(
                    QFont(*FONT_LIST))
                self.filelistScreen.optionsWidget.mergeButton.clicked.connect(
                    mergePDF)
                self.filelistScreen.optionsWidget.mergeButton.setToolTip(
                    'Merge files into one PDF')
                self.filelistScreen.optionsWidget.layout.addWidget(
                    self.filelistScreen.optionsWidget.mergeButton)

                self.filelistScreen.optionsWidget.splitButton = QPushButton(
                    'Split PDFs')
                self.filelistScreen.optionsWidget.splitButton.setFont(
                    QFont(*FONT_LIST))
                self.filelistScreen.optionsWidget.splitButton.clicked.connect(
                    splitPDF)
                self.filelistScreen.optionsWidget.splitButton.setToolTip(
                    'Split files into single-page PDFs')
                self.filelistScreen.optionsWidget.layout.addWidget(
                    self.filelistScreen.optionsWidget.splitButton)

                self.filelistScreen.optionsWidget.reverseButton = QPushButton(
                    'Reverse PDFs')
                self.filelistScreen.optionsWidget.reverseButton.setFont(
                    QFont(*FONT_LIST))
                self.filelistScreen.optionsWidget.reverseButton.clicked.connect(
                    reversePDF)
                self.filelistScreen.optionsWidget.reverseButton.setToolTip(
                    'Reverse page order')
                self.filelistScreen.optionsWidget.layout.addWidget(
                    self.filelistScreen.optionsWidget.reverseButton)

                self.filelistScreen.optionsWidget.backButton = QPushButton('Back')
                self.filelistScreen.optionsWidget.backButton.setFont(
                    QFont(*FONT_LIST))
                self.filelistScreen.optionsWidget.backButton.clicked.connect(goBack)
                self.filelistScreen.optionsWidget.backButton.setToolTip(
                    'Go back to welcome screen')
                self.filelistScreen.optionsWidget.layout.addWidget(
                    self.filelistScreen.optionsWidget.backButton)

        # Bounce back to welcome screen with fail message if no valid file dropped
        else:
            self.text.setText(STRING_WELCOME_FAIL)
            self.text.setStyleSheet(STYLESHEET_MAIN)

# Define main window


class MAIN_WINDOW(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_gui()

    def init_gui(self):
        self.setWindowTitle(APP_NAME + ' v.' +
                            APP_VERSION + ' by ' + APP_AUTHOR)
        self.resize(720, 480)
        self.setWindowIcon(QIcon(resource_path(':/tewl_logo')))
        self.window = QWidget()
        self.layout = QGridLayout()
        self.setCentralWidget(self.window)
        self.window.setLayout(self.layout)

        self.filelistScreen = QWidget()
        self.layout.addWidget(self.filelistScreen)
        self.filelistScreen.hide()

        self.welcomeScreen = WELCOME_SCREEN(self.filelistScreen)
        self.layout.addWidget(self.welcomeScreen)
        self.welcomeScreen.show() # Show the main window

        # self.filelistScreen = FILELIST_SCREEN()
        # self.layout.addWidget(self.filelistScreen)
        # self.filelistScreen.hide()

        # self.workingScreen = QWidget()
        # self.layout.addWidget(self.workingScreen)
        # self.workingScreen.hide()

        # self.FINISHED_SCREEN = QWidget()
        # self.layout.addWidget(self.FINISHED_SCREEN)
        # self.FINISHED_SCREEN.hide()


# Initialise the programme
if __name__ == '__main__':
    app = QApplication([])
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    app.setStyleSheet(STYLESHEET_CONTAINER)
    mainWindow = MAIN_WINDOW()
    mainWindow.show()

    sys.exit(app.exec_())
