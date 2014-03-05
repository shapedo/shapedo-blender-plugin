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
from shapedo.EnumData import CATEGORIES, LICENSES

#constant
CREATE_NEW_PROJECT = "<Add new project>"
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
    "CurrentFile" : "",
    "Username" : "" }

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
        settings.update(json.loads(file.readline()))
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
    if str(context.scene.ProjectEnum) == CREATE_NEW_PROJECT:
        setFiles(context,True)
    else:
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
    projects = []
    a = ShapDoAPI(settings["API"])
    try:
        projectsDict = a.getProjectsList()["projects"]
    except urllib.error.HTTPError:
        bpy.ops.error.message('INVOKE_DEFAULT', 
            MessageType="Error",
            message="Could not connect to server, check your API key")
        return []
    for project in projectsDict:
        projects2.append((project["name"], project["title"], project["url"]))
        projects.append(project["name"])
    
    #Append 'add new file' option
    projects2.append((CREATE_NEW_PROJECT, CREATE_NEW_PROJECT, CREATE_NEW_PROJECT))
    
    bpy.types.Scene.ProjectEnum = EnumProperty(
        items=projects2,
        name="Project",
        update=projectUpdated)


def setFiles(context,dummy=False):
    """ Load a new set of files paths from a project in to the enum, runs each time we need to update the list
    
    :param context: Scene context
    :param dummy: Used if we are loading a new project, dummy value will be generated
    """
    global files
    
    files2 = []
    files = []
    
    if dummy:
        files2.append((ADD_NEW_FILE, ADD_NEW_FILE, ADD_NEW_FILE))
        
    else:
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
        
        mainCol = self.layout.column()
        
        mainCol.prop(context.scene, 'ProjectEnum')
        mainCol.prop(context.scene, 'FilesEnum')
        mainCol.operator("shapedo.download", text="Download")
        mainCol.operator("shapedo.upload", text="Upload")
        props = mainCol.operator("wm.url_open", text="Open Project Page", icon='WORLD_DATA')
        props.url = "http://shapedo.com/" + settings["Username"] + "/" + settings["CurrentProject"]
        mainCol.operator("settings.refresh", text="Update project list")
        settingsCol = self.layout.column()
        settingsCol.operator("settings.dialog", text="Settings")
        
        #draw logic
        mainCol.enabled = "API" in settings and settings["API"] != ""
                
       
 
class OBJECT_OT_SettingsButton(bpy.types.Operator):
    """ Open the settings dialog"""
    bl_idname = "settings.dialog"
    bl_label = "Settings Dialog"
    
    def execute(self, context):
        # Invoke the dialog
        bpy.ops.object.settings_dialog_operator('INVOKE_DEFAULT')
        return {'FINISHED'}

class OBJECT_OT_SettingsButton(bpy.types.Operator):
    """ Open the settings dialog"""
    bl_idname = "settings.refresh"
    bl_label = "Refresh Project List"
    
    def execute(self, context):
        # Invoke the dialog
        setProjects()
        context.scene.ProjectEnum = settings["CurrentProject"]
        setFiles(context)
        context.scene.FilesEnum = settings["CurrentFile"]
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
    commit_message = StringProperty(name = "Change description")
    
    new_project_title = StringProperty(name = "Project title*")
    new_project_description = StringProperty(name = "Project description*")
    new_project_category = EnumProperty(items = CATEGORIES, name = "Category*")
    new_project_license = EnumProperty(items = LICENSES, name = "License*")
    new_project_private = BoolProperty(name = "", description = "True or False?")
    new_project_tags = StringProperty(name = "Tags (comma seprated):")
    
    new_file_path = StringProperty(name="New file name*")

    def draw(self, context):
        layout = self.layout
        layout.alignment = 'EXPAND'
        
        if context.scene.ProjectEnum != CREATE_NEW_PROJECT:
            layout.prop(self , "commit_message")
        
        row = layout.row()
        row.alignment = 'EXPAND'
        
        if context.scene.ProjectEnum == CREATE_NEW_PROJECT:
            row = layout.row()
            row.prop(self , "new_project_title")
            row = layout.row()
            row.prop(self , "new_project_description")
            row = layout.row()
            row.prop(self , "new_project_category")
            row = layout.row()
            row.prop(self , "new_project_license")
            row = layout.row()
            split = row.split(percentage=0.32)
            split.label("Private project?")
            split.prop(self , "new_project_private")
            row = layout.row()
            row.prop(self , "new_project_tags")
        
        if context.scene.FilesEnum == ADD_NEW_FILE:
            row = layout.row()
            row.alignment = 'EXPAND'
            split = row.split(percentage=0.85)
            split.prop(self , "new_file_path")
            split.label(".blend")
            
            
    def execute(self, context):
        
        bpy.ops.upload.shapedo('INVOKE_DEFAULT',
                                 commit_message = self.commit_message,
                                 new_project_title= self.new_project_title,
                                 new_project_description = self.new_project_description,
                                 new_project_category = self.new_project_category,
                                 new_project_license = self.new_project_license,
                                 new_project_private = self.new_project_private,
                                 new_project_tags = self.new_project_tags,
                                 new_file_path = self.new_file_path,
                                 )
        return {'FINISHED'}
 
    def invoke(self, context, event):
        self.settings_token = settings["API"]
        return context.window_manager.invoke_props_dialog(self, width=450, height=300)

 
class SettingsDialogOperator(bpy.types.Operator):
    """Settings dialog"""
    bl_idname = "object.settings_dialog_operator"
    bl_label = "ShapeDo connection settings"
 
    settings_username = StringProperty(name="Username")
    settings_password = StringProperty(name="Password", subtype="PASSWORD")
 
    def execute(self, context):
        global settings
        
        self.report({'INFO'}, str(settings))
        
        a = ShapDoAPI()
        
        self.settings_username = self.settings_username.strip()
        self.settings_password = self.settings_password.strip()
        
        if self.settings_username != "" and self.settings_password != 0:
            reply = a.getToken(self.settings_username, self.settings_password)
            print(reply)
            
            try:
                if not reply["success"]:
                    bpy.ops.error.message('INVOKE_DEFAULT', 
                    MessageType="Error",
                    message="Authentication failed, check your username and password")
                else:
                    settings["API"] = reply["apiKey"]
                    settings["Username"] = self.settings_username
                    save_settings()
                    setProjects()
                    setFiles(context)
                    
            except:
                bpy.ops.error.message('INVOKE_DEFAULT', 
                MessageType="Error",
                message="Could not connect to server, check your internet connection")
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        obj = context.object
 
        row = layout.row()
        row.alignment = 'EXPAND'
       
        
        row = layout.row()
        row.prop(self , "settings_username")
        row = layout.row()
        row.prop(self , "settings_password")
        row = layout.row()
        split = row.split(percentage=0.25)
        props = split.operator("wm.url_open", text="Sign Up", icon='WORLD_DATA')
        props.url = "http://shapedo.com/user/login"
        
        
        row = layout.row()
        row.alignment = 'CENTER'
        row.label("API: " + settings["API"])
    
    def invoke(self, context, event):
        self.settings_token = settings["API"]
        return context.window_manager.invoke_props_dialog(self, width=450, height=300)


class UploadShapeDo(bpy.types.Operator):
    """ Opreator to upload data from the upload dialog without getting it stuck """
    bl_idname = "upload.shapedo"
    bl_label = "Upload"
    
    commit_message = StringProperty(name = "Change description")
    
    new_project_title = StringProperty(name = "Project title*")
    new_project_description = StringProperty(name = "Project description*")
    new_project_category = EnumProperty(items = CATEGORIES, name = "Category*")
    new_project_license = EnumProperty(items = LICENSES, name = "License*")
    new_project_private = BoolProperty(name = "", description = "True or False?")
    new_project_tags = StringProperty(name = "Tags (comma seprated):")
    
    new_file_path = StringProperty(name="New file name*")
    
    _timer = None
    _thread = None
    
    def modal(self, context, event):
        
        a = ShapDoAPI(settings["API"])
        
        if context.scene.ProjectEnum == CREATE_NEW_PROJECT:
            
            self.report({'INFO'}, "Creating new project")
            bpy.ops.wm.save_mainfile(filepath=BLEND_SAVE_PATH)
            newFilePath = self.new_file_path.split(".blend")[0] + ".blend"
            result = a.createNewProject(self.new_project_title, BLEND_SAVE_PATH, newFilePath, self.new_project_description,
                              "", self.new_project_category, self.new_project_license, 
                               self.new_project_tags, self.new_project_private)
            
            
            #Make enums include new project, and set it to the current project
            newProjectName = result['url'].split("/")[-1]
            
            settings["CurrentProject"] = newProjectName
            settings["CurrentFile"] = newFilePath
            save_settings()
            
            setProjects()
            setFiles(context)
            
            context.scene.ProjectEnum = newProjectName
            context.scene.FilesEnum = newFilePath
        
        #uploading new file to existing project
        elif context.scene.FilesEnum == ADD_NEW_FILE:
            self.report({'INFO'}, self.commit_message)
                
            newFileName = self.new_file_path + ".blend"
            
            if newFileName not in files:
                #uploading new file
                bpy.ops.wm.save_mainfile(filepath=BLEND_SAVE_PATH)
                a.uploadFile(context.scene.ProjectEnum, newFileName, self.commit_message, BLEND_SAVE_PATH)
                
                setFiles(context)
                context.scene.FilesEnum = newFileName
            else:
                #Error file already exists
                bpy.ops.error.message('INVOKE_DEFAULT', MessageType="Error", 
                                    message="File already exists in project, please provide another.")
            
        #uploading to existing file    
        else:
            self.report({'INFO'}, self.commit_message)
            print("updating existing")
            
            if not working_on_stl:
                bpy.ops.wm.save_mainfile(filepath=BLEND_SAVE_PATH)
            else:
                # select all objects
                for object in bpy.data.objects:
                    object.select = True
                bpy.ops.export_mesh.stl(filepath=BLEND_SAVE_PATH)
            print(self.commit_message)
            
            print(a.uploadFile(context.scene.ProjectEnum, context.scene.FilesEnum, self.commit_message, BLEND_SAVE_PATH))         
            
        return {'FINISHED'}
    
    def execute(self, context):
        
        self._timer = context.window_manager.event_timer_add(0.5, context.window)
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

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
    
