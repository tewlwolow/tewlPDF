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
import sys, os, time, resource_rc

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
APP_VERSION = '0.3 beta' # TODO: 1.0 when done!
APP_AUTHOR = 'tewlwolow'

# Messages
STRING_WELCOME = 'Drop it here'
STRING_WELCOME_FAIL = 'Didn\'t drop any PDF files.\nTry again!'

# Stylesheet finals
FONT_MAIN = ['Campora', 43]
FONT_LIST = ['Linux Biolinum G', 12, QFont.Bold]

# Define stylesheets
# Using paths from resource_rc cuz, again, auto-py-to-exe
stylesheet = """
    mainWindow {
        background-image: url(:/twine.png); 
    }
"""
stylesheetMain = 'background-image: url(:/bush.png); border: 2px solid black; color: rgb(0, 0, 0)'
stylesheetList = 'background-image: url(:/bushList.png); border: 2px solid black; color: rgb(0, 0, 0)'
stylesheetHighlight = 'background-image: url(:/bush.png); border: 2px solid black; color: rgba(0, 0, 139, 130)' 

# Define window structure
class dragDropWindow(QWidget):
    def __init__(self, PDFContainerWindow):
        super().__init__()

        # Define the contents of the welcome screen
        self.setWindowTitle('DragDrop')
        self.setAcceptDrops(True)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.text = QLabel(STRING_WELCOME)
        self.layout.addWidget(self.text)
        self.text.setAlignment(Qt.AlignCenter)        
        self.text.setStyleSheet(stylesheetMain) 
        self.text.setFont(QFont(*FONT_MAIN))        
        self.show()

        # Catch the second screen and initialise it
        self.PDFWindow = PDFContainerWindow
        self.PDFWindow.setAcceptDrops(True)
        self.PDFWindowLayout = QHBoxLayout(self.PDFWindow)

        # Create the list widget to hold filenames inside the second screen
        self.PDFWindow.listWidget = QListWidget(self.PDFWindow)
        self.PDFWindow.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.PDFWindow.listWidget.setDragEnabled(True)
        self.PDFWindow.listWidget.setFont(QFont(*FONT_LIST)) 
        self.PDFWindow.listWidget.setStyleSheet(stylesheetList)

        # Set the layout and hide for now
        self.PDFWindow.setLayout(self.PDFWindowLayout) 
        self.PDFWindow.hide()  
        
    def dragEnterEvent(self, event):
        # Define highlight style
        self.text.setStyleSheet(stylesheetHighlight)

        # Bounce off mouse clicks
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        # Go back to main style
        self.text.setStyleSheet(stylesheetMain) 

    # Main step to dynamically create data and define operations
    def dropEvent(self, event):

        # Catche dropped files
        self.files = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile().endswith('.pdf')]

        # Create list objects for each valid file
        for f in self.files:
            i = QListWidgetItem((QIcon(resource_path('logo.png'))), f, self.PDFWindow.listWidget)

        if len(self.files):
            # Advance if provided with valid files
            self.hide()
            self.PDFWindow.show()

            # Purge data between window switches
            def clearData():
                self.PDFWindow.listWidget.clear()
                self.PDFWindowLayout.removeWidget(self.PDFWindow.optionsWidget)
                self.PDFWindow.optionsWidget.deleteLater()

            # Bounce back to welcome screen
            def goBack():
                self.PDFWindow.hide()
                clearData()
                self.text.setText(STRING_WELCOME)
                self.text.setStyleSheet(stylesheetMain) 
                self.show()
            
            # Bounce back to welcome screen without clearing data after finished operation
            def reRun():
                self.backButton.deleteLater()
                self.PDFWindow.hide()
                self.text.setText(STRING_WELCOME)
                self.text.setStyleSheet(stylesheetMain) 
                self.show()

            # Show the finished operation window
            def finishedWindow():
                time.sleep(1)
                self.text.setText('It\'s done!')
                self.text.setStyleSheet(stylesheetMain) 
                self.backButton = QPushButton('Again')
                self.backButton.setFont(QFont(*FONT_LIST))   
                self.backButton.clicked.connect(reRun)
                self.layout.addWidget(self.backButton)

            # Show window while operation is taking place
            def loaderWindow():
                self.PDFWindow.hide()
                self.text.setText('Working...')
                self.text.setStyleSheet(stylesheetMain)
                self.show()

            # Define merging operation
            def mergePDF():
                # Get files once again; user might have reordered those
                self.files = [str(self.PDFWindow.listWidget.item(i).text()) for i in range(self.PDFWindow.listWidget.count())]
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
                    self.PDFWindow.show()
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
                            text, ok = QInputDialog.getText(self.PDFWindow, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                            if ok and text:
                                self.PDFpassword = str(text)
                                try:
                                    src = Pdf.open(f, password=self.PDFpassword)
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
                self.files = [str(self.PDFWindow.listWidget.item(i).text()) for i in range(self.PDFWindow.listWidget.count())]
                loaderWindow()
                folderDialog = QFileDialog.getExistingDirectory(self, 'Select Folder')

                if not folderDialog:
                    self.hide()
                    self.PDFWindow.show()
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
                            text, ok = QInputDialog.getText(self.PDFWindow, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                            if ok and text:
                                self.PDFpassword = str(text)
                                try:
                                    src = Pdf.open(f, password=self.PDFpassword)
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
                self.files = [str(self.PDFWindow.listWidget.item(i).text()) for i in range(self.PDFWindow.listWidget.count())]
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
                        self.PDFWindow.show()
                        return
                    clearData()

                    while True:
                        try:
                            src = Pdf.open(f)
                            break
                        except PasswordError:
                            text, ok = QInputDialog.getText(self.PDFWindow, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                            if ok and text:
                                self.PDFpassword = str(text)
                                try:
                                    src = Pdf.open(f, password=self.PDFpassword)
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
                    folderDialog = QFileDialog.getExistingDirectory(self, 'Select Folder')

                    if not folderDialog:
                        self.hide()
                        self.PDFWindow.show()
                        return
                    clearData()

                    for f in self.files:
                        fileName = Path(f)
                        while True:
                            try:
                                src = Pdf.open(f)
                                break
                            except PasswordError:
                                text, ok = QInputDialog.getText(self.PDFWindow, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                                if ok and text:
                                    self.PDFpassword = str(text)
                                    try:
                                        src = Pdf.open(f, password=self.PDFpassword)
                                        break
                                    except PasswordError:
                                        continue
                                else:
                                    goBack()
                                    return

                        path = str(folderDialog + '/' + f'{fileName.stem}_reversed.pdf')
                        dst = Pdf.new()
                        dst.pages.extend(src.pages)
                        dst.pages.reverse()
                        dst.save(path)
                        dst.close()
                        src.close()

                finishedWindow()
            
            # Construct window content
            self.PDFWindow.optionsWidget = QWidget(self.PDFWindow)
            self.PDFWindow.optionsWidget.layout = QVBoxLayout(self.PDFWindow.optionsWidget)
            self.PDFWindow.optionsWidget.setLayout(self.PDFWindow.optionsWidget.layout)
            self.PDFWindowLayout.addWidget(self.PDFWindow.listWidget)      
            self.PDFWindowLayout.addWidget(self.PDFWindow.optionsWidget)

            # Add buttons based on file context
            if len(self.files) == 1:
                self.PDFWindow.optionsWidget.splitButton = QPushButton('Split PDF')
                self.PDFWindow.optionsWidget.splitButton.setFont(QFont(*FONT_LIST))
                self.PDFWindow.optionsWidget.splitButton.clicked.connect(splitPDF)
                self.PDFWindow.optionsWidget.splitButton.setToolTip('Split file into single-page PDFs')
                self.PDFWindow.optionsWidget.layout.addWidget(self.PDFWindow.optionsWidget.splitButton)

                self.PDFWindow.optionsWidget.reverseButton = QPushButton('Reverse PDF')
                self.PDFWindow.optionsWidget.reverseButton.setFont(QFont(*FONT_LIST))
                self.PDFWindow.optionsWidget.reverseButton.clicked.connect(reversePDF)
                self.PDFWindow.optionsWidget.reverseButton.setToolTip('Reverse page order')
                self.PDFWindow.optionsWidget.layout.addWidget(self.PDFWindow.optionsWidget.reverseButton)

                self.PDFWindow.optionsWidget.backButton = QPushButton('Back')
                self.PDFWindow.optionsWidget.backButton.setFont(QFont(*FONT_LIST))   
                self.PDFWindow.optionsWidget.backButton.clicked.connect(goBack)
                self.PDFWindow.optionsWidget.backButton.setToolTip('Go back to welcome screen')
                self.PDFWindow.optionsWidget.layout.addWidget(self.PDFWindow.optionsWidget.backButton)
            
            else:
                self.PDFWindow.optionsWidget.mergeButton = QPushButton('Merge PDFs')
                self.PDFWindow.optionsWidget.mergeButton.setFont(QFont(*FONT_LIST))
                self.PDFWindow.optionsWidget.mergeButton.clicked.connect(mergePDF)
                self.PDFWindow.optionsWidget.mergeButton.setToolTip('Merge files into one PDF')
                self.PDFWindow.optionsWidget.layout.addWidget(self.PDFWindow.optionsWidget.mergeButton)

                self.PDFWindow.optionsWidget.splitButton = QPushButton('Split PDFs')
                self.PDFWindow.optionsWidget.splitButton.setFont(QFont(*FONT_LIST))
                self.PDFWindow.optionsWidget.splitButton.clicked.connect(splitPDF)
                self.PDFWindow.optionsWidget.splitButton.setToolTip('Split files into single-page PDFs')
                self.PDFWindow.optionsWidget.layout.addWidget(self.PDFWindow.optionsWidget.splitButton)

                self.PDFWindow.optionsWidget.reverseButton = QPushButton('Reverse PDFs')
                self.PDFWindow.optionsWidget.reverseButton.setFont(QFont(*FONT_LIST))
                self.PDFWindow.optionsWidget.reverseButton.clicked.connect(reversePDF)
                self.PDFWindow.optionsWidget.reverseButton.setToolTip('Reverse page order')
                self.PDFWindow.optionsWidget.layout.addWidget(self.PDFWindow.optionsWidget.reverseButton)

                self.PDFWindow.optionsWidget.backButton = QPushButton('Back')
                self.PDFWindow.optionsWidget.backButton.setFont(QFont(*FONT_LIST))   
                self.PDFWindow.optionsWidget.backButton.clicked.connect(goBack)
                self.PDFWindow.optionsWidget.backButton.setToolTip('Go back to welcome screen')
                self.PDFWindow.optionsWidget.layout.addWidget(self.PDFWindow.optionsWidget.backButton)

        # Bounce back to welcome screen with fail message if no valid file dropped    
        else:
            self.text.setText(STRING_WELCOME_FAIL)
            self.text.setStyleSheet(stylesheetMain) 

# Define main window
class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_gui()

    def init_gui(self):
        self.setWindowTitle(APP_NAME + ' v.' + APP_VERSION + ' by ' + APP_AUTHOR)
        self.resize(720, 480)
        self.setWindowIcon(QIcon(resource_path('logo.png')))
        self.window = QWidget()
        self.layout = QGridLayout()
        self.setCentralWidget(self.window)
        self.window.setLayout(self.layout)

        self.PDFWindow = QWidget()
        self.layout.addWidget(self.PDFWindow)
        self.PDFWindow.hide()

        self.dragWindow = dragDropWindow(self.PDFWindow)
        self.layout.addWidget(self.dragWindow)

# Initialise the programme
if __name__ == '__main__':
    app = QApplication([])
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    app.setStyleSheet(stylesheet)       
    mainWindow = mainWindow()
    mainWindow.show()
    
    sys.exit(app.exec_())
