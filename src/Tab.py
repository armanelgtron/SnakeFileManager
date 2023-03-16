from src.common import *

from src.DirectoryView import DirectoryView;
from src.FileMgmt import FileMgmt;

class Tab(FileMgmt):
	def __init__(this, gui):
		super().__init__(gui);
		
		this.view = DirectoryView(gui);
		
		this.view.itemDoubleClicked.connect( this.onFileEnter );
		this.view.itemDelegate().commitData.connect( this.onFileRename );
		
		this.view.s.callDelete.connect( this.doFileDelete );
		this.view.s.callTrash.connect( this.doFileTrash );
		
		this.view.s.filesDropped.connect( this.onDroppedFiles );
		
		gui.dirTabs.addTab(this.view, "New Tab");
	
	def __del__(this):
		print("tab deleted");
	
	def close(this):
		this.historyBack.clear();
		this.historyForward.clear();
		this.view.clear();
		this.file = None;
		this.gui.dirTabs.removeTab( this.getTab() );
	
	def getTab(this):
		return this.gui.dirTabs.indexOf(this.view);
	
	def getPathForBar(this):
		if( this.file ):
			parsed = urllib.parse.urlparse( this.getURI() );
			if( parsed.scheme == "file" ):
				return parsed.path;
			else:
				return parsed.geturl();
		else:
			return str();
	
	def select(this, *names):
		for i in range(this.view.count()):
			item = this.view.item(i);
			try: names.index( item.text() )
			except ValueError: item.setSelected( False );
			else:
				item.setSelected( True );
				this.view.scrollToItem( item );
	
	def update(this):
		id_ = this.getTab();
		if( this.file ):
			this.gui.dirTabs.setTabText( id_, this.getName() );
			if( this.gui.dirTabs.currentIndex() == id_ ):
				this.gui.urlBar.setText( this.getPathForBar() );
				this.gui.setWindowTitle( this.getName() );
				this.gui.actionBack.setEnabled( len( this.historyBack ) > 0 );
				this.gui.actionForward.setEnabled( len( this.historyForward ) > 0 );
				this.gui.status.setText( str(this.view.count())+" files" );
		return this;
	
	
	def refresh(this):
		selected = [ i.text() for i in this.view.selectedItems() ];
		this.loadFileCore( this.file );
		this.select( selected );
	
	def goUp(this):
		name = this.getName();
		
		this.loadFile( this.file.get_parent() );
		
		this.select( name );
	
	def goBack(this):
		i = len(this.historyBack)-1;
		if( i >= 0 ):
			f = this.historyBack[i];
			
			name = this.getName();
			
			this.historyBack.remove( f );
			this.historyForward.append( this.file );
			
			this.loadFileCore( f );
			
			this.select( name );
	
	def goForward(this):
		i = len(this.historyForward)-1;
		if( i >= 0 ):
			f = this.historyForward[i];
			
			name = this.getName();
			
			this.historyForward.remove( f );
			this.historyBack.append( this.file );
			
			this.loadFileCore( f );
			
			this.select( name );
