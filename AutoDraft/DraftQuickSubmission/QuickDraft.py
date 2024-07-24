# pylint: disable=invalid-name
# Otherwise it will complain about non-conforming module name.
"""QuickDraft Plugin."""
from __future__ import absolute_import, print_function
from distutils.spawn import find_executable
import os
import sys
import subprocess

if sys.version_info[0] < 3:
    raise RuntimeError("This plugin does not support python 2. Instructions how to run as Python 3 you can find in this guide https://docs.thinkboxsoftware.com/products/deadline/10.1/1_User%20Manual/manual/python-upgrade.html")

from DraftParamParser import ParseCommandLine_TypeAgnostic # pylint: disable=import-error,wildcard-import
from DraftParamParser import * # pylint: disable=import-error,wildcard-import

# Best-effort import for type annotations
try:
    from typing import Dict, List, Optional, Text
except ImportError:
    pass


def GetDeadlineCommand():
    # type: () -> str
    """
    Finds the Deadline Command executable as it is installed on your machine by searching in the following order:
    * The DEADLINE_PATH environment variable
    * The PATH environment variable
    * The file /Users/Shared/Thinkbox/DEADLINE_PATH
    """

    for env in ("DEADLINE_PATH", "PATH"):
        try:
            env_value = os.environ[env] # type: str
        except KeyError:
            # if the error is a key error it means that DEADLINE_PATH is not set.
            # however Deadline command may be in the PATH or on OSX it could be in the file /Users/Shared/Thinkbox/DEADLINE_PATH
            continue

        exe = find_executable("deadlinecommand", env_value) # type: Optional[str]
        if exe:
            return exe

    # On OSX, we look for the DEADLINE_PATH file if the environment variable does not exist.
    if os.path.exists("/Users/Shared/Thinkbox/DEADLINE_PATH"):
        with open("/Users/Shared/Thinkbox/DEADLINE_PATH") as dl_file:
            deadline_bin = dl_file.read().strip()
        exe = find_executable("deadlinecommand", deadline_bin)
        if exe:
            return exe

    raise Exception("Deadline could not be found.  Please ensure that Deadline is installed.")


def GetRepositoryPath(subdir=None):  # pylint: disable=missing-docstring,invalid-name,line-too-long
    # type: (Optional[str]) -> Text
    startupinfo = None

    cmd = [GetDeadlineCommand(), "-GetRepositoryPath "] # type: List[str]
    if subdir is not None and subdir:  # pylint: disable=consider-using-in
        cmd.append(subdir)

    # Specifying PIPE for all handles to workaround a Python bug on Windows.
    # The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            startupinfo=startupinfo)

    proc.stdin.close() # type: ignore # stdin is set above, but mypy doesn't think so
    proc.stderr.close() # type: ignore # stderr is set above, but mypy doesn't think so
    output = proc.stdout.read() # type: ignore # stdout is set above, but mypy doesn't think so

    path = output.decode("utf_8") # type: Text # pylint: disable=redefined-outer-name
    path = path.replace("\r", "").replace("\n", "").replace("\\", "/")

    return path


path = GetRepositoryPath("events/AutoDraft/DraftQuickSubmission")

if path != "":
    # Add the path to the system path
    if path not in sys.path:
        msg = "Appending \"%s\" to system path to import Quick Draft scripts"
        print(msg % path)
        sys.path.append(path) # type: ignore # doesn't like that it's unicode in py2, but that's how we wrote it
    else:
        print("\"%s\" is already in the system path" % path)

    # NOTE: callable below most likely comes from DraftParamParser, but
    # it is hard to tell without knowing. That is one of the reasons to avoid
    # wildcard imports. Leaving it as is for now till more serious refactoring.
    params = ParseCommandLine_TypeAgnostic(sys.argv) # type: Dict # pylint: disable=undefined-variable,line-too-long

    try:
        quickType = params['quickType'] # type: str
    except:
        raise Exception("Error: No Quick Draft type was specified.")

    if quickType == "createImages":
        from DraftCreateImages import CreateImages
        CreateImages(params)
    elif quickType == "createMovie":
        from DraftCreateMovie import CreateMovie
        CreateMovie(params)
    elif quickType == "concatenateMovies":
        from DraftConcatenateMovies import ConcatenateMovies
        ConcatenateMovies(params)
    else:
        msg = "Error: Unrecognised Quick Draft type: " + quickType + "."
        raise Exception(msg)

else:
    msg = ("The Quick Draft scripts could not be found in the Deadline "
           "Repository. Please make sure that the Deadline Client has been "
           "installed on this machine, that the Deadline Client bin folder is "
           "set in the DEADLINE_PATH environment variable, and that the "
           "Deadline Client has been configured to point to a valid "
           "Repository."
           )
    print(msg)
