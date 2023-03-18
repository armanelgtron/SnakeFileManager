from src.common import *

def filePropertiesDialog(*items):
	f = Qt.QFile("gui/fileProperties.ui");
	f.open(Qt.QFile.ReadOnly);
	u = QtUiTools.QUiLoader().load(f);
	f.close();
	
	def recurChildren(m):
		for w in m.children():
			setattr(u, w.objectName(), w);
			recurChildren(w);
	recurChildren(u);
	
	unappliedChanges = [];
	
	
	numItems = len( items );
	if( numItems == 0 ): return;
	
	files = [];
	infos = [];
	
	for item in items:
		f = gio.file_new_for_uri( item.path );
		info = f.query_info( "standard::*,time::*,access::*", gio.FileQueryInfoFlags.NONE );
		
		files.append( f );
		infos.append( info );
	
	item = items[0];
	
	f = files[0];
	info = infos[0];
	
	u.setWindowTitle( "Properties for "+f.get_basename() );
	
	### General page ###
	
	if( numItems == 1 ):
		u.fileName.setText( info.get_edit_name() );
	else:
		u.fileName.setText( str.join(", ", [ i.get_edit_name() for i in infos ]) );
		u.fileName.setEnabled( False );
	
	u.icon.setHorizontalScrollBarPolicy( Qt.Qt.ScrollBarAlwaysOff );
	u.icon.setVerticalScrollBarPolicy( Qt.Qt.ScrollBarAlwaysOff );
	try:
		for n in info.get_icon().get_names():
			icon = QtGui.QIcon.fromTheme( n );
			if( not icon.isNull() ):
				break;
	except:
		pass;
	else:
		pixmap = icon.pixmap( icon.actualSize(Qt.QSize(64, 64)) );
		icoscene = QtWidgets.QGraphicsScene();
		icoscene.addPixmap( pixmap );
		u.icon.setScene( icoscene );
	
	def getInfoRow( cat ):
		for i in range( u.generalInfo.rowCount() ):
			h = u.generalInfo.verticalHeaderItem(i).text().lower();
			if( h == cat ):
				return i;
	
	def setInfo( cat, txt, title=None ):
		r = getInfoRow( cat );
		if( r is not None ):
			item = QtWidgets.QTableWidgetItem( str(txt) );
			if( title is None ): title = txt;
			item.setToolTip( str(title) );
			u.generalInfo.setItem( r, 0, item );
	
	setInfo( "type", info.get_content_type() );
	
	try:
		openWith = gio.file_new_for_uri( item.path ).query_default_handler();
	except GLib.GError as err:
		print(err);
	else:
		setInfo( "open with", openWith.get_name() );
	
	
	setInfo( "location", f.get_uri() );
	
	# i've done... something
	def getQDateTime(gDateTime):
		try:
			return Qt.QDateTime.fromMSecsSinceEpoch( gDateTime.to_unix() * 1000 );
		except:
			return Qt.QDateTime();
	
	creationTime = getQDateTime( info.get_creation_date_time() );
	modTime = getQDateTime( info.get_modification_date_time() );
	accessTime = getQDateTime( info.get_access_date_time() );
	
	if( creationTime != modTime ):
		setInfo( "created", creationTime.toString() );
	setInfo( "modified", modTime.toString() );
	setInfo( "accessed", accessTime.toString() );
	
	# calculate size
	totalSize = 0;
	for i in infos:
		totalSize += i.get_size();
	
	sizeStr = sizeBytes = str()+" bytes";
	sizeName = ( "", "K", "M", "G", "T" );
	sizeCalc1 = sizeCalc2 = totalSize; sizeIt = 0;
	while( sizeCalc2 >= 1000 and sizeIt <= len( sizeName ) ):
		sizeIt += 1;
		sizeCalc1 /= 1024;
		sizeCalc2 /= 1000;
	
	if( sizeIt > 0 ):
		sizeStr = ( "%.1f %siB (%.1f %sB)" % ( sizeCalc1, sizeName[sizeIt], sizeCalc2, sizeName[sizeIt] ) );
	
	if( numItems > 1 ):
		sizeStr += " total";
		sizeBytes += " total";
	
	setInfo( "size", sizeStr, sizeBytes );
	
	# match volume name
	uri = f.get_uri();
	volmon = gio.VolumeMonitor.get();
	for m in volmon.get_mounts():
		if( m.get_root() ):
			m_uri = m.get_root().get_uri();
			if( uri.find(m_uri) == 0 ):
				setInfo( "volume", m.get_name() );
				break;
	
	
	### Permissions page ###
	
	permPageLoaded = [False];
	def loadPermissionsPage():
		if( permPageLoaded[0] ): return;
		permPageLoaded[0] = True;
		
		print("load permissions");
		
		# and here i thought qt would make my life easier...
		
		qfi = Qt.QFileInfo( f.get_path() );
		qfi.refresh();
		qf = Qt.QFile( f.get_path() );
		
		perm = qf.permissions();
		
		u.ownerName.setText( qfi.owner() );
		u.groupName.addItem( qfi.group() );
		
		# owner permissions
		u.ownerAccess.setCurrentIndex(
			(   int( bool( perm & Qt.QFile.ReadOwner ) ) ) ^ 
			( 2*int( bool( perm & Qt.QFile.WriteOwner ) ) )
		);
		
		# group permissions
		u.groupAccess.setCurrentIndex(
			(   int( bool( perm & Qt.QFile.ReadGroup  ) ) ) ^ 
			( 2*int( bool( perm & Qt.QFile.WriteGroup ) ) )
		);
		
		# other users' permissions
		u.otherAccess.setCurrentIndex(
			(   int( bool( perm & Qt.QFile.ReadOther  ) ) ) ^ 
			( 2*int( bool( perm & Qt.QFile.WriteOther ) ) )
		);
		
		# executable
		execOwner = bool( perm & Qt.QFile.ExeOwner );
		execGroup = bool( perm & Qt.QFile.ExeGroup );
		execOther = bool( perm & Qt.QFile.ExeOther );
		execSum = execOwner + execGroup + execOther;
		
		if( execSum == 3 ):
			u.executable.setChecked( True );
		elif( execSum == 0 ):
			u.executable.setChecked( False );
		else:
			u.executable.setCheckState( Qt.Qt.PartiallyChecked );
		
		if( qfi.isDir() ):
			u.executable.hide();
			u.labelProgram.hide();
	
	
	u.openAdvancedPermissions.setEnabled( False );
	
	
	def tabLoad():
		currWidget = u.tabWidget.currentWidget()
		if( currWidget == u.tabPermissions ):
			loadPermissionsPage();
	
	u.tabWidget.currentChanged.connect( tabLoad );
	tabLoad();
	
	
	# temp - since saving changes isnt implemented yet
	u.buttonBox.setStandardButtons( QtWidgets.QDialogButtonBox.Cancel );
	
	def apply():
		for c in unappliedChanges:
			pass;
	
	u.show();
	u.exec();
