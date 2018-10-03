import os,stat
from gi.repository import Gtk, GObject,Gedit,Gio
from gi.repository.GdkPixbuf import Pixbuf
ACCELERATOR=['<Alt>k']

class NimbusAppActivatable(GObject.Object,Gedit.AppActivatable):
    __gtype_name__="nimbus"
    app=GObject.Property(type=Gedit.App)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        self.app.set_accels_for_action("win.nimbus",ACCELERATOR)
        self.menu_ext=self.extend_menu("tools-section")
        item=Gio.MenuItem.new("Nimbus","win.nimbus")
        self.menu_ext.prepend_menu_item(item)

    def do_deactivate(self):
        self.app.set_accels_for_action("win.nimbus",[])
        self.menu_ext=None

    def do_update_state(self):
        pass


class NimbusWindowActivatable(GObject.Object,Gedit.WindowActivatable):
    window=GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        action=Gio.SimpleAction(name="nimbus")
        action.connect("activate",self.on_nimbus_activate)
        '''filebrowser=Gtk.Button("click me")
        pane=self.window.get_side_panel()
        pane.add_titled(filebrowser,"Project Browser","Browser")
        pane.show_all()'''
        self.window.add_action(action)

    def do_deactivate(self):
        pass
    def on_nimbus_activate(self,action,parameter,user_data=None):
        projectDialog=Gtk.FileChooserDialog("Please select a folder",self.window,
                                            Gtk.FileChooserAction.SELECT_FOLDER,
                                            (Gtk.STOCK_CANCEL,Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN,Gtk.ResponseType.OK))
        response=projectDialog.run()
        if response==Gtk.ResponseType.OK:
            self.projectDirectory=projectDialog.get_filename()
            fileSystemTreeStore=Gtk.TreeStore(str,Pixbuf)
            self.populateFileSystemTreeStore(fileSystemTreeStore,self.projectDirectory)
            fileSystemTreeView=Gtk.TreeView(fileSystemTreeStore)

            treeViewCol=Gtk.TreeViewColumn("File")

            colCellText=Gtk.CellRendererText()
            colCellImg = Gtk.CellRendererPixbuf()

            treeViewCol.pack_start(colCellImg, False)
            treeViewCol.pack_start(colCellText,True)

            treeViewCol.add_attribute(colCellText, "text", 0)
            treeViewCol.add_attribute(colCellImg, "pixbuf", 1)

            fileSystemTreeView.append_column(treeViewCol)
            # add "on expand" callback
            fileSystemTreeView.connect("row-expanded", self.onRowExpanded)
            # add "on collapse" callback
            fileSystemTreeView.connect("row-collapsed", self.onRowCollapsed)
            # add "on activated" callback
            fileSystemTreeView.connect("row-activated", self.onRowActivated)
            scrollView = Gtk.ScrolledWindow()
            scrollView.add(fileSystemTreeView)

            pane=self.window.get_side_panel()
            pane.add_titled(scrollView,"pbrowser","Nimbus")
            pane.show_all()
        else:
            print("cancel clicked")
        projectDialog.destroy()
    def populateFileSystemTreeStore(self,treeStore,path,parent=None):
        itemCounter=0
        for item in os.listdir(path):
            itemFullName=os.path.join(path,item)
            itemMeta=os.stat(itemFullName)
            itemIsFolder=stat.S_ISDIR(itemMeta.st_mode)
            itemIcon=Gtk.IconTheme.get_default().load_icon("folder" if itemIsFolder else "empty",22,0)
            currentIter=treeStore.append(parent,[item,itemIcon])
            if itemIsFolder:
                treeStore.append(currentIter,[None,None])
            itemCounter+=1
        if itemCounter < 1:
            treeStore.append(parent,[None,None])
    def onRowExpanded(self,treeView, treeIter, treePath):
        # get the associated model
        treeStore = treeView.get_model()
        currentPath=''
        iterParent=treeIter
        while iterParent:
            currentPath=os.path.join(treeStore.get_value(iterParent,0),currentPath)
            iterParent=treeStore.iter_parent(iterParent)
        # get the full path of the position
        newPath = os.path.join(self.projectDirectory,currentPath)
        # populate the subtree on curent position
        self.populateFileSystemTreeStore(treeStore, newPath, treeIter)
        # remove the first child (dummy node)
        treeStore.remove(treeStore.iter_children(treeIter))
    def onRowCollapsed(self,treeView, treeIter, treePath):
        # get the associated model
        treeStore = treeView.get_model()
        # get the iterator of the first child
        currentChildIter = treeStore.iter_children(treeIter)
        # loop as long as some childern exist
        while currentChildIter:
            # remove the first child
            treeStore.remove(currentChildIter)
            # refresh the iterator of the next child
            currentChildIter = treeStore.iter_children(treeIter)
        # append dummy node
        treeStore.append(treeIter, [None, None])
    def onRowActivated(self,treeView,treePath,treeCol):
        treeStore=treeView.get_model()
        treeIter=treeStore.get_iter(treePath)
        currentPath=''
        iterParent=treeIter
        while iterParent:
            currentPath=os.path.join(treeStore.get_value(iterParent,0),currentPath)
            iterParent=treeStore.iter_parent(iterParent)
        currentPath = os.path.join(self.projectDirectory, currentPath)[:-1]
        itemMeta=os.stat(currentPath).st_mode
        isDir=stat.S_ISDIR(itemMeta)
        if not isDir:
            loadFile=Gio.File.new_for_path(currentPath)
            self.window.create_tab_from_location(loadFile,None,0,0,False,True)
            
