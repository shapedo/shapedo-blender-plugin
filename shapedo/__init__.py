bl_info = {
    "name" : "ShapeDo",
    "author" : "Guy Sheffer",
    "version" : (0, 0, 2),
    "blender" : (2, 68, 0),
    "category" : "Tools",
    "location" : "3D View >> Tools",
    "wiki_url" : "https://github.com/shapedo/shapedo-blender-plugin",
    "tracker_url" : "https://github.com/shapedo/shapedo-blender-plugin/blob/master/shapedo/shapedo-blender-plugin/__ini__.py",
    "description" : "A blender addon to work on projects on ShapeDo from within blender"
}

import bpy
from bpy.props import *
import os.path
import json
from bpy.app.handlers import persistent
import urllib.request
from shapedo.shapedoSDK import ShapDoAPI

APT_TOKEN_PATH = os.path.join(bpy.utils.user_resource('SCRIPTS'), "presets",
"shhapedo.txt")

BLEND_SAVE_PATH = os.path.join(bpy.utils.user_resource('SCRIPTS'), "presets",
"shapedo.blend")
print(APT_TOKEN_PATH)
settings = {"API" : "",
	    "ProjectEnum" : 1,
	    "FilesEnum" : 1}

#Holds the lists for the Enums
projects = []
files = []

#Are we working on stl, or blend file?
working_on_stl = False

def save_settings():
    """ Save our settings in to an external file
    """
    path = os.path.join(bpy.utils.user_resource('SCRIPTS'), "presets")
    if not os.path.exists(path):
        os.makedirs(path)
        
    file = open(APT_TOKEN_PATH, 'w+')
    file.write(json.dumps(settings))
    
    file.close()

@persistent
def load_settings():
    """ Load our settings in to an external file
    """
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

def projectUpdated(self, context):
    """ Runs when projects enum is update
    :param: self
    :param context: The context, holds the scene etc
    """
    setFiles(context)
    settings["ProjectEnum"] = str(context.scene.ProjectEnum)
    save_settings()
    return

def filesUpdated(self, context):
    """ Runs when files enum is update
    :param: self
    :param context: The context, holds the scene etc
    """
    settings["FilesEnum"] = str(context.scene.FilesEnum)
    save_settings()
    return

#enums for project and files path enum
bpy.types.Scene.ProjectEnum = EnumProperty(
    items = projects,
    name = "Project",update=projectUpdated)

bpy.types.Scene.FilesEnum = EnumProperty(
    items = files,
    name = "Files",
    update=filesUpdated)

def setProjects():
  """ Load a new set of Projects in to the enum, runs each time we need to update the list
  """
  projects2 = []
  a = ShapDoAPI(settings["API"])
  print(a.getProjectsList().keys())
  projects = a.getProjectsList()["projects"]
  for project in projects:
    projects2.append((project["name"], project["title"], project["url"]))
  bpy.types.Scene.ProjectEnum = EnumProperty(
        items = projects2,
        name = "Project",
        update=projectUpdated)
  return

def setFiles(context):
  """ Load a new set of files paths from a project in to the enum, runs each time we need to update the list
  """
  files2 = []
  a = ShapDoAPI(settings["API"])
  print("project:")
  print(str(context.scene.ProjectEnum))
  filesDict = a.getProjectInfo(str(context.scene.ProjectEnum))["files"]
  for key in filesDict:
    files2.append((key, key, filesDict[key]))
  bpy.types.Scene.FilesEnum = EnumProperty(
        items = files2,
        name = "Files",
        update=filesUpdated)
  return

class ToolPropsPanel(bpy.types.Panel):
    """ The main toolset of the plugin 
    """
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
        self.layout.operator("shapedo.download", text='Download')
        self.layout.operator("shapedo.upload", text='Upload')
        
        self.layout.operator("settings.dialog", text='Settings')
        return
       
 
class OBJECT_OT_SettingsButton(bpy.types.Operator):
    """ Open the settings dialog
    """
    bl_idname = "settings.dialog"
    bl_label = "Settings Dialog"
    
    def execute(self, context):
        # Invoke the dialog
        bpy.ops.object.settings_dialog_operator('INVOKE_DEFAULT')
        return{'FINISHED'}    
    

class OBJECT_OT_PullButton(bpy.types.Operator):
    bl_idname = "shapedo.download"
    bl_label = "Say Hello"
 
    def execute(self, context):
        global working_on_stl
        self.report({'INFO'}, "Downloading from ShapeDo")
        
        a = ShapDoAPI(settings["API"])
        a.downloadProject(context.scene.ProjectEnum, context.scene.FilesEnum,BLEND_SAVE_PATH)
        
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
            
        return{'FINISHED'}    

class OBJECT_OT_PushButton(bpy.types.Operator):
    bl_idname = "shapedo.upload"
    bl_label = "Push to Shapedo"
 
    def execute(self, context):
        bpy.ops.object.push_dialog_operator('INVOKE_DEFAULT')
        return{'FINISHED'}

class PushDialogOperator(bpy.types.Operator):
    """ Push dialog
    """
    bl_idname = "object.push_dialog_operator"
    bl_label = "Push file to ShapeDo"
    commit_message = StringProperty(name="Change description")
 
    def execute(self, context):
        
        self.report({'INFO'}, self.commit_message)
        
        if not working_on_stl:
            bpy.ops.wm.save_mainfile(filepath=BLEND_SAVE_PATH)
        else:
            bpy.ops.export_mesh.stl(filepath=BLEND_SAVE_PATH)
        print(self.commit_message)
        a = ShapDoAPI(settings["API"])
        a.uploadFile(context.scene.ProjectEnum, context.scene.FilesEnum, self.commit_message, BLEND_SAVE_PATH)

        return {'FINISHED'}
 
    def invoke(self, context, event):
        self.my_string = settings["API"]
        return context.window_manager.invoke_props_dialog(self)
 
class SettingsDialogOperator(bpy.types.Operator):
    """ Settings dialog
    """
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
 
    def invoke(self, context, event):
        self.my_string = settings["API"]
        return context.window_manager.invoke_props_dialog(self)

bpy.utils.register_module(__name__)

def register():
    """ Plugin regestration, they all have to do that """
    print("Loading ShapeDo addon")
    load_settings()
    try:
        setProjects()
        setFiles(bpy.context)
    except:
        pass
    
def unregister():
    print("Unloading ShapeDo addon")
