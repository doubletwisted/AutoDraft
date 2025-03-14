# AutoDraft
AutoDraft is a Deadline Event Plugin for simple creation of previews from rendered jobs. 

## Overview
AutoDraft is a Deadline Event Plugin based on the original DraftEventPlugin designed to simplify using Draft in Deadline with easy-to-do configuration. It triggers the creation of a draft job upon job completion, which processes the rendered sequence. After Draft job is completed it will be deleted. 
AutoDraftCopy copies AutoDraft output to selected directories for example for dailies. 

## Installation

1. Download this git and move the contents to your Deadline Repository under "repository/custom/events/".
2. In Deadline Monitor go to Tools > Power User Mode.
3. In Deadline Monitor go to Tools > Synchronize Monitor Scripts and Plugins
4. In Deadline Monitor go to Tools > Configure Events... > AutoDraft > Global Enabled/Opt-In.


## Configuration File Details

- **State**
  - **Description:** Determines the plugin's operational mode. Options are Global Enabled, Opt-In, and Disabled.

- **JobNameFilter**
  - **Description:** A Python regular expression to filter jobs based on their names. Default is `.+`, which processes any job.

- **GroupFilter**
  - **Description:** A Python regular expression to filter jobs based on their group. Default is `.+`, which processes any group.

- **PluginNameFilter**
  - **Description:** A Python regular expression to filter jobs based on the plugin name. Default is `^(?!DraftPlugin$).+$`, which excludes jobs using the DraftPlugin.

- **DraftColorSpaceIn**
  - **Description:** Specifies the input color space for Draft. Default is `ACES-ACEScg`.

- **DraftColorSpaceOut**
  - **Description:** Specifies the output color space for Draft. Default is `Output-sRGB`.

- **OCIOConfigFile**
  - **Description:** Location of the OCIO configuration file. Default is `C:\ACES\aces_1.2\config.ocio`.

- **Priority**
  - **Description:** Sets the priority of the draft job. Default is `50`.

- **Quality**
  - **Description:** Sets the quality of the movie output, ranging from 0 to 100. Default is `75`.

- **FrameRate**
  - **Description:** Default frame rate for the movie. If the job comment includes "XXfps", it will use that frame rate. Default is `30`.


<meta name="google-site-verification" content="cZdJ0LEvBAC2lOvQOvaN-YL6bEHHTN5vQlyFFD8oePA" />
