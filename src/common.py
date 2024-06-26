import sys, os;
import ctypes;
import re;
import time;
import urllib.parse;

from PySide2 import QtWidgets, QtGui, QtUiTools;
from PySide2 import QtCore as Qt;
QtWidgets.QApplication.exec = QtWidgets.QApplication.exec_;
#QtWidgets.QMenu.exec = QtWidgets.QMenu.exec_; #somehow this segfaults
#QtWidgets.QMenu.exec = lambda *a:QtWidgets.QMenu.exec_(*a);

from gi.repository import Gio as gio, GLib;
