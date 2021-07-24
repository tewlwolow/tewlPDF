#! python3
# Character Encoding: UTF-8

'''
# tewlPDF
# a simple PDF manipulator with PyQt5 GUI
'''

# Import all the required stuff
from PyQt5.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QGridLayout, 
    QWidget,
    QMainWindow,
    QApplication,
    QLabel,
    QListWidget,
    QListWidgetItem,
    #QErrorMessage,
    #QMessageBox,
    QAbstractItemView,
    QFileDialog
)
from PyQt5 import QtGui, QtCore
import sys, PyPDF2, os

# Define some semi-constans
APP_NAME = 'tewlPDF'
APP_VERSION = '0.1'
APP_AUTHOR = 'tewlwolow'
STRING_WELCOME = 'Drop it here'
STRING_WELCOME_FAIL = 'Didn\'t drop any PDF files.\nTry again!'

# Define stylesheet for main window
stylesheet = """
    mainWindow {
        background-image: url("bush.png"); 
    }
"""            

# Define Drag & Drop window
class dragDropWindow(QWidget):
    def __init__(self, PDFContainerWindow):
        super().__init__()
        self.PDFWindow = PDFContainerWindow
        self.setWindowTitle('Drag & Drop')
        self.setAcceptDrops(True)
        self.PDFWindow.setAcceptDrops(True)
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.text = QLabel(STRING_WELCOME)
        self.layout.addWidget(self.text)
        self.text.setAlignment(QtCore.Qt.AlignCenter)        
        self.text.setStyleSheet('background-image: url("twine.png"); border: 2px solid black; color: rgb(0, 0, 0)') 
        self.text.setFont(QtGui.QFont('Cambria', 42))        
        self.show()

        self.PDFWindow.setWindowTitle('PDFWindow')
        self.PDFWindowLayout = QVBoxLayout(self.PDFWindow)

        self.PDFWindow.listWidget = QListWidget()
        self.PDFWindow.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.PDFWindow.listWidget.setDragEnabled(True)
        
        self.PDFWindow.setLayout(self.PDFWindowLayout)
        self.PDFWindow.hide()

        self.PDFWindowLayout.addWidget(self.PDFWindow.listWidget)        
        
    def dragEnterEvent(self, event):
        self.text.setStyleSheet('background-image: url("twine.png"); border: 2px solid black; color: rgb(150, 80, 65)') 
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.text.setStyleSheet('background-image: url("twine.png"); border: 2px solid black; color: rgb(0, 0, 0)') 

    def dropEvent(self, event):

        self.files = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile().endswith('.pdf')]
        for f in self.files:
            QListWidgetItem(f, self.PDFWindow.listWidget)

        if len(self.files):
            self.hide()
            self.PDFWindow.show()

            def goBack():
                self.PDFWindow.hide()
                self.PDFWindow.listWidget.clear()
                self.text.setText(STRING_WELCOME)
                self.text.setStyleSheet('background-image: url("twine.png"); border: 2px solid black; color: rgb(0, 0, 0)') 
                self.show()

            # TODO: Assert that file is not encrypted
            # TODO: Specify output file
            def mergePDFs():
                if len(self.files) <= 1:
                    goBack()
                    self.text.setText('Cannot merge a single file!')
                    self.text.setStyleSheet('background-image: url("twine.png"); border: 2px solid black; color: rgb(0, 0, 0)') 
                    self.show()
                else:
                    pdfWriter = PyPDF2.PdfFileWriter()
                    self.files = [str(self.PDFWindow.listWidget.item(i).text()) for i in range(self.PDFWindow.listWidget.count())]
                    for f in self.files:
                        pdfFileObj = open(f, 'rb')
                        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
                        for pageNum in range(pdfReader.numPages):
                            pageObj = pdfReader.getPage(pageNum)
                            pdfWriter.addPage(pageObj)

                    saveDialog = QFileDialog.getSaveFileName(
                    self,
                    filter=('Portable Document Files (*.pdf)')
                    )
                    path = str(saveDialog[0])
                    outputFile = open(path, 'wb')
                    pdfWriter.write(outputFile)
                    outputFile.close()

            self.PDFWindow.mergeButton = QPushButton('Merge PDFs')
            self.PDFWindow.backButton = QPushButton('Back')
            
            self.PDFWindow.mergeButton.clicked.connect(self.PDFWindow.mergeButton.deleteLater)
            self.PDFWindow.mergeButton.clicked.connect(self.PDFWindow.backButton.deleteLater)
            self.PDFWindow.mergeButton.clicked.connect(mergePDFs)

            self.PDFWindow.backButton.clicked.connect(self.PDFWindow.backButton.deleteLater)
            self.PDFWindow.backButton.clicked.connect(self.PDFWindow.mergeButton.deleteLater)
            self.PDFWindow.backButton.clicked.connect(goBack)

            self.PDFWindowLayout.addWidget(self.PDFWindow.mergeButton)
            self.PDFWindowLayout.addWidget(self.PDFWindow.backButton)
            
        else:
            self.text.setText(STRING_WELCOME_FAIL)
            self.text.setStyleSheet('background-image: url("twine.png"); border: 2px solid black; color: rgb(0, 0, 0)') 



# Define main window
class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_gui()

    def init_gui(self):

        self.setWindowTitle(APP_NAME + ' v.' + APP_VERSION + ' by ' + APP_AUTHOR)
        self.resize(720, 480)
        self.setWindowIcon(QtGui.QIcon('tewlPDF_logo.png'))
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
    app.setStyleSheet(stylesheet)       
    mainWindow = mainWindow()
    mainWindow.show()
    
    sys.exit(app.exec_())
