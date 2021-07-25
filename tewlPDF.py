#! python3
# Character Encoding: UTF-8

'''
# tewlPDF
# a simple PDF manipulator with PyQt5 GUI
'''

# Import all the required stuff
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
from PyQt5 import QtGui, QtCore
from pathlib import Path
import sys, os, pikepdf, time

# Define some (semi) constans
APP_NAME = 'tewlPDF'
APP_VERSION = '0.2 beta'
APP_AUTHOR = 'tewlwolow'
STRING_WELCOME = 'Drop it here'
STRING_WELCOME_FAIL = 'Didn\'t drop any PDF files.\nTry again!'
FONT_MAIN = ['Campora', 43]
FONT_LIST = ['Linux Biolinum G', 12, QtGui.QFont.Bold]

# Define stylesheets
stylesheet = """
    mainWindow {
        background-image: url("twine.png"); 
    }
"""
stylesheetMain = 'background-image: url("bush.png"); border: 2px solid black; color: rgb(0, 0, 0)'
stylesheetList = 'background-image: url("bushList.png"); border: 2px solid black; color: rgb(0, 0, 0)'
stylesheetHighlight = 'background-image: url("bush.png"); border: 2px solid black; color: rgba(0, 0, 139, 130)' 

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
        self.text.setAlignment(QtCore.Qt.AlignCenter)        
        self.text.setStyleSheet(stylesheetMain) 
        self.text.setFont(QtGui.QFont(*FONT_MAIN))        
        self.show()

        # Catch the second screen and initialise it
        self.PDFWindow = PDFContainerWindow
        self.PDFWindow.setAcceptDrops(True)
        self.PDFWindowLayout = QHBoxLayout(self.PDFWindow)

        # Create the list widget to hold filenames inside the second screen
        self.PDFWindow.listWidget = QListWidget(self.PDFWindow)
        self.PDFWindow.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.PDFWindow.listWidget.setDragEnabled(True)
        self.PDFWindow.listWidget.setFont(QtGui.QFont(*FONT_LIST)) 
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
            i = QListWidgetItem((QtGui.QIcon('logo.png')), f, self.PDFWindow.listWidget)

        if len(self.files):
            # Advance if provided with valid files
            self.hide()
            self.PDFWindow.show()

            def clearData():
                self.PDFWindow.listWidget.clear()
                self.PDFWindowLayout.removeWidget(self.PDFWindow.optionsWidget)
                self.PDFWindow.optionsWidget.deleteLater()

            def goBack():
                self.PDFWindow.hide()

                clearData()

                self.text.setText(STRING_WELCOME)
                self.text.setStyleSheet(stylesheetMain) 
                self.show()

            def reRun():
                self.backButton.deleteLater()
                self.PDFWindow.hide()
                self.text.setText(STRING_WELCOME)
                self.text.setStyleSheet(stylesheetMain) 
                self.show()

            # Show the finished window
            def finishedWindow():
                time.sleep(1)
                self.text.setText('It\'s done!')
                self.text.setStyleSheet(stylesheetMain) 

                self.backButton = QPushButton('Again')
                self.backButton.setFont(QtGui.QFont(*FONT_LIST))   
                self.backButton.clicked.connect(reRun)
                self.layout.addWidget(self.backButton)

            def loaderWindow():
                self.PDFWindow.hide()
    
                self.text.setText('Working...')
                self.text.setStyleSheet(stylesheetMain)
                
                self.show()

            def mergePDF():
                self.files = [str(self.PDFWindow.listWidget.item(i).text()) for i in range(self.PDFWindow.listWidget.count())]
                loaderWindow()
                saveDialog = QFileDialog.getSaveFileName(
                self,
                'Save merged PDF',
                'Merged Document.pdf',
                'Portable Document Files (*.pdf)')

                path = str(saveDialog[0])

                if not path:
                    self.hide()
                    self.PDFWindow.show()
                    return
                clearData()

                pdf = pikepdf.Pdf.new()
                for f in self.files:
                    while True:
                        try:
                            src = pikepdf.Pdf.open(f)
                            break
                        except pikepdf.PasswordError:
                            fileName = Path(f)
                            text, ok = QInputDialog.getText(self.PDFWindow, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                            if ok and text:
                                self.PDFpassword = str(text)
                                try:
                                    src = pikepdf.Pdf.open(f, password=self.PDFpassword)
                                    break
                                except pikepdf.PasswordError:
                                    continue
                            else:
                                goBack()
                                return

                    pdf.pages.extend(src.pages)

                pdf.save(path)
                pdf.close()
                finishedWindow()
            
            def splitPDF():
                self.files = [str(self.PDFWindow.listWidget.item(i).text()) for i in range(self.PDFWindow.listWidget.count())]
                loaderWindow()
                folderDialog = QFileDialog.getExistingDirectory(self, 'Select Folder')

                if not folderDialog:
                    self.hide()
                    self.PDFWindow.show()
                    return
                clearData()

                n = 0
                for f in self.files:
                    while True:
                        try:
                            src = pikepdf.Pdf.open(f)
                            break
                        except pikepdf.PasswordError:
                            fileName = Path(f)
                            text, ok = QInputDialog.getText(self.PDFWindow, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                            if ok and text:
                                self.PDFpassword = str(text)
                                try:
                                    src = pikepdf.Pdf.open(f, password=self.PDFpassword)
                                    break
                                except pikepdf.PasswordError:
                                    continue
                            else:
                                goBack()
                                return
                    for _, page in enumerate(src.pages):
                        dst = pikepdf.Pdf.new()
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
                            src = pikepdf.Pdf.open(f)
                            break
                        except pikepdf.PasswordError:
                            text, ok = QInputDialog.getText(self.PDFWindow, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                            if ok and text:
                                self.PDFpassword = str(text)
                                try:
                                    src = pikepdf.Pdf.open(f, password=self.PDFpassword)
                                    break
                                except pikepdf.PasswordError:
                                    continue
                            else:
                                goBack()
                                return
                    
                    dst = pikepdf.Pdf.new()
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
                                src = pikepdf.Pdf.open(f)
                                break
                            except pikepdf.PasswordError:
                                text, ok = QInputDialog.getText(self.PDFWindow, 'Password required', 'File:\n' + fileName.name + '\nis protected by a password.\n\nProvide password:')
                                if ok and text:
                                    self.PDFpassword = str(text)
                                    try:
                                        src = pikepdf.Pdf.open(f, password=self.PDFpassword)
                                        break
                                    except pikepdf.PasswordError:
                                        continue
                                else:
                                    goBack()
                                    return

                        path = str(folderDialog + '/' + f'{fileName.stem}_reversed.pdf')
                        dst = pikepdf.Pdf.new()
                        dst.pages.extend(src.pages)
                        dst.pages.reverse()

                        dst.save(path)

                        dst.close()
                        src.close()

                finishedWindow()
            
            self.PDFWindow.optionsWidget = QWidget(self.PDFWindow)
            self.PDFWindow.optionsWidget.layout = QVBoxLayout(self.PDFWindow.optionsWidget)
            self.PDFWindow.optionsWidget.setLayout(self.PDFWindow.optionsWidget.layout)
            self.PDFWindowLayout.addWidget(self.PDFWindow.listWidget)      
            self.PDFWindowLayout.addWidget(self.PDFWindow.optionsWidget)

            if len(self.files) == 1:
                self.PDFWindow.optionsWidget.splitButton = QPushButton('Split PDF')
                self.PDFWindow.optionsWidget.splitButton.setFont(QtGui.QFont(*FONT_LIST))
                self.PDFWindow.optionsWidget.splitButton.clicked.connect(splitPDF)
                self.PDFWindow.optionsWidget.layout.addWidget(self.PDFWindow.optionsWidget.splitButton)

                self.PDFWindow.optionsWidget.reverseButton = QPushButton('Reverse PDF')
                self.PDFWindow.optionsWidget.reverseButton.setFont(QtGui.QFont(*FONT_LIST))
                self.PDFWindow.optionsWidget.reverseButton.clicked.connect(reversePDF)
                self.PDFWindow.optionsWidget.layout.addWidget(self.PDFWindow.optionsWidget.reverseButton)

                self.PDFWindow.optionsWidget.backButton = QPushButton('Back')
                self.PDFWindow.optionsWidget.backButton.setFont(QtGui.QFont(*FONT_LIST))   
                self.PDFWindow.optionsWidget.backButton.clicked.connect(goBack)
                self.PDFWindow.optionsWidget.layout.addWidget(self.PDFWindow.optionsWidget.backButton)
            
            else:
                self.PDFWindow.optionsWidget.mergeButton = QPushButton('Merge PDFs')
                self.PDFWindow.optionsWidget.mergeButton.setFont(QtGui.QFont(*FONT_LIST))
                self.PDFWindow.optionsWidget.mergeButton.clicked.connect(mergePDF)
                self.PDFWindow.optionsWidget.layout.addWidget(self.PDFWindow.optionsWidget.mergeButton)

                self.PDFWindow.optionsWidget.splitButton = QPushButton('Split PDFs')
                self.PDFWindow.optionsWidget.splitButton.setFont(QtGui.QFont(*FONT_LIST))
                self.PDFWindow.optionsWidget.splitButton.clicked.connect(splitPDF)
                self.PDFWindow.optionsWidget.layout.addWidget(self.PDFWindow.optionsWidget.splitButton)

                self.PDFWindow.optionsWidget.reverseButton = QPushButton('Reverse PDFs')
                self.PDFWindow.optionsWidget.reverseButton.setFont(QtGui.QFont(*FONT_LIST))
                self.PDFWindow.optionsWidget.reverseButton.clicked.connect(reversePDF)
                self.PDFWindow.optionsWidget.layout.addWidget(self.PDFWindow.optionsWidget.reverseButton)

                self.PDFWindow.optionsWidget.backButton = QPushButton('Back')
                self.PDFWindow.optionsWidget.backButton.setFont(QtGui.QFont(*FONT_LIST))   
                self.PDFWindow.optionsWidget.backButton.clicked.connect(goBack)
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
        self.setWindowIcon(QtGui.QIcon('logo.png'))
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
    app.setAttribute(QtCore.Qt.AA_DisableWindowContextHelpButton)
    app.setStyleSheet(stylesheet)       
    mainWindow = mainWindow()
    mainWindow.show()
    
    sys.exit(app.exec_())
