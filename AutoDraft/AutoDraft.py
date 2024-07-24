
###############################################################
## Imports
###############################################################
from __future__ import absolute_import
from System.Diagnostics import *
from System.IO import File, Path
from System import TimeSpan

from Deadline.Events import DeadlineEventListener
from Deadline.Jobs import Job
from Deadline.Scripting import ClientUtils, FrameUtils, PathUtils, RepositoryUtils, StringUtils

import re
import sys
import os
import subprocess
import tempfile
import traceback


from six.moves import range

from typing import Any, Dict, List, Optional

##############################################################################################
## This is the function called by Deadline to get an instance of the Draft event listener.
##############################################################################################
def GetDeadlineEventListener():
    # type: () -> DraftEventListener
    return DraftEventListener()

def CleanupDeadlineEventListener(eventListener):
    # type: (DraftEventListener) -> None
    eventListener.Cleanup()

###############################################################
## The Draft event listener class.
###############################################################
class DraftEventListener (DeadlineEventListener):
    def __init__(self):
        # type: () -> None
        if sys.version_info.major == 3:
            super().__init__()
        self.OnJobFinishedCallback += self.OnJobFinished
        
        #member variables
        self.OutputPathCollection = {} # type: Dict[str, int]
        self.DraftSuffixDict = {} # type: Dict[str, int]
    
    def Cleanup(self):
        # type: () -> None
        del self.OnJobFinishedCallback

    # Utility function that creates a Deadline Job based on given parameters
    def CreateDraftJob(
            self,
            draftScript, # type: str
            job, # type: Job
            jobTag, # type: str
            outputIndex=0, # type: int
            outFileNameOverride=None, # type: Optional[str]
            draftArgs=None, # type: Optional[List[str]]
            mode=None, # type: Optional[str]
            quickDraftFormat=None, # type: Optional[Dict[str, Any]]
            dependencies=None # type: Optional[str]
        ):
        # type: (...) -> str
        
        if draftArgs is None:
            draftArgs = []
        
        # Grab the draf-related job settings
        outputFilenames = job.JobOutputFileNames

        if len(outputFilenames) == 0:
            raise Exception("ERROR: Could not find a full output path in Job properties; No Draft job will be created.")
        elif len(outputFilenames) <= outputIndex:
            raise Exception("ERROR: Output Index out of range for given Job; No Draft job will be created.")

        outputDirectories = job.JobOutputDirectories

        jobOutputFile = outputFilenames[outputIndex]
        jobOutputDir = outputDirectories[outputIndex]

        inputFrameList = ""
        frames = []
        frameRangeOverride = job.GetJobExtraInfoKeyValue("FrameRangeOverride")
        if not frameRangeOverride == "":
            inputFrameList = frameRangeOverride
            frames = FrameUtils.Parse(inputFrameList)
        else:
            # Grab the Frame Offset (if applicable)
            frameOffset = 0
            strFrameOffset = job.GetJobExtraInfoKeyValue("OutputFrameOffset{0}".format(outputIndex))
            if strFrameOffset:
                try:
                    frameOffset = int(strFrameOffset)
                except:
                    pass

            # calculate our frame list
            if frameOffset != 0:
                ClientUtils.LogText("Applying Frame Offset of %s to Frame List..." % frameOffset)

            for frame in job.Frames:
                frames.append(frame + frameOffset)

            inputFrameList = FrameUtils.ToFrameString(frames)

        # Grab the submission-related plugin settings
        relativeFolder = self.GetConfigEntryWithDefault("OutputFolder", "Draft")
        draftGroup = self.GetConfigEntryWithDefault("DraftGroup", "").strip()
        draftPool = self.GetConfigEntryWithDefault("DraftPool", "").strip()
        draftLimit = self.GetConfigEntryWithDefault("DraftLimit", "").strip()
        draftPriorityOffset = self.GetIntegerConfigEntryWithDefault("PriorityOffset", 0)

        if not draftGroup:
            draftGroup = job.Group

        if not draftPool:
            draftPool = job.Pool

        # TODO: Handle custom max priority?
        draftPriority = self.GetConfigEntryWithDefault('Priority', '50') #max(0, min(100, job.Priority + draftPriorityOffset))

        
        draftOutputFolder = Path.GetDirectoryName(jobOutputDir)
        draftOutputFolder = Path.Combine(draftOutputFolder, relativeFolder)
        draftOutputFolder = RepositoryUtils.CheckPathMapping(draftOutputFolder, True)
        draftOutputFolder = PathUtils.ToPlatformIndependentPath(draftOutputFolder)
        
        # Check if we have a name override or a Quick Draft job, else pull from Job
        if outFileNameOverride:
            draftOutputFile = outFileNameOverride
        elif quickDraftFormat:
            jobOutputFile = re.sub(r"\?", "#", Path.GetFileName(jobOutputFile))
            draftOutputFile = Path.GetFileNameWithoutExtension(jobOutputFile)
            if(quickDraftFormat["isMovie"]):
                draftOutputFile = draftOutputFile.replace("#", "").rstrip("_-. ")
            draftOutputFile += "." + quickDraftFormat["extension"]
        else:
            jobOutputFile = re.sub(r"\?", "#", Path.GetFileName(jobOutputFile))
            draftOutputFile = Path.GetFileNameWithoutExtension(jobOutputFile).replace("#", "").rstrip("_-. ")
            draftOutputFile += ".mov"
        
        
        draftOutput = Path.Combine(draftOutputFolder, draftOutputFile)

        deadlineTemp = ClientUtils.GetDeadlineTempPath()
        
        jobInfoFile = ""
        pluginInfoFile = ""
        with tempfile.NamedTemporaryFile(mode="w", dir=deadlineTemp, delete=False) as fileHandle:
            jobInfoFile = fileHandle.name 
            fileHandle.write("Plugin=DraftPlugin\n")
            fileHandle.write("Name={0} [{1}]\n".format(job.Name, jobTag))
            fileHandle.write("BatchName={0}\n".format(job.BatchName))
            fileHandle.write("Comment=Job Created by AutoDraft\n")
            fileHandle.write("Department={0}\n".format(job.Department))
            fileHandle.write("UserName={0}\n".format(job.UserName))
            fileHandle.write("Pool={0}\n".format(draftPool))
            fileHandle.write("Group={0}\n".format(draftGroup))
            fileHandle.write("Priority={0}\n".format(draftPriority))
            fileHandle.write("OnJobComplete=%s\n" % job.JobOnJobComplete) #"delete"
            fileHandle.write("ChunkSize=1000000\n")

            if draftLimit:
                fileHandle.write("LimitGroups={0}\n".format(draftLimit))

            fileHandle.write("OutputFilename0={0}\n".format(draftOutput))

            fileHandle.write("Frames={0}\n".format(inputFrameList))
            
            if dependencies:
                fileHandle.write("JobDependencies=%s\n" % dependencies)
            
            if mode:
                self.LogInfo("MODE: " + mode)
                
                modeParts = mode.split('|')
                if len(modeParts) == 2:
                    modeType = modeParts[0]
                    
                    if modeType == "Shotgun":
                        shotgunMode = modeParts[1]
                    
                        #Get the shotgun ID from the job
                        shotgunID = job.GetJobExtraInfoKeyValue("VersionId")
                        if (shotgunID == ""):
                            ClientUtils.LogText("WARNING: Could not find an associated Shotgun Version ID.  The Draft output will not be uploaded to Shotgun.")
                        else:
                            #Pull any SG info from the other job
                            fileHandle.write("ExtraInfo0={0}\n".format(job.ExtraInfo0))
                            fileHandle.write("ExtraInfo1={0}\n".format(job.ExtraInfo1))
                            fileHandle.write("ExtraInfo2={0}\n".format(job.ExtraInfo2))
                            fileHandle.write("ExtraInfo3={0}\n".format(job.ExtraInfo3))
                            fileHandle.write("ExtraInfo4={0}\n".format(job.ExtraInfo4))
                            fileHandle.write("ExtraInfo5={0}\n".format(job.ExtraInfo5))

                            #Only bother with the necessary KVPs
                            fileHandle.write("ExtraInfoKeyValue0=VersionId={0}\n".format(shotgunID))
                            fileHandle.write("ExtraInfoKeyValue1=TaskId={0}\n".format(job.GetJobExtraInfoKeyValue('TaskId')))
                            fileHandle.write("ExtraInfoKeyValue2=Mode={0}\n".format(shotgunMode))


        # Build the Draft plugin info file
        with tempfile.NamedTemporaryFile(mode="w", dir=deadlineTemp, delete=False) as fileHandle:
            pluginInfoFile = fileHandle.name 
            # build up the script arguments
            scriptArgs = draftArgs

            scriptArgs.append('frameList=%s ' % inputFrameList)
            scriptArgs.append('startFrame=%s ' % frames[0])
            scriptArgs.append('endFrame=%s ' % frames[-1])
            
            scriptArgs.append('inFile="%s" ' % Path.Combine(jobOutputDir, jobOutputFile ))
            scriptArgs.append('outFile="%s" ' % draftOutput)
            scriptArgs.append('outFolder="%s" ' % Path.GetDirectoryName(draftOutput))

            scriptArgs.append('deadlineJobID=%s ' % job.JobId)

            
            for i, scriptArg in enumerate(scriptArgs):
                fileHandle.write("ScriptArg%d=%s\n" % (i, scriptArg))

        ClientUtils.LogText("Submitting {0} Job to Deadline...".format(jobTag))
        output = self.CallDeadlineCommand([jobInfoFile, pluginInfoFile, draftScript])
        ClientUtils.LogText(output)

        jobId = ""
        resultArray = output.split()
        for line in resultArray:
            if line.startswith("JobID="):
                jobId = line.replace("JobID=","")
                break
        return jobId
     
    ## This is called when the job finishes rendering.
    def OnJobFinished(self, job):
        # type: (Job) -> None
        # Reset those in case the script was not reloaded
        groupFilter = self.GetConfigEntryWithDefault('GroupFilter', '.+')
        if not re.match(groupFilter, job.Group):
            return

        jobNameFilter = self.GetConfigEntryWithDefault('JobNameFilter', '.+')
        if re.match(r'^(hudy_redshift)$', job.Group) and not re.match(jobNameFilter, job.JobName):
            return

        pluginNameFilter = self.GetConfigEntryWithDefault('PluginNameFilter', '')
        if not re.match(pluginNameFilter, job.JobPlugin):
            return

        self.OutputPathCollection = {}
        self.DraftSuffixDict = {}
        
        draftQuickScript = RepositoryUtils.GetRepositoryFilePath("custom/events/AutoDraft/DraftQuickSubmission/QuickDraft.py", True)

        comment = job.Comment
        # Define the regular expression pattern to match any number before "fps". If a match is found, extract the frame rate
        pattern = r'(\d+)\s*fps'
        match = re.search(pattern, comment)
        if match:
            frameRate = match.group(1)
        else:
            frameRate =  self.GetConfigEntryWithDefault('Quality', '35')

        # Get all the other Quick Draft-related KVPs from the Job
        resolution = "1"
        quality = self.GetConfigEntryWithDefault('Quality', '75')
        ocio_config_file = self.GetConfigEntryWithDefault("OCIOConfigFile", r"C:\ACES\aces_1.2\config.ocio")
        colorSpaceIn = f"OCIOConfigFile {ocio_config_file} {self.GetConfigEntryWithDefault('DraftColorSpaceIn', 'ACES-ACEScg')}"
        colorSpaceOut = f"OCIOConfigFile {ocio_config_file} {self.GetConfigEntryWithDefault('DraftColorSpaceOut', 'Output-sRGB')}"
        annotationsString = job.GetJobExtraInfoKeyValueWithDefault("DraftAnnotationsString", "None")
        annotationsFramePaddingSize = job.GetJobExtraInfoKeyValueWithDefault("DraftAnnotationsFramePaddingSize", "None")

        if len(job.Frames) > 1:
            extension = "mov"
            isMovie = True
            codec = "h264"
        else:
            extension = "png"
            isMovie = False
            codec = "zip"
        format = {'extension' : extension, 'isMovie' : isMovie}
        
        outputCount = len(job.JobOutputFileNames)
        for i in range(0, outputCount):
            scriptArgs = []
            scriptArgs.append('resolution="%s" ' % resolution)
            scriptArgs.append('codec="%s" ' % codec)
            scriptArgs.append('quality="%s" ' % quality)
            scriptArgs.append('colorSpaceIn="%s" ' % colorSpaceIn)
            scriptArgs.append('colorSpaceOut="%s" ' % colorSpaceOut)
            scriptArgs.append('annotationsString="%s" ' % annotationsString)
            scriptArgs.append('annotationsFramePaddingSize="%s" ' % annotationsFramePaddingSize)
            scriptArgs.append('isDistributed="%s" ' % False)

            if isMovie:
                scriptArgs.append('frameRate="%s" ' % frameRate)
                scriptArgs.append('quickType="createMovie" ')
            else:
                scriptArgs.append('quickType="createImages" ')

            mode = None

            ClientUtils.LogText("====Submitting Job for Output {0} of {1}====".format(i + 1, outputCount))
            
            self.CreateDraftJob(draftQuickScript, job, "Quick Draft", outputIndex=i, draftArgs=scriptArgs, mode=mode, quickDraftFormat=format)


    def CallDeadlineCommand(self, arguments):
        deadlineBin = ClientUtils.GetBinDirectory()
        
        deadlineCommand = ""
        if os.name == 'nt':
            deadlineCommand = Path.Combine(deadlineBin, "deadlinecommandbg.exe")
        else:
            deadlineCommand = Path.Combine(deadlineBin, "deadlinecommandbg")
        
        arguments.insert(0, deadlineCommand)
        proc = subprocess.Popen(arguments, cwd=deadlineBin)
        proc.wait()
        
        outputPath = Path.Combine(ClientUtils.GetDeadlineTempPath(), "dsubmitoutput.txt")
        output = File.ReadAllText(outputPath)
        
        return output