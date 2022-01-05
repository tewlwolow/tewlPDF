#! python3
# Character Encoding: UTF-8

'''
# tewlPDF
# a simple PDF manipulator with PyQt5 GUI

# Shortcut to recompile resources:
# pyrcc5 resources.qrc -o resources.py
'''

# TODO: add slicing
# TODO: add cutting
# TODO: add extracting

##############################################################################################################################

import os
import sys

from pathlib import Path

from pikepdf import PasswordError, Pdf
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QFont, QFontDatabase, QIcon
# Import all the required stuff
# Keeping it tidy, it gets up bloated anyway
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QDialog,
							 QFileDialog, QGridLayout, QHBoxLayout,
							 QInputDialog, QLabel, QListWidget,
							 QListWidgetItem, QMainWindow, QPushButton,
							 QSizeGrip, QStyle, QVBoxLayout, QWidget, qApp)

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
APP_VERSION = '0.9'
APP_AUTHOR = 'tewlwolow'

# Messages
STRING_DROP = 'DROP IT HERE'
STRING_DROP_FAIL = 'Didn\'t drop any PDF files.\nTry again!'
STRING_FINISHED = 'It\'s done!'

STRING_SPLIT = 'SPLIT'
STRING_MERGE = 'MERGE'
STRING_REVERSE = 'REVERSE'
STRING_BACK = 'BACK'
STRING_CUT = 'CUT'

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

# Fonts
FONT_MAIN = ['Darker Grotesque', 60]
FONT_LIST = ['Zen Maru Gothic', 16]

# Define stylesheets
# Using paths from resource_rc cuz, again, auto-py-to-exe
STYLESHEET_CONTAINER = """
	MainWindow {
		background-image: url(:tewl_bg_main);
	}
"""
STYLESHEET_MAIN = 'background-color: rgba(255,255,255,0.15); border-radius: 50px; color: rgb(0, 0, 0)'
STYLESHEET_BUTTON = 'background-color: rgba(255, 25, 30, 0.3); padding: 10px 10px 10px 10px; border: 2px solid rgba(0,0,0,0.2); border-radius: 25%; color: rgb(0, 0, 0)'
STYLESHEET_BUTTON_SECONDARY = 'background-color: rgba(120, 80, 120, 0.2); padding: 10px 10px 10px 10px; border: 1px solid rgba(0,0,0,0.2); border-radius: 25%; color: rgb(0, 0, 0)'
STYLESHEET_LIST = 'background-color: rgba(255,255,255,0.3); border-radius: 25px; color: rgb(0, 0, 0); padding: 15px 15px 15px 15px;'
STYLESHEET_HIGHLIGHT = 'background-color: rgba(255,255,255,0.15); border-radius: 50px; color: rgba(255, 255, 255, 0.6)'

# Define window structure


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
		self.backButton = QPushButton('Again')
		self.backButton.setFont(QFont(*FONT_LIST))
		self.backButton.clicked.connect(restart)
		self.backButton.setStyleSheet(STYLESHEET_BUTTON_SECONDARY)
		self.layout.addWidget(self.backButton)
		self.setLayout(self.layout)


class FilelistScreen(QWidget):
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
		self.listWidget.itemDoubleClicked.connect(self.removeListItem)

		self.setLayout(self.layout)

	def setFiles(self, files):
		self.__files = files

	def getFiles(self):
		return self.__files

	def purgeFiles(self):
		self.__files = []

	def removeListItem(self, item):
		self.__files.remove(item.text())
		item.setHidden(True)
		newFiles = self.__files
		self.clearData()
		self.setFiles(newFiles)
		self.parseFiles()
		if len(self.__files) == 0:
			self.goBack()

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

	# Define cutting operation
	def cutPDF(self):

		# Nothing works here for hiding the ugly bar...
		inputWindow = QInputDialog(self)

		limit, ok = inputWindow.getInt(
		   self, 'Give details', 'The last page to be included in the first file:')

		if not ok or limit == 0:
			self.hide()
			self.show()
			return

		f = self.__files[0]
		fileName = Path(f)
		self.hide()

		folderDialog = QFileDialog.getExistingDirectory(
			self, 'Select Folder')

		if not folderDialog:
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

		path_1 = str(folderDialog + '/' +
						   f'{fileName.stem}_part1.pdf')

		path_2 = str(folderDialog + '/' +
						   f'{fileName.stem}_part2.pdf')

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
				(self.style().standardIcon(QStyle.SP_FileDialogDetailedView)), f, self.listWidget)

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
				self.optionsWidget.cutButton = QPushButton(STRING_CUT)
				self.optionsWidget.cutButton.setFont(
					QFont(*FONT_LIST))
				self.optionsWidget.cutButton.clicked.connect(
					self.cutPDF)
				self.optionsWidget.cutButton.setToolTip(
					'Cut PDF in two')
				self.optionsWidget.layout.addWidget(
					self.optionsWidget.cutButton)
				self.optionsWidget.cutButton.setStyleSheet(STYLESHEET_BUTTON)

			if len(self.__files) > 1:
				self.optionsWidget.mergeButton = QPushButton(STRING_MERGE)
				self.optionsWidget.mergeButton.setFont(
					QFont(*FONT_LIST))
				self.optionsWidget.mergeButton.clicked.connect(
					self.mergePDF)
				self.optionsWidget.mergeButton.setToolTip(
					'Merge files into one PDF')
				self.optionsWidget.layout.addWidget(
					self.optionsWidget.mergeButton)
				self.optionsWidget.mergeButton.setStyleSheet(STYLESHEET_BUTTON)

			self.optionsWidget.splitButton = QPushButton(STRING_SPLIT)
			self.optionsWidget.splitButton.setFont(
				QFont(*FONT_LIST))
			self.optionsWidget.splitButton.clicked.connect(
				self.splitPDF)
			self.optionsWidget.splitButton.setToolTip(
				'Split files into single-page PDFs')
			self.optionsWidget.layout.addWidget(
				self.optionsWidget.splitButton)
			self.optionsWidget.splitButton.setStyleSheet(STYLESHEET_BUTTON)

			self.optionsWidget.reverseButton = QPushButton(STRING_REVERSE)
			self.optionsWidget.reverseButton.setFont(
				QFont(*FONT_LIST))
			self.optionsWidget.reverseButton.clicked.connect(
				self.reversePDF)
			self.optionsWidget.reverseButton.setToolTip(
				'Reverse page order')
			self.optionsWidget.layout.addWidget(
				self.optionsWidget.reverseButton)
			self.optionsWidget.reverseButton.setStyleSheet(
				STYLESHEET_BUTTON)

			self.optionsWidget.backButton = QPushButton(STRING_BACK)
			self.optionsWidget.backButton.setFont(
				QFont(*FONT_LIST))
			self.optionsWidget.backButton.clicked.connect(
				self.goBack)
			self.optionsWidget.backButton.setToolTip(
				'Go back to welcome screen')
			self.optionsWidget.layout.addWidget(
				self.optionsWidget.backButton)
			self.optionsWidget.backButton.setStyleSheet(
				STYLESHEET_BUTTON_SECONDARY)


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

		button = QPushButton(QIcon(':/tewl_logo'), "")
		button.setStyleSheet('background-color: transparent; margin-top: 20px')
		button.setIconSize(QSize(100, 100))
		button.clicked.connect(self.infoClicked)
		self.layout.addWidget(button, 0, 0, 1, 1,
							  alignment=Qt.AlignCenter | Qt.AlignTop)

	def infoClicked(self, b):

		dlg = QDialog(self)
		dlg.setWindowTitle("Info")
		dlg.setWindowFlags(Qt.SplashScreen)
		dlg.layout = QGridLayout()

		dlg.text = QLabel()
		dlg.text.setOpenExternalLinks(True)
		dlg.text.setTextFormat(Qt.RichText)
		dlg.text.setText(STRING_INFO.format(APP_VERSION))
		dlg.text.setAlignment(Qt.AlignCenter)
		dlg.text.setFont(QFont(*FONT_LIST))

		dlg.setStyleSheet('background-color: rgb(50,10,40); color: beige')

		dlg.layout.addWidget(dlg.text)
		dlg.setLayout(dlg.layout)
		dlg.setWindowOpacity(0.95)

		dlg.mouseDoubleClickEvent = lambda event: dlg.hide()

		dlg.exec()

	def dragEnterEvent(self, event):
		# Define highlight style
		self.text.setStyleSheet(STYLESHEET_HIGHLIGHT)

		# Bounce off mouse clicks just in case something weird happens
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
class MainWindow(QMainWindow):
	def __init__(self):
		super().__init__()
		self.initGUI()

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

	def initGUI(self):
		self.setWindowTitle(APP_NAME + ' v.' +
							APP_VERSION + ' by ' + APP_AUTHOR)
		self.setStyleSheet(STYLESHEET_CONTAINER)
		self.resize(1200, 800)
		self.setWindowIcon(QIcon(':/tewl_logo'))
		self.window = QWidget()
		self.layout = QGridLayout()
		self.setCentralWidget(self.window)
		self.setWindowFlags(Qt.FramelessWindowHint)
		self.window.setLayout(self.layout)

		self.mouseDoubleClickEvent = lambda event: qApp.quit()
		self.clicked = False

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


# Initialise the programme
if __name__ == '__main__':
	app = QApplication([])
	app.setAttribute(Qt.AA_DisableWindowContextHelpButton)

	QFontDatabase.addApplicationFont(':/tewl_h_font')
	QFontDatabase.addApplicationFont(':/tewl_p_font')

	mainWindow = MainWindow()
	mainWindow.show()

	sys.exit(app.exec_())
