#!/usr/bin/python3

from src.common import *

from src.Main import Main;

def main():
	app = QtWidgets.QApplication(sys.argv);
	
	def handle_exception(exc, val, tb):
		sys.__excepthook__(exc, val, tb);
		if( app.instance().thread() == Qt.QThread.currentThread() ):
			try:
				window.thread.requestInterruption();
			except:
				pass;
			gui_exception(exc, val, tb);
		else:
			window.worker.fatalError.emit(exc, val, tb);
	
	def gui_exception(exc, val, tb):
		import traceback;
		msg = QtWidgets.QMessageBox();
		msg.setIcon(QtWidgets.QMessageBox.Critical);
		msg.setText("<b>An internal error occurred.</b> <br /> This is probably a bug, please send a bug report.");
		msg.setInformativeText(str.join("\n", traceback.format_exception(exc, val, tb)));
		msg.setWindowTitle("Internal Error");
		msg.exec();
	
	sys.excepthook = handle_exception;
	
	m = Main();
	
	app.exec();

if(__name__ == "__main__"):
	main();