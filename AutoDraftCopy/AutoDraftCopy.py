from __future__ import absolute_import
from Deadline.Events import DeadlineEventListener
from Deadline.Scripting import ClientUtils
import os
import sys
import shutil
from datetime import datetime
import traceback

def GetDeadlineEventListener():
    # type: () -> AutoDraftCopyListener
    return AutoDraftCopyListener()

def CleanupDeadlineEventListener(eventListener):
    # type: (AutoDraftCopyListener) -> None
    eventListener.Cleanup()

class AutoDraftCopyListener(DeadlineEventListener):
    def __init__(self):
        if sys.version_info.major == 3:
            super().__init__()
        # type: () -> None
        self.OnJobFinishedCallback += self.OnJobFinished

    def Cleanup(self):
        # type: () -> None
        del self.OnJobFinishedCallback

    def OnJobFinished(self, job):
        # type: (Job) -> None
        try:
            # Check if the job was created by AutoDraft
            if "Job Created by AutoDraft" in job.Comment:
                self.CopyDraftOutput(job)
            else:
                return
        except:
            ClientUtils.LogText(traceback.format_exc())

    def CopyDraftOutput(self, job):
        outputDirectories = job.JobOutputDirectories
        outputFilenames = job.JobOutputFileNames
        username = job.UserName 

        if not outputDirectories or not outputFilenames:
            ClientUtils.LogText("No output directories or filenames found.")
            return

        for i in range(len(outputDirectories)):
            draftOutputDir = outputDirectories[i]
            draftOutputFile = outputFilenames[i]
            draftOutputPath = os.path.join(draftOutputDir, draftOutputFile)

            if not os.path.exists(draftOutputPath):
                ClientUtils.LogText(f"Draft output file does not exist: {draftOutputPath}")
                continue

            projects_dir = self.GetConfigEntry("ProjectsDir")

            if not projects_dir:
                ClientUtils.LogText("ProjectsDir is not set in the configuration.")
                return

            project_folder = os.path.join(projects_dir, draftOutputPath.split(projects_dir)[1].split("\\")[0])
            current_date = datetime.now().strftime('%Y_%m_%d')
            dailies_folder = self.GetConfigEntry("Dailies")
            if not dailies_folder:
                ClientUtils.LogText("Dailies folder is not set in the configuration.")
                return

            # Ensure dailies_folder does not start with a backslash
            if dailies_folder.startswith("\\") or dailies_folder.startswith("/"):
                dailies_folder = dailies_folder[1:]

            base_target_dir1 = os.path.join(project_folder, dailies_folder)
            copy_dailies = self.GetBooleanConfigEntryWithDefault("CopyToDailies", True)
            copy_user = self.GetBooleanConfigEntryWithDefault("CopyToUserDir", False)

            # Check existence of base directories and create current date folder if needed
            if os.path.exists(base_target_dir1):
                if copy_dailies:
                    target_dir = os.path.join(base_target_dir1, current_date)
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    target_file = os.path.join(target_dir, os.path.basename(draftOutputPath))
                    self.CopyFile(draftOutputPath, target_file)
                if copy_user:
                    target_user_dir = os.path.join(base_target_dir1, current_date, username)
                    if not os.path.exists(target_user_dir):
                        os.makedirs(target_user_dir)
                    target_file = os.path.join(target_user_dir, os.path.basename(draftOutputPath))
                    self.CopyFile(draftOutputPath, target_file)
            else:
                ClientUtils.LogText(f"Base target directory does not exist. Checked: {base_target_dir1}")

    def CopyFile(self, src, dst):
        # type: (str, str) -> None
        shutil.copy2(src, dst)
        ClientUtils.LogText(f"Copied {src} to {dst}")

