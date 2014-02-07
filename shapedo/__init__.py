bl_info = {
    "name" : "ShapeDo",
    "author" : "Guy Sheffer",
    "version" : (0, 0, 2),
    "blender" : (2, 68, 0),
    "category" : "Tools",
    "location" : "3D View > Tools",
    "wiki_url" : "https://github.com/shapedo/shapedo-blender-plugin",
    "tracker_url" : "https://github.com/shapedo/shapedo-blender-plugin/issues",
    "description" : "An addon to work on projects on ShapeDo from within Blender"}

import bpy
import json
import os.path
import urllib.request
from bpy.props import *
from bpy.app.handlers import persistent
from shapedo.shapedoSDK import ShapDoAPI

#constant
ADD_NEW_FILE = "<Add new File>"
ACCEPTED_FILETYPES = ["blend","stl"]


APT_TOKEN_PATH = os.path.join(bpy.utils.user_resource('SCRIPTS'), "presets",
"shapedo.txt")

BLEND_SAVE_PATH = os.path.join(bpy.utils.user_resource('SCRIPTS'), "presets",
"shapedo.blend")
print(APT_TOKEN_PATH)

settings = {
    "API" : "",
    "ProjectEnum" : [],
    "FilesEnum" : [],
    "CurrentProject" : "",
    "CurrentFile" : ""}

#Holds the lists for the Enums
projects = []
files = []

#Are we working on stl, or blend file?
working_on_stl = False


def save_settings():
    """ Save our settings in to an external file"""

    path = os.path.join(bpy.utils.user_resource('SCRIPTS'), "presets")
    if not os.path.exists(path):
        os.makedirs(path)

    file = open(APT_TOKEN_PATH, 'w+')
    file.write(json.dumps(settings))
    
    file.close()


@persistent
def load_settings():
    """ Load our settings in to an external file"""

    global settings
    try:
        file = open(APT_TOKEN_PATH, 'r')
    except:
        return
    try:
        settings = json.loads(file.readline())
    except:
        return
    file.close()
    print(settings)


def setWorkingProject(context):
    """Set the dropbox to the current project and file we are working on"""
    
    context.scene.ProjectEnum = settings["CurrentProject"]
    context.scene.FilesEnum = settings["CurrentFile"]


def projectUpdated(self, context):
    """ Runs when projects enum is update
    :param: self
    :param context: The context, holds the scene etc
    """
    setFiles(context)
    settings["ProjectEnum"] = str(context.scene.ProjectEnum)
    save_settings()


def filesUpdated(self, context):
    """ Runs when files enum is update
    :param: self
    :param context: The context, holds the scene etc
    """
    settings["FilesEnum"] = str(context.scene.FilesEnum)
    save_settings()


#enums for project and files path enum
bpy.types.Scene.ProjectEnum = EnumProperty(
    items=projects,
    name="Project",
    update=projectUpdated)

bpy.types.Scene.FilesEnum = EnumProperty(
    items=files,
    name="Files",
    update=filesUpdated)


def setProjects():
    """ Load a new set of Projects in to the enum, runs each time we need to update the list"""
    global projects
    projects2 = []
    a = ShapDoAPI(settings["API"])
    try:
        filesDict = a.getProjectsList()["projects"]
    except urllib.error.HTTPError:
        bpy.ops.error.message('INVOKE_DEFAULT', 
            MessageType="Error",
            message="Could not connect to server, check your API key")
        return []
    for project in filesDict:
        projects2.append((project["name"], project["title"], project["url"]))
    
    projects = filesDict.keys()
    
    bpy.types.Scene.ProjectEnum = EnumProperty(
        items=projects2,
        name="Project",
        update=projectUpdated)


def setFiles(context):
    """ Load a new set of files paths from a project in to the enum, runs each time we need to update the list"""
    global files
    
    files2 = []
    files = []
    a = ShapDoAPI(settings["API"])
    print("project:")
    print(str(context.scene.ProjectEnum))
    try:
        filesDict = a.getProjectInfo(str(context.scene.ProjectEnum))["files"]
    except:
        return
    for key in filesDict:
        if key.split(".")[-1] in ACCEPTED_FILETYPES:
            files2.append((key, key, filesDict[key]))
    
    #Append 'add new file' option
    files2.append((ADD_NEW_FILE, ADD_NEW_FILE, ADD_NEW_FILE))
    
    files = filesDict.keys()
    
    bpy.types.Scene.FilesEnum = EnumProperty(
        items = files2,
        name = "Files",
        update=filesUpdated)
    
    #Set to first option
    context.scene.FilesEnum = files2[0][1]


class ToolPropsPanel(bpy.types.Panel):
    """ The main toolset of the plugin"""
    bl_label = "ShapeDo sync"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOL_PROPS"
    
    bpy.types.Scene.urlPath = StringProperty(name="urlPath")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        global itemsPath
        self.layout.prop(context.scene, 'ProjectEnum')
        self.layout.prop(context.scene, 'FilesEnum')
        self.layout.operator("shapedo.download", text="Download")
        self.layout.operator("shapedo.upload", text="Upload")
        self.layout.operator("settings.dialog", text="Settings")
       
 
class OBJECT_OT_SettingsButton(bpy.types.Operator):
    """ Open the settings dialog"""
    bl_idname = "settings.dialog"
    bl_label = "Settings Dialog"
    
    def execute(self, context):
        # Invoke the dialog
        bpy.ops.object.settings_dialog_operator('INVOKE_DEFAULT')
        return {'FINISHED'}    
    

class OBJECT_OT_PullButton(bpy.types.Operator):
    bl_idname = "shapedo.download"
    bl_label = "Say Hello"
 
    def execute(self, context):
        global working_on_stl
        self.report({'INFO'}, "Downloading from ShapeDo")

        settings["CurrentProject"] = context.scene.ProjectEnum
        settings["CurrentFile"] = context.scene.FilesEnum
        save_settings()
        
        a = ShapDoAPI(settings["API"])
        a.downloadProject(settings["CurrentProject"], settings["CurrentFile"], BLEND_SAVE_PATH)
        
        try:
            bpy.ops.wm.open_mainfile(filepath=BLEND_SAVE_PATH)
            working_on_stl = False
        except RuntimeError:
            
            bpy.ops.wm.read_homefile()
            bpy.ops.object.delete()
            
            for item in bpy.data.objects:
                try:
                    bpy.context.scene.objects.unlink(item)
                    bpy.data.objects.remove(item)
                except:
                    pass
                
            bpy.ops.import_mesh.stl(filepath=BLEND_SAVE_PATH)
            working_on_stl = True
        
        setWorkingProject(context)
        return{'FINISHED'}    


class OBJECT_OT_PushButton(bpy.types.Operator):
    bl_idname = "shapedo.upload"
    bl_label = "Push to Shapedo"
 
    def execute(self, context):
        bpy.ops.object.push_dialog_operator('INVOKE_DEFAULT')
        return {'FINISHED'}


class PushDialogOperator(bpy.types.Operator):
    """ Push dialog"""
    bl_idname = "object.push_dialog_operator"
    bl_label = "Push file to ShapeDo"
    commit_message = StringProperty(name="Change description")
    new_file_path = StringProperty(name="New file name")

    def draw(self, context):
        layout = self.layout
        layout.alignment = 'EXPAND'
        layout.prop(self , "commit_message")
        
        row = layout.row()
        row.alignment = 'EXPAND'
        split = row.split(percentage=0.85)
        
        if context.scene.FilesEnum == ADD_NEW_FILE:
            split.prop(self , "new_file_path")
            split.label(".blend")
            
    def execute(self, context):
        
        def uploadBlend():
            a.uploadFile(context.scene.ProjectEnum, context.scene.FilesEnum, self.commit_message, BLEND_SAVE_PATH)
        
        self.report({'INFO'}, self.commit_message)
        
        a = ShapDoAPI(settings["API"])
        
        print(context.scene.FilesEnum == ADD_NEW_FILE)
        if context.scene.FilesEnum == ADD_NEW_FILE:
            newFileName = self.new_file_path + ".blend"
            
            if newFileName not in files:
                #uploading new file
                bpy.ops.wm.save_mainfile(filepath=BLEND_SAVE_PATH)
                a.uploadFile(context.scene.ProjectEnum, newFileName, self.commit_message, BLEND_SAVE_PATH)
                
                setFiles(context)
                context.scene.FilesEnum = newFileName
                uploadBlend()
            else:
                #Error file already exists
                bpy.ops.error.message('INVOKE_DEFAULT', MessageType="Error", 
                                      message="File already exists in project, please provide another.")
            
        else:
            if not working_on_stl:
                bpy.ops.wm.save_mainfile(filepath=BLEND_SAVE_PATH)
            else:
                bpy.ops.export_mesh.stl(filepath=BLEND_SAVE_PATH)
            print(self.commit_message)
            
            uploadBlend()
        return {'FINISHED'}
 
    def invoke(self, context, event):
        self.my_string = settings["API"]
        return context.window_manager.invoke_props_dialog(self, width=450, height=300)
 
 
class SettingsDialogOperator(bpy.types.Operator):
    """Settings dialog"""
    bl_idname = "object.settings_dialog_operator"
    bl_label = "ShapeDo connection settings"
 
    my_string = StringProperty(name="API Key")
 
    def execute(self, context):
        global settings
        
        self.report({'INFO'}, str(settings))
        
        settings["API"] = "%s" % (self.my_string.strip())
        
        save_settings()
        setProjects()
        setFiles(context)
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        obj = context.object
 
        row = layout.row()
        row.alignment = 'EXPAND'
        
        split = row.split(percentage=0.75)
        col = split.column() 
        col.prop(self , "my_string")
        col = split.column()

        props = col.operator("wm.url_open", text="Get API key", icon='WORLD_DATA')
        props.url = "http://shapedo.com/user"
    
    def invoke(self, context, event):
        self.my_string = settings["API"]
        return context.window_manager.invoke_props_dialog(self, width=450, height=300)


class MessageOperator(bpy.types.Operator):
    """
    The error message operator. When invoked, pops up a dialog 
    window with the given message.
    """
    bl_idname = "error.message"
    bl_label = "Message"
    MessageType = StringProperty()
    message = StringProperty()
 
    def execute(self, context):
        self.report({'INFO'}, self.message)
        print(self.message)
        return {'FINISHED'}
 
    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=600, height=200)
 
    def draw(self, context):
        self.layout.label(self.MessageType)
        row = self.layout.row()
        row.alignment = 'EXPAND'
        row.prop(self, "message")


def register():
    """Plugin registration, they all have to do that"""
    print("Loading ShapeDo addon")
    bpy.utils.register_module(__name__)
    load_settings()
    try:
        setProjects()
        ##TODO:  make this actually load the most recent file on startup
        setWorkingProject(bpy.context)
        setFiles(bpy.context)   
    except:
        pass
    
def unregister():
    print("Unloading ShapeDo addon")
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
    
