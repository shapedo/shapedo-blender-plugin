#!/usr/bin/python3
import json
import urllib.request
import urllib.parse
import shutil
import base64


class ShapDoAPI():
    """ShapeDo API handler class"""
    
    def __init__(self, token = "", host="https://shapedo.com/api/v1/"):
        """
        Constructor
        
        :param token: The API token from shapedo.com
        :param host: Url to shapedo
        """
        self.token = token
        self.host = host

    def _post(self, url, paramDict={}, token = False):
        """
        Internal funciton to send the post requests
        
        :param url: the url to access
        :param paramDict: A dict of the parameters to pass
        """
        if not token:
            extraItems = {"token": self.token}
        else:
            extraItems = {}
            
        params = urllib.parse.urlencode(dict(paramDict.items() | extraItems.items())).encode('UTF-8')
        f = urllib.request.urlopen(self.host + url, params)
        
        data = str(f.read().decode('latin-1'))
        reply = json.loads(data)
        if reply["success"] and not token:
            return reply["result"]
        else:
            return reply
    
    def getProjectInfo(self, projectName):
        """
        Get project info
        
        :param projectName: The name of the project owned by the user
        """
        return self._post("info", {"name": projectName})
    
    def getProjectsList(self):
        """
        List the projects owned by the user
        
        :return: a dict with the project information
        """
        return self._post("list")
    
    def uploadFile(self, projectName, filename, message, fileData):
        """
        Upload a file to a project in ShapeDo
        
        :param projectName: The name of the project
        :param filename: File path within the project tree
        :param message: Message describing what was changed
        :param fileData: Path to the file to upload
        """
        return self._post("upload", {
            "name": projectName,
            "file": base64.encodestring(open(fileData, 'rb').read()).decode(),
            "filename": filename,
            "message": message
            }
        )
    
    def createNewProject(self, projectTitle, localPath, remotePath, projectDescription = "", projectInstructions = "", projectCategory = "", projectLicense = "cc-sa", 
                         projectTags = "", private = False):
        """
        Create a new project
        
        :param localPath: the path to the file we are going to upload
        :param remotePath: The path of the file on shapedo
        :param projectDescription: description of the project
        :param projectCategory: Category as listed on ShapeDo API
        :param projectLicense: Licnese from the ones listed on ShapeDo
        :param projectTitle: the project title
        """
        
        return self._post("create", {
            "title" : projectTitle,
            "file": base64.encodestring(open(localPath, 'rb').read()).decode(),
            "filename": remotePath,
            "description": projectDescription,
            "instructions" : projectInstructions,
            "category" : projectCategory,
            "license" : projectLicense,
            "tags" : projectTags,
            "private" : private
            }
        )
    
    def downloadProject(self, projectName, filePath, savePath):
        """
        Download a file from a project
        
        :param projectName: The name of the project
        :param filePath: File path within the project tree
        :param savePath: The path where to save the file
        """
        response = self.getProjectInfo(projectName)
        downloadPath = response['files'][filePath]
        with urllib.request.urlopen(urllib.parse.quote(downloadPath, safe='/:?=')) as response, open(savePath, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        return
    
    def getToken(self, username, password):
        """
        Get API token
        
        :param username: The username
        :param passwordL The password
        :return: The API token response, token should be in "apiKey" key
        """
        return self._post("api-key", {
            "username": username,
            "password": password
            }, True)