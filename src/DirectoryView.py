from src.common import *

class DirectoryView(QtWidgets.QListWidget):
	def __init__(this, win):
		super().__init__();
		this.updateProperties();
		this.gui = win;
		this.oldSize = this.size();
		
		# what a disaster
		class signals(Qt.QObject):
			filesDropped = Qt.Signal(QtGui.QDropEvent);
			callDelete = Qt.Signal(list);
			callTrash = Qt.Signal(list);
		this.s = signals();
	
	def updateProperties(this):
		# TODO: make this user customizable?
		this.setSelectionMode( QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection );
		#this.setViewMode( QtWidgets.QListView.IconMode );
		#this.setFlow( QtWidgets.QListView.LeftToRight );
		this.setLayoutMode( QtWidgets.QListView.Batched );
		this.setWrapping( True );
		this.setUniformItemSizes( False );
		this.setSelectionRectVisible( True );
		this.setResizeMode( QtWidgets.QListView.Adjust );
		this.setDragDropMode( QtWidgets.QAbstractItemView.DragDrop );
	
	def mimeTypes(this):
		return ["text/uri-list"];
	
	def mimeData(this, items):
		mime = Qt.QMimeData();
		mime.setUrls([ Qt.QUrl(u.path) for u in items ]);
		return mime;
	
	def startDrag(this, a):
		super( DirectoryView, this ).startDrag(a);
	
	def dragEnterEvent(this, e):
		#super( DirectoryView, this ).dragEnterEvent(e);
		#print(e.mimeData().urls())
		if( e.mimeData().hasUrls() ):
			e.accept();
	
	def dragMoveEvent(this, e):
		#super( DirectoryView, this ).dragMoveEvent(e);
		#print(e.mimeData().urls())
		if( e.mimeData().hasUrls() ):
			e.setDropAction(Qt.Qt.CopyAction)
			e.accept();
	
	def dragEvent(this, e):
		#super( DirectoryView, this ).dragEvent(e);
		print(e.mimeData().urls())
	
	def dropEvent(this, e):
		#super( DirectoryView, this ).dropEvent(e);
		this.s.filesDropped.emit(e);
	
	def contextMenuEvent(this, e):
		menu = QtWidgets.QMenu();
		
		selected = this.selectedItems();
		
		if( len( selected ) == 0 ):
			createNew = menu.addMenu( this.gui.menuCreateNew.title() );
			for i in this.gui.menuCreateNew.actions():
				createNew.addAction( i );
			
			menu.addSeparator();
			
			paste = menu.addAction( this.gui.actionPaste.icon(), this.gui.actionPaste.text() );
		else:
			cut = menu.addAction( this.gui.actionCut.icon(), this.gui.actionCut.text() );
			copy = menu.addAction( this.gui.actionCopy.icon(), this.gui.actionCopy.text() );
			
			menu.addSeparator();
			
			trash = menu.addAction( "Move to Trash" );
			delete = menu.addAction( "Delete file" );
			
			menu.addSeparator();
			
			rename = menu.addAction( "Rename..." );
		
		a = menu.exec_( this.mapToGlobal( e.pos() ) );
		
		if( len( selected ) != 0 ):
			if( a == rename ):
				if( len( selected ) == 1 ):
					item = selected[0];
					item.setFlags( item.flags() | Qt.Qt.ItemIsEditable );
					this.editItem( item );
				else:
					pass;
			elif( a == delete ):
				this.s.callDelete.emit( [*selected] );
			elif( a == trash ):
				this.s.callTrash.emit( [*selected] );
		else:
			pass;
	
	def updateGeometries(this):
		# store values for later... you'll see...
		h = this.horizontalScrollBar();
		h_v = h.value(); h_r = ( h.minimum(), h.maximum() );
		
		# mate
		super( DirectoryView, this ).updateGeometries();
		
		# instead of scrolling by item (which can get quite wide)
		# scroll by pixels, which makes more sense here
		this.setHorizontalScrollMode( QtWidgets.QAbstractItemView.ScrollPerPixel );
		this.horizontalScrollBar().setSingleStep(20); # random value that feels good
		
		# hacky workaround for weird bug causing inability to scroll
		# and constant flicker on large directories
		if( this.oldSize != this.size() ):
			this.horizontalScrollBar().setRange(*h_r);
			this.horizontalScrollBar().setValue(h_v);
			this.oldSize = this.size();
		# needs more fixing to hold scrollbar position better
