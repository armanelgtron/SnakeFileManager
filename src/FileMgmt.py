from src.common import *

class FileMgmt:
	def __init__(this, gui):
		this.file = None;
		this.historyBack = [];
		this.historyForward = [];
		
		this.gui = gui;
		this.view = None;
	
	def getPath(this):
		if( this.file ):
			return this.file.get_path();
		else:
			return str();
	
	def getURI(this):
		if( this.file ):
			return this.file.get_uri();
		else:
			return str();
	
	def getName(this):
		if( this.file ):
			if( this.file.get_basename ):
				return this.file.get_basename();
			else:
				return this.file.get_name();
		else:
			return str();
	
	
	def update(this):
		pass;
	
	
	def onFileEnter(this, item):
		if( item.file_type == gio.FileType.DIRECTORY ):
			this.loadDir( item.path );
		else:
			f = gio.file_new_for_uri( item.path );
			a = f.query_default_handler();
			a.launch_uris([f.get_uri()]);
	
	def onFileRename(this, txt):
		print(txt, txt.text());
		
		# since we use this a lot here
		def dispErr(text):
			def dispErrReal():
				msg = QtWidgets.QMessageBox();
				msg.setIcon( QtWidgets.QMessageBox.Warning );
				msg.setText( text );
				msg.setWindowTitle("Unable to rename file");
				msg.exec();
			# we have to display the error after we're out of this function
			# else it may bring down our whole application
			# qt issues
			t = Qt.QTimer();
			t.setSingleShot( True );
			t.timeout.connect(dispErrReal);
			t.start(1);
			this.__renameErrMsg = t;
		
		# find the file to be renamed
		# maybe i have no imagination
		item = None;
		for i in range(this.view.count()):
			item_ = this.view.item(i);
			if( item_.text() == txt.text() ):
				if( item is not None ):
					dispErr("A file by the same name already exists.");
					
					# good enough... hopefully
					for ii in this.view.selectedItems():
						ii.setText( Qt.QUrl(ii.path).fileName() );
						if( ii.flags() & Qt.Qt.ItemIsEditable ):
							ii.setFlags( ii.flags() ^ Qt.Qt.ItemIsEditable );
					
					return;
				item = item_;
		
		# i can't imagine
		assert( item.flags() & Qt.Qt.ItemIsEditable );
		item.setFlags( item.flags() ^ Qt.Qt.ItemIsEditable );
		
		#print( urllib.parse.urljoin( this.getURI()+"/", item.text() ) );
		
		# get the old and new paths
		f = gio.file_new_for_uri( item.path );
		dest = gio.file_new_for_uri( urllib.parse.urljoin( this.getURI()+"/", item.text() ) );
		
		# simple validity check
		if( txt.text().find("/") >= 0 ):
			dispErr("Filenames cannot contain slashes.");
			item.setText( f.get_basename() );
			return;
		
		# safety check
		if( dest.get_basename() != txt.text() ):
			dispErr("Possibly illegal filename.");
			item.setText( f.get_basename() );
			return;
		
		if( f.get_basename() == dest.get_basename() ):
			# looks the same to me
			this.gui.statusBar().showMessage("Cancelled.", 5000);
			return;
		
		# do it
		try:
			f.move( dest, gio.FileCopyFlags.NONE );
		except GLib.GError as e:
			dispErr( str(e) );
			item.setText( f.get_basename() );
		else:
			# update details
			item.path = dest.get_uri();
			this.gui.statusBar().showMessage("File renamed successfully.", 5000);
	
	def doFileDelete(this, items):
		assert( len(items) > 0 );
		
		msg = "Permanently delete %s ?\n\nThis cannot be undone!"
		
		if( len(items) == 1 ):
			msg = msg % ("\""+(items[0].text())+"\"");
		else:
			msg = msg % (str(len(items))+" selected items");
		
		r = QtWidgets.QMessageBox.warning(this.gui, " ", msg,
			QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No
		);
		if( r == QtWidgets.QMessageBox.Yes ):
			for i in items:
				f = gio.file_new_for_uri( i.path );
				
				# we really need to get this right
				# checks to make sure we're deleting the file from the right folder
				assert( this.getURI() == f.get_parent().get_uri() );
				assert( f.get_parent().hash() == this.file.hash() );
				# check to make sure the file names match, just in case
				assert( f.get_basename() == i.text() );
				
				# ok, now actually delete it
				try:
					f.delete();
				except GLib.GError as e:
					q = QtWidgets.QMessageBox();
					q.setIcon(QtWidgets.QMessageBox.Warning);
					q.setWindowTitle(" ");
					q.setText("Failure deleting \""+f.get_basename()+"\"");
					q.setInformativeText( str(e) );
					q.exec();
				else:
					this.view.takeItem( this.view.row( i ) );
	
	def doFileTrash(this, items):
		for i in items:
			f = gio.file_new_for_uri( i.path );
			try:
				f.trash();
			except GLib.GError as e:
				q = QtWidgets.QMessageBox();
				q.setIcon(QtWidgets.QMessageBox.Warning);
				q.setWindowTitle(" ");
				q.setText( "Failure trashing \""+f.get_basename()+"\"" );
				q.setInformativeText( str(e) );
				q.exec();
			else:
				this.view.takeItem( this.view.row( i ) );
	
	def makeNewFile(this):
		i = 0; fileNotCreated = True;
		while( fileNotCreated ):
			if( i >= 99 ): break; # give up
			name = "untitled";
			if( i != 0 ):
				name += str( i+1 );
			f = gio.file_new_for_uri( urllib.parse.urljoin( this.getURI()+"/", name ) );
			try:
				f.create( gio.FileCreateFlags.NONE );
			except GLib.GError as e:
				if( e.matches(gio.io_error_quark(), gio.IOErrorEnum.EXISTS) ):
					i += 1;
					continue;
				q = QtWidgets.QMessageBox();
				q.setIcon(QtWidgets.QMessageBox.Warning);
				q.setWindowTitle(" ");
				q.setText( "Couldn't create new file" );
				q.setInformativeText( str(e) );
				q.exec();
				return;
			else:
				fileNotCreated = False;
		
		item = QtWidgets.QListWidgetItem( QtGui.QIcon.fromTheme( "unknown" ), "" );
		
		# set expected parameters
		item.path = f.get_uri();
		item.is_hidden_file = False;
		item.file_type = gio.FileType.REGULAR;
		
		# add it, then let the user set the name
		this.view.addItem(item);
		item.setFlags( item.flags() | Qt.Qt.ItemIsEditable );
		this.view.editItem( item );
	
	def makeNewDir(this):
		i = 0; fileNotCreated = True;
		while( fileNotCreated ):
			if( i >= 99 ): break; # give up
			name = "newdir";
			if( i != 0 ):
				name += str( i+1 );
			f = gio.file_new_for_uri( urllib.parse.urljoin( this.getURI()+"/", name ) );
			try:
				f.make_directory();
			except GLib.GError as e:
				if( e.matches(gio.io_error_quark(), gio.IOErrorEnum.EXISTS) ):
					i += 1;
					continue;
				q = QtWidgets.QMessageBox();
				q.setIcon(QtWidgets.QMessageBox.Warning);
				q.setWindowTitle(" ");
				q.setText( "Couldn't create new directory" );
				q.setInformativeText( str(e) );
				q.exec();
				return;
			else:
				fileNotCreated = False;
		
		item = QtWidgets.QListWidgetItem( QtGui.QIcon.fromTheme( "folder" ), "" );
		
		# set expected parameters
		item.path = f.get_uri();
		item.is_hidden_file = False;
		item.file_type = gio.FileType.DIRECTORY;
		
		# add it, then let the user set the name
		this.view.addItem(item);
		item.setFlags( item.flags() | Qt.Qt.ItemIsEditable );
		this.view.editItem( item );
	
	def onDroppedFiles(this, e):
		if( e.mimeData().hasUrls() ):
			e.setDropAction(Qt.Qt.CopyAction)
			e.accept();
			print(e.mimeData().urls())
			
			menu = QtWidgets.QMenu();
			
			path = this.getURI();
			path_str = "current dir.";
			menu.addAction( "%i file(s) to %s"%( len(e.mimeData().urls()), path_str ) ).setEnabled( False );
			
			actCopy = menu.addAction( QtGui.QIcon.fromTheme( "edit-copy" ), "Copy" );
			actMove = menu.addAction( QtGui.QIcon.fromTheme( "edit-find-replace" ), "Move" );
			actLink = menu.addAction( QtGui.QIcon.fromTheme( "insert-link" ), "Link");
			
			a = menu.exec_( this.view.mapToGlobal( e.pos() ) );
			
			def errMsg(action, url, err):
				q = QtWidgets.QMessageBox();
				q.setIcon(QtWidgets.QMessageBox.Warning);
				q.setWindowTitle(" ");
				if( url.scheme() == "file" ):
					disp = url.path();
				else:
					disp = url.url();
				q.setText( "Failure "+action+" \""+disp+"\"" );
				q.setInformativeText( err );
				q.exec();
			
			def addFile(f):
				type_ = f.query_file_type( gio.FileQueryInfoFlags.NONE );
				if( type_ == gio.FileType.DIRECTORY ):
					icon = QtGui.QIcon.fromTheme( "folder" );
				else:
					icon = QtGui.QIcon.fromTheme( "unknown" );
				item = QtWidgets.QListWidgetItem( icon, f.get_basename() );
				
				# set expected parameters
				item.path = f.get_uri();
				item.is_hidden_file = False;
				item.file_type = type_;
				
				this.view.addItem(item);
				
				return item;
			
			if( a == actCopy ):
				print("cp");
				action = "copying";
				for u in e.mimeData().urls():
					f = gio.file_new_for_uri( u.url() );
					dest = gio.file_new_for_uri( urllib.parse.urljoin( path+"/", u.fileName() ) );
					try:
						f.copy( dest, gio.FileCopyFlags.NONE );
					except GLib.GError as e:
						errMsg(action, u, str(e));
					else:
						if( path == this.getURI() ):
							addFile(dest);
			
			elif( a == actMove ):
				print("mv");
				action = "moving";
				for u in e.mimeData().urls():
					f = gio.file_new_for_uri( u.url() );
					dest = gio.file_new_for_uri( urllib.parse.urljoin( path+"/", u.fileName() ) );
					try:
						f.move( dest, gio.FileCopyFlags.NONE );
					except GLib.GError as e:
						errMsg(action, u, str(e));
					else:
						if( path == this.getURI() ):
							addFile(dest);
			
			elif( a == actLink ):
				print("ln");
				action = "creating link"
				for u in e.mimeData().urls():
					#f = gio.file_new_for_uri( u.url() );
					dest = gio.file_new_for_uri( urllib.parse.urljoin( path+"/", u.fileName() ) );
					try:
						dest.make_symbolic_link( u.url() );
					except GLib.GError as e:
						errMsg(action, u, str(e));
					else:
						if( path == this.getURI() ):
							addFile(dest);
	
	
	def openDir(this, name):
		parsed = urllib.parse.urlparse( name );
		
		if( parsed.path == "" ):
			return False;
		
		if( parsed.scheme == "" ):
			dir_ = "file://"+name;
		else:
			dir_ = name;
		
		f = gio.file_new_for_uri(dir_);
		
		return f;
	
	def loadDir(this, name):
		f = this.openDir(name);
		if( f ):
			this.loadFile( f );
		return this;
	
	def loadFile(this, f):
		if( this.file and this.file.hash() != f.hash() ):
			this.historyBack.append( this.file );
			this.historyForward.clear();
		
		return this.loadFileCore(f);

	def loadFileCore(tab, f, from_=None):
		tab.file = f;
		
		opts = [
			"standard::name",
			"standard::type",
			"standard::icon",
			"standard::is-hidden",
			"standard::is-symlink",
		];
		
		tab.gui.statusBar().showMessage("Please wait...");
		
		# prepare the dir view for new items
		tab.view.clear();
		tab.view.repaint();
		
		# request mount, just in case
		l = GLib.MainLoop();
		f.mount_enclosing_volume(gio.MountMountFlags.NONE, None, None, lambda *a:l.quit(), l)
		l.run();
		
		t = time.time()+0.25;
		msg = "Please wait";
		
		# no, not THAT uNk
		unk = QtGui.QIcon.fromTheme( "unknown" );
		
		# get the list of files
		try:
			c = f.enumerate_children( str.join( ",", opts ), gio.FileQueryInfoFlags.NONE, None );
		except GLib.GError as e:
			tab.update();
			q = QtWidgets.QErrorMessage();
			q.setWindowTitle("Whoops");
			q.showMessage( str(e) );
			q.exec();
		else:
			for f in c:
				# find a working icon from the list
				for n in f.get_icon().get_names():
					icon = QtGui.QIcon.fromTheme( n );
					if( not icon.isNull() ):
						break;
				if( icon.isNull() ):
					icon = unk;
				
				# add the file
				item = QtWidgets.QListWidgetItem( icon, f.get_name() );
				item.path = urllib.parse.urljoin( tab.getURI()+"/", f.get_name() );
				item.hidden_file = f.get_is_hidden();
				item.file_type = f.get_file_type();
				if( f.get_is_symlink() or item.hidden_file ):
					font = item.font();
					font.setItalic( f.get_is_symlink() );
					font.setStrikeOut( item.hidden_file );
					item.setFont(font);
				tab.view.addItem(item);
				if( not tab.gui.actionShowHiddenFiles.isChecked() ):
					item.setHidden( item.hidden_file );
				
				if( t < time.time() ):
					t = time.time()+1;
					tab.gui.statusBar().showMessage(msg);
					msg += ".";
					tab.view.repaint();
			
			tab.update();
		
		tab.gui.statusBar().clearMessage();
		
		return tab;
