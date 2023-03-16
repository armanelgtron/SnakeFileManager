from src.common import *
from src.Tab import Tab;

class Main:
	def openWindow(this):
		f = Qt.QFile("gui/main.ui");
		f.open(Qt.QFile.ReadOnly);
		gui = QtUiTools.QUiLoader().load(f);
		f.close();
		
		def recurChildren(m):
			for w in m.children():
				setattr(gui, w.objectName(), w);
				recurChildren(w);
		recurChildren(gui);
		
		gui.setWindowTitle("");
		
		gui.status = QtWidgets.QLabel(gui);
		gui.statusBar().addWidget( gui.status );
		
		gui.splitter.setSizes([125, 400]);
		
		# remove seperator
		gui.toolBar.removeAction(gui.toolBar.actions()[0]);
		
		# add items, already created in menu bar
		# since I could find no way to do this within Qt Designer
		# without outright moving them
		gui.toolBar.addAction(gui.actionBack);
		gui.toolBar.addAction(gui.actionForward);
		gui.toolBar.addAction(gui.actionUp);
		
		# couldn't do this either
		gui.urlBar = QtWidgets.QLineEdit(gui);
		gui.toolBar.addWidget(gui.urlBar);
		
		gui.actionGo = gui.urlBar.addAction( QtGui.QIcon.fromTheme("go-jump"), QtWidgets.QLineEdit.TrailingPosition );
		
		gui.toolBar.addAction(gui.actionSearch);
		gui.toolBar.addAction(gui.actionNewTab);
		
		# remove default empty tabs
		# this could also be done from Qt Designer
		gui.dirTabs.clear();
		
		# handle signals
		
		# new window signal: create from current shown directory
		gui.actionNewWindow.triggered.connect( lambda: this.openTab( this.openWindow() ).loadDir( gui.urlBar.text() ) );
		
		# tab signals
		gui.actionNewTab.triggered.connect( lambda: this.newTab( gui ) );
		gui.dirTabs.tabCloseRequested.connect( lambda i: this.closeTab( gui, i ) );
		
		gui.dirTabs.currentChanged.connect( lambda: this.onTabChange( gui ) );
		
		# workaround for the occasional issue of bleeding eyes when reading this code
		def currTabFunc( signal, callback ):
			signal.connect( lambda *a: this.currentTabFunc( gui, callback, *a ) );
		
		currTabFunc( gui.actionBack.triggered, lambda t:t.goBack() );
		currTabFunc( gui.actionForward.triggered, lambda t:t.goForward() );
		currTabFunc( gui.actionUp.triggered, lambda t:t.goUp() );
		currTabFunc( gui.urlBar.returnPressed, lambda t:t.loadDir( gui.urlBar.text() ) );
		currTabFunc( gui.actionGo.triggered, lambda t:t.loadDir( gui.urlBar.text() ) );
		
		currTabFunc( gui.actionRefresh.triggered, lambda t:t.refresh() );
		
		currTabFunc( gui.actionNewDir.triggered, lambda t:t.makeNewDir() );
		currTabFunc( gui.actionNewFile.triggered, lambda t:t.makeNewFile() );
		
		def toggleShowHiddenFiles(shown):
			for t in this.tabs:
				for i in range(t.view.count()):
					item = t.view.item(i);
					item.setHidden( ( not shown ) and item.hidden_file );
		gui.actionShowHiddenFiles.toggled.connect(toggleShowHiddenFiles);
		
		# finally, open the window and add it to the list
		gui.show();
		
		this.wins.append(gui);
		
		gui.shortcutBar.setOpenLinks( False );
		currTabFunc( gui.shortcutBar.anchorClicked, lambda t, d:t.loadDir( d.url() ) );
		this.updateShortcuts();
		
		return gui;
	
	def updateShortcuts(this):
		std = "<!-- f -->";
		med = "<!-- m -->";
		t = """
<html>
<body>
<b>Standard</b> <br />
"""+std+"""
<br />
<b>Media</b> <br />
"""+med+"""
<br />
</body>
</html>
		""";
		
		def add(type_, path, name):
			parsed = urllib.parse.urlparse( path );
			if( parsed.scheme == "file" ):
				title = parsed.path;
			else:
				title = parsed.geturl();
			return t.replace( type_, "<a title=\""+title+"\" href=\""+path+"\">"+name+"</a>"+"<br />"+type_ );
		
		# add some known folders
		t=add( std, os.getenv("HOME"), "Home" );
		# maximum laziness, since i already wrote this in kde kmdr
		for d in ("Downloads,Documents,Music,Pictures,Video".split(",")):
			u = "file://"+(os.getenv("HOME"))+"/"+d;
			if( gio.file_new_for_uri( u ).query_exists() ):
				t=add( std, u, d );
		
		t=add( med, "file:///", "Root Directory" );
		
		# get volumes
		volmon = gio.VolumeMonitor.get();
		for v in volmon.get_volumes():
			m = v.get_mount();
			if( m ):
				t=add( med, m.get_root().get_uri(), m.get_name() );
		
		# set it in all windows
		for gui in this.wins:
			gui.shortcutBar.setText(t);
	
	def openTab(this, gui):
		tab = Tab(gui);
		this.tabs.append(tab);
		#print(tab);
		
		return tab;
	
	def newTab(this, gui):
		tab = this.openTab(gui);
		tab.loadDir( gui.urlBar.text() );
		gui.dirTabs.setCurrentIndex( tab.getTab() );
		
		return tab;
	
	def closeTab(this, *args):
		if( isinstance( args[0], Tab ) ):
			pass; #STUB
		elif( isinstance( args[0], QtWidgets.QMainWindow ) ):
			if( isinstance( args[1], int ) ):
				for t in this.tabs:
					if( t.gui == args[0] and t.getTab() == args[1] ):
						this.tabs.remove( t );
						t.close();
						import gc;
						ref = gc.get_referrers(t);
						print(sys.getrefcount(t), ref);
						break;
	
	def currentTab(this, gui):
		for t in this.tabs:
			if( gui == t.gui and gui.dirTabs.currentIndex() == t.getTab() ):
				return t;
		return None;
	
	def currentTabFunc(this, gui, callback, *a):
		for t in this.tabs:
			if( gui == t.gui and gui.dirTabs.currentIndex() == t.getTab() ):
				callback(t, *a);
	
	def onTabChange(this, gui):
		tab = this.currentTab( gui );
		if( tab ):
			tab.update();
	
	def __init__(this):
		this.wins = [];
		this.tabs = [];
		
		this.openTab( this.openWindow() ).loadDir( os.getenv("PWD") );
		
		this.updateShortcutsTimer = Qt.QTimer();
		this.updateShortcutsTimer.timeout.connect( this.updateShortcuts );
		this.updateShortcutsTimer.start( int(1*60*1e3) );
		