#! python3
# Character Encoding: UTF-8

'''
# tewlPDF
# a simple PDF manipulator with PyQt5 GUI

# Shortcut to recompile resources:
# pyrcc5 resources.qrc -o resources.py
'''

##############################################################################################################################

import os
import sys

from pathlib import Path

from pikepdf import PasswordError, Pdf
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QFontDatabase, QIcon

from PyQt5.QtWidgets import (QApplication, QDialog, QDialogButtonBox,
                             QFileDialog, QFormLayout, QGridLayout, QHBoxLayout,
                             QInputDialog, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
                             QSizeGrip, QSpinBox, QStyle, QVBoxLayout, QWidget, qApp)

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
APP_VERSION = '0.9.1'
APP_AUTHOR = 'tewlwolow'

# Messages
STRING_DROP = 'DROP IT HERE'
STRING_DROP_FAIL = 'Didn\'t drop any PDF files.\nTry again!'
STRING_FINISHED = 'It\'s done!'
STRING_ERROR = '<h2><strong>Error!<strong></h2>'
STRING_ERRORMESSAGE = STRING_ERRORMESSAGE = "Invalid page number for file:<br><strong>{}</strong><br>Skipping."


STRING_SPLIT = 'SPLIT'
STRING_MERGE = 'MERGE'
STRING_REVERSE = 'REVERSE'
STRING_BACK = 'BACK'
STRING_CUT = 'CUT'
STRING_EXTRACT = 'EXTRACT'
STRING_AGAIN = 'AGAIN'

TOOLTIP_SPLIT = 'Split files into single-page PDFs'
TOOLTIP_MERGE = 'Merge files into one PDF'
TOOLTIP_REVERSE = 'Reverse page order'
TOOLTIP_BACK = 'Go back to welcome screen'
TOOLTIP_CUT = 'Cut PDF in two'
TOOLTIP_EXTRACT = 'Extract pages from PDF'
TOOLTIP_AGAIN = 'Manipulate more files'

STRING_INFO = """
	<h2><center>tewlPDF v.{}</center></h2><br>
	Drag and drop files into main window to manipulate them.<br>
	Grab corners to resize. Click and move to reposition.<br>
	Double-click app window to exit.<br>
	Double-click list items to remove them.<br>
	Double-click on this dialog to close it.<br><br>
	© Created by <strong>Leon Czernecki</strong>, 2022-21.<br>
	<a style="color:lightblue" href = "https:/www.github.com/tewlwolow">github.com/tewlwolow</a>  
"""
STRING_EXIT = "Are you sure you want to exit?"

# Fonts
FONT_MAIN = ['Darker Grotesque', 60]
FONT_LIST = ['Zen Maru Gothic', 15]

# Define stylesheets
# Using paths from resource_rc cuz, again, auto-py-to-exe
STYLESHEET_CONTAINER = """
	MainWindow {
		background-image: url(:tewl_bg_main);
	}
"""
STYLESHEET_MAIN = 'background-color: rgba(255,255,255,0.15); border-radius: 50px; color: rgb(0, 0, 0)'
STYLESHEET_HIGHLIGHT = 'background-color: rgba(255,255,255,0.15); border-radius: 50px; color: rgba(255, 255, 255, 0.6)'
STYLESHEET_LIST = 'background-color: rgba(255,255,255,0.3); border-radius: 25px; color: rgb(0, 0, 0); padding: 15px 15px 15px 15px;'
STYLESHEET_BUTTON = 'background-color: rgba(255, 25, 30, 0.3); padding: 10px 10px 10px 10px; border: 2px solid rgba(0,0,0,0.2); border-radius: 25%; color: rgb(0, 0, 0)'
STYLESHEET_BUTTON_SECONDARY = 'background-color: rgba(120, 80, 120, 0.2); padding: 10px 10px 10px 10px; border: 1px solid rgba(0,0,0,0.2); border-radius: 25%; color: rgb(0, 0, 0)'
STYLESHEET_BUTTON_AGAIN = 'background-color: rgba(100, 50, 170, 0.2); padding: 10px 10px 10px 10px; border: 1px solid rgba(0,0,0,0.2); border-radius: 25%; color: rgb(0, 0, 0); margin-bottom: 10%'

# Define window structure

# Window to be shown after finished operation


class FinishedScreen(QWidget):
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

        self.againButton = QPushButton(STRING_AGAIN)
        self.againButton.setFont(QFont(*FONT_LIST))
        self.againButton.clicked.connect(restart)
        self.againButton.setStyleSheet(STYLESHEET_BUTTON_AGAIN)

        self.layout.addWidget(self.againButton, 0, 0, -
                              1, -1, alignment=Qt.AlignCenter | Qt.AlignBottom)
        self.setLayout(self.layout)


# Main window defining available operations
# Contains a list over files to be processed
class FilelistScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.layout = QHBoxLayout(self)
        self.listWidget = QListWidget(self)
        self.listWidget.setFont(QFont(*FONT_LIST))
        self.listWidget.setStyleSheet(STYLESHEET_LIST)
        # For reordering the list inside the widget
        self.listWidget.setDragDropMode(
            QListWidget.InternalMove)
        self.listWidget.setDragEnabled(True)
        # Remove item if double-clicked
        self.listWidget.itemDoubleClicked.connect(self.removeListItem)
        self.setLayout(self.layout)

    # Setter
    def setFiles(self, files):
        self.__files = files

    # Getter
    def getFiles(self):
        return self.__files

    # Clear list between cycles
    def purgeFiles(self):
        self.__files = []

    # Remove list object from class attribute and hide from view
    def removeListItem(self, item):
        self.__files.remove(item.text())
        item.setHidden(True)
        newFiles = self.__files
        self.clearData()
        self.setFiles(newFiles)
        self.parseFiles()
        # If there's no files left, bounce back to welcome screen
        if len(self.__files) == 0:
            self.goBack()

    def dragEnterEvent(self, event):
        # Make sure mouse clicks don't intefere
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    # Only add valid PDFs to list
    def dropEvent(self, event):
        addedFiles = [u.toLocalFile() for u in event.mimeData().urls()
                      if u.toLocalFile().endswith('.pdf')]

        # Organise files and rerun view parser
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

    # Useful for cancelling a specific operation
    def reShow(self):
        self.hide()
        self.show()

    # For showing out of index errors
    def showIndexErrorBox(self, filename):
        indexErrorBox = QMessageBox()
        indexErrorBox.setIcon(QMessageBox.Critical)
        indexErrorBox.setTextFormat(Qt.RichText)
        indexErrorBox.setText(STRING_ERROR)
        indexErrorBox.setInformativeText(
            STRING_ERRORMESSAGE.format(filename.stem))
        indexErrorBox.setWindowTitle(STRING_ERROR)
        indexErrorBox.setWindowFlags(Qt.FramelessWindowHint)
        indexErrorBox.exec_()

    # Fairly cumbersome loop for handling errors due to encrypted files
    def getSafeFile(self, f):
        while True:
            try:
                src = Pdf.open(f)
                return src
            except PasswordError:
                fileName = Path(f)
                text, ok = QInputDialog.getText(
                    self, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:', QLineEdit.Password)
                if text and ok:
                    self.PDFpassword = str(text)
                    try:
                        src = Pdf.open(
                            f, password=self.PDFpassword)
                        return src
                    except PasswordError:
                        continue
                else:
                    return None

    # Define merging operation
    def mergePDF(self):
        # Get files once again; user might have reordered those
        # Using data from the 'model', not view
        self.__files = [str(self.listWidget.item(i).data(Qt.UserRole))
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
            self.reShow()
            return

        pdf = Pdf.new()
        for f in self.__files:
            src = self.getSafeFile(f)
            if not src:
                self.reShow()
                return
            pdf.pages.extend(src.pages)

        pdf.save(path)
        pdf.close()

        self.clearData()
        mainWindow.finishedScreen.show()

    # Define cutting operation
    def cutPDF(self):

        # Nothing works here for hiding the ugly bar...
        inputWindow = QInputDialog(self)

        limit, ok = inputWindow.getInt(
            self, 'Give details', 'The last page to be included in the first file:')

        if not ok or limit == 0:
            self.reShow()
            return

        folderDialog = QFileDialog.getExistingDirectory(
            self, 'Select Folder')

        if not folderDialog:
            self.reShow()
            return

        for f in self.__files:
            fileName = Path(f)
            src = self.getSafeFile(f)
            if not src:
                self.reShow()
                return

            # Check for OutOfBounds type error
            if len(src.pages) <= limit:
                self.showIndexErrorBox(fileName)
                return
            else:
                self.hide()

                # Define paths for two cut files
                path_1 = str(folderDialog + '/' +
                             f'{fileName.stem}_part1.pdf')

                path_2 = str(folderDialog + '/' +
                             f'{fileName.stem}_part2.pdf')

                # Create new files per designated slices
                dst_1 = Pdf.new()
                for page in src.pages[:limit]:
                    dst_1.pages.append(page)
                dst_1.save(path_1)
                dst_1.close()

                dst_2 = Pdf.new()
                for page in src.pages[limit:]:
                    dst_2.pages.append(page)
                dst_2.save(path_2)
                dst_2.close()

                src.close()

        self.clearData()
        mainWindow.finishedScreen.show()

    # Define extracting operation
    def extractPDF(self):

        # Nothing works here for hiding the ugly bar...
        inputWindow = QDialog(self)
        inputWindow.setWindowTitle('Pages to extract:')
        inputWindow.first = QSpinBox(inputWindow)
        inputWindow.last = QSpinBox(inputWindow)
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, inputWindow)
        layout = QFormLayout(inputWindow)
        layout.addRow("First page", inputWindow.first)
        layout.addRow("Last page", inputWindow.last)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(inputWindow.accept)
        buttonBox.rejected.connect(inputWindow.reject)
        inputWindow.exec_()

        # Because we're using 0-indexed Pythonic numbering later on
        first = int(inputWindow.first.value()) - 1
        last = int(inputWindow.last.value())

        if first < 0 or last == 0:
            self.reShow()
            return

        # Different file/folder handling based on no files
        if len(self.__files) == 1:
            f = self.__files[0]
            fileName = Path(f)

            saveDialog = QFileDialog.getSaveFileName(
                self,
                'Save reversed PDF',
                fileName.stem + '_extracted',
                'Portable Document Files (*.pdf)')
            path = str(saveDialog[0])

            if not path:
                self.reShow()
                return

            src = self.getSafeFile(f)
            if not src:
                self.reShow()
                return

            if len(src.pages) <= last:
                self.showIndexErrorBox(fileName)
                return
            else:
                self.hide()

                dst = Pdf.new()

                # Write the selected slice to a new file
                for page in src.pages[first:last]:
                    dst.pages.append(page)
                dst.save(path)
                dst.close()

                src.close()
        else:
            folderDialog = QFileDialog.getExistingDirectory(
                self, 'Select Folder')

            if not folderDialog:
                self.reShow()
                return

            for f in self.__files:
                fileName = Path(f)
                src = self.getSafeFile(f)
                if not src:
                    self.reShow()
                    return

                if len(src.pages) <= last:
                    self.showIndexErrorBox(fileName)
                    return
                else:
                    self.hide()

                    path = str(folderDialog + '/' +
                               f'{fileName.stem}_extracted.pdf')

                    dst = Pdf.new()

                    # Write the selected slice to a new file
                    for page in src.pages[first:last]:
                        dst.pages.append(page)
                    dst.save(path)
                    dst.close()

                    src.close()

        self.clearData()
        mainWindow.finishedScreen.show()

    # Define splitting operation
    def splitPDF(self):
        self.hide()
        folderDialog = QFileDialog.getExistingDirectory(
            self, 'Select Folder')

        if not folderDialog:
            self.reShow()
            return

        # Need a custom counter here in order not to end up overwriting the files
        n = 0
        for f in self.__files:
            src = self.getSafeFile(f)
            if not src:
                self.reShow()
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
        self.hide()

        # Different file/folder handling based on no files
        # TODO: Refactor? Too much repetition here I fear
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
                self.reShow()
                return

            src = self.getSafeFile(f)
            if not src:
                self.reShow()
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
                self.reShow()
                return

            for f in self.__files:
                fileName = Path(f)
                src = self.getSafeFile(f)
                if not src:
                    self.reShow()
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

    def initButton(self, button, tooltip, func, style):
        button.setFont(QFont(*FONT_LIST))
        button.clicked.connect(func)
        button.setToolTip(tooltip)
        self.optionsWidget.layout.addWidget(button)
        button.setStyleSheet(style)

    # Create list objects for each valid file

    def parseFiles(self):
        # Create list view for each valid file dropped
        # Show only the file stem, but store the full path for proper handling of reorder events
        for f in self.__files:
            i = QListWidgetItem()
            i.setIcon(self.style().standardIcon(
                QStyle.SP_FileDialogDetailedView))
            i.setText(Path(f).stem)
            i.setData(Qt.UserRole, f)
            self.listWidget.addItem(i)

        if len(self.__files):
            # Advance only if provided with valid files
            # Update doesn't work. Bummer
            self.reShow()

            # Construct window content, i.e. list and options view
            self.optionsWidget = QWidget(self)
            self.optionsWidget.layout = QVBoxLayout(
                self.optionsWidget)
            self.optionsWidget.setLayout(
                self.optionsWidget.layout)
            self.layout.addWidget(self.listWidget)
            self.layout.addWidget(
                self.optionsWidget)

            # Add buttons based on file context

            # Can only merge more than one file, right?
            if len(self.__files) > 1:
                self.optionsWidget.mergeButton = QPushButton(STRING_MERGE)
                self.initButton(self.optionsWidget.mergeButton,
                                TOOLTIP_MERGE, self.mergePDF, STYLESHEET_BUTTON)

            self.optionsWidget.cutButton = QPushButton(STRING_CUT)
            self.initButton(self.optionsWidget.cutButton,
                            TOOLTIP_CUT, self.cutPDF, STYLESHEET_BUTTON)

            self.optionsWidget.extractButton = QPushButton(STRING_EXTRACT)
            self.initButton(self.optionsWidget.extractButton,
                            TOOLTIP_EXTRACT, self.extractPDF, STYLESHEET_BUTTON)

            self.optionsWidget.splitButton = QPushButton(STRING_SPLIT)
            self.initButton(self.optionsWidget.splitButton,
                            TOOLTIP_SPLIT, self.splitPDF, STYLESHEET_BUTTON)

            self.optionsWidget.reverseButton = QPushButton(STRING_REVERSE)
            self.initButton(self.optionsWidget.reverseButton,
                            TOOLTIP_REVERSE, self.reversePDF, STYLESHEET_BUTTON)

            self.optionsWidget.backButton = QPushButton(STRING_BACK)
            self.initButton(self.optionsWidget.backButton, TOOLTIP_BACK,
                            self.goBack, STYLESHEET_BUTTON_SECONDARY)


class WelcomeScreen(QWidget):
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

        # Add the clickable logo
        button = QPushButton(QIcon(':/tewl_logo'), "")
        button.setStyleSheet('background-color: transparent; margin-top: 20px')
        button.setIconSize(QSize(100, 100))
        button.clicked.connect(self.infoClicked)
        self.layout.addWidget(button, 0, 0, 1, 1,
                              alignment=Qt.AlignCenter | Qt.AlignTop)
        self.dlg = QDialog(self)
        self.dlg.setWindowTitle("Info")
        self.dlg.setWindowFlags(Qt.SplashScreen)
        self.dlg.layout = QGridLayout()
        self.dlg.text = QLabel()
        self.dlg.text.setOpenExternalLinks(True)
        self.dlg.text.setTextFormat(Qt.RichText)
        self.dlg.text.setText(STRING_INFO.format(APP_VERSION))
        self.dlg.text.setAlignment(Qt.AlignCenter)
        self.dlg.text.setFont(QFont(*FONT_LIST))
        self.dlg.setStyleSheet('background-color: rgb(50,10,40); color: beige')
        self.dlg.layout.addWidget(self.dlg.text)
        self.dlg.setLayout(self.dlg.layout)
        self.dlg.setWindowOpacity(0.95)
        self.dlg.mouseDoubleClickEvent = lambda event: self.dlg.hide()
        self.dlg.hide()

    # Show info popup on clicking the logo
    def infoClicked(self, b):
        self.dlg.exec_()

    def dragEnterEvent(self, event):
        # Show highlight on drag enter
        self.text.setStyleSheet(STYLESHEET_HIGHLIGHT)

        # Bounce off mouse clicks just in case something weird happens
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        # Go back to the main style
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
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initGUI()

    def initGUI(self):
        # Just in case it shows in some configurations
        self.setWindowTitle(APP_NAME + ' v.' +
                            APP_VERSION + ' by ' + APP_AUTHOR)
        self.setWindowIcon(QIcon(':/tewl_logo'))
        self.setStyleSheet(STYLESHEET_CONTAINER)
        # A bit wider than usual, best for messages
        self.resize(1200, 800)
        self.window = QWidget()
        self.layout = QGridLayout()
        self.setCentralWidget(self.window)
        # Yayyyy modern design!
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.window.setLayout(self.layout)
        self.clicked = False

        # Not 100% sure it's the best we can do here, but oh well
        self.gripSize = 16
        self.grips = []
        for i in range(4):
            grip = QSizeGrip(self)
            grip.resize(self.gripSize, self.gripSize)
            self.grips.append(grip)

        # Define and show welcome screen
        self.welcomeScreen = WelcomeScreen()
        self.layout.addWidget(self.welcomeScreen)
        self.welcomeScreen.show()

        # Define filelist screen
        self.filelistScreen = FilelistScreen()
        self.layout.addWidget(self.filelistScreen)
        self.filelistScreen.hide()

        # Define finished screen
        self.finishedScreen = FinishedScreen(self)
        self.layout.addWidget(self.finishedScreen)
        self.finishedScreen.hide()

    # Immersive escape route
    def mouseDoubleClickEvent(self, event):
        msg = STRING_EXIT
        reply = QMessageBox.question(self, 'Message',
                                     msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
            qApp.quit()
        else:
            event.ignore()

    def resizeEvent(self, event):
        QMainWindow.resizeEvent(self, event)
        rect = self.rect()
        # top left grip doesn't need to be moved...
        # top right
        self.grips[1].move(rect.right() - self.gripSize, 0)
        # bottom right
        self.grips[2].move(
            rect.right() - self.gripSize, rect.bottom() - self.gripSize)
        # bottom left
        self.grips[3].move(0, rect.bottom() - self.gripSize)

    # Make the programme draggable
    def mousePressEvent(self, ev):
        self.old_pos = ev.screenPos()

    def mouseMoveEvent(self, ev):
        if self.clicked:
            dx = self.old_pos.x() - ev.screenPos().x()
            dy = self.old_pos.y() - ev.screenPos().y()
            # A bunch of explicit conversions cuz Python complains implicit one is gonna get deprecated real soon
            self.move(int(self.pos().x()) - int(dx),
                      int(self.pos().y()) - int(dy))
        self.old_pos = ev.screenPos()
        self.clicked = True
        return QWidget.mouseMoveEvent(self, ev)


# Initialise the programme
if __name__ == '__main__':
    app = QApplication([])

    # Ugly, not needed, begone
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton)

    # Add main fonts here
    QFontDatabase.addApplicationFont(':/tewl_h_font')
    QFontDatabase.addApplicationFont(':/tewl_p_font')

    mainWindow = MainWindow()
    mainWindow.show()

    sys.exit(app.exec_())
