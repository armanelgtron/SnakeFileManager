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
	
	
	item = items[0];
	
	f = gio.file_new_for_uri( item.path );
	
	info = f.query_info( "standard::*,time::*", gio.FileQueryInfoFlags.NONE );
	
	u.fileName.setText( info.get_edit_name() );
	

	
	# i've done... something
	def getQDateTime(gDateTime):
		return Qt.QDateTime.fromSecsSinceEpoch( gDateTime.to_unix() );
	creationTime = getQDateTime( info.get_creation_date_time() );
	modTime = getQDateTime( info.get_modification_date_time() );
	accessTime = getQDateTime( info.get_access_date_time() );
	
	
	
	# temp - since saving changes isnt implemented yet
	u.buttonBox.setStandardButtons( QtWidgets.QDialogButtonBox.Cancel );
	
	unappliedChanges = [];
	
	def apply():
		for c in unappliedChanges:
			pass;
	
	u.show();
	u.exec();
