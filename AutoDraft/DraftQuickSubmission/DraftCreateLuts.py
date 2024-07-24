from __future__ import absolute_import, print_function

try:
    from typing import List, Optional
except:
    pass

import Draft
from DraftASCCDLReader import ReadASCCDL

def CreateLuts( colorSpaceIn, colorSpaceOut ):
    # type(str, str) -> Optional[Draft.LUT]
    luts = []
    
    colorInInfo = colorSpaceIn.split()
    colorOutInfo = colorSpaceOut.split()
    
    colorInType = colorInInfo[0]
    colorOutType = colorOutInfo[0]

    if( colorInType == "OCIOConfigFile" or colorOutType ==  "OCIOConfigFile" ):
        lut = CreateLutFromOCIOConfigfile( colorInInfo, colorOutInfo )
        if lut:
         luts.append( lut )
    else:
        lutIn = CreateLut( colorSpaceIn )
        if lutIn:
            try:
                lutInverse = lutIn.Inverse()
                luts.append( lutInverse )
            except Exception as e:
                print("Warning: Error while inverting the lut that defines color space in.", e, "Color space in will be ignored.")
            
        lutOut = CreateLut( colorSpaceOut )
        if lutOut:
            luts.append( lutOut )
    
    return luts

def CreateLutFromOCIOConfigfile( colorInInfo, colorOutInfo ):
    # type: (str, str) -> Optional[Draft.LUT]
    colorInConfigfile = colorInInfo[1]
    colorOutConfigfile = colorOutInfo[1]
    
    lut = None
    
    if colorInConfigfile == colorOutConfigfile:
        Draft.LUT.SetOCIOConfig( colorInConfigfile )
        try:
            #old
            #lut = Draft.LUT.CreateOCIOProcessor( colorInInfo[2], colorOutInfo[2] )
            #fix
            lut = Draft.LUT.CreateOCIOProcessor(colorInInfo[2].replace('-', ' - '), colorOutInfo[2].replace('-', ' - '))
        except Exception as e:
            print("Warning: Error while creating OCIO lut from configfile.", e, "No lut will be applied.")
        return lut
    else:
        print("Warning: Error while creating OCIO lut from configfile. The configfiles for color space in and color space out need to match. No lut will be applied.")
    return None
    
def CreateLut( colorSpace ):
    # type: (str) -> Optional[Draft.LUT]
    if colorSpace == "Identity":
        return None
    
    lutInfo = colorSpace.split()
    lutType = lutInfo[0]

    lut = None
    
    if lutType == "Draft":
        lut = CreateDraftLut( lutInfo )
        # new
        print('Create LUT succefully')
        print(lutInfo)
        #old
    elif lutType == "OCIOLutFile":
        #fix
    #elif lutType == "OCIOConfigFile":
        lut = CreateOCIOLutFromFile( lutInfo[1] )
        print('Create LUT succefully')
        print(lutInfo[1])
 
    return lut

def CreateDraftLut( lutInfo ):
    # type: (List[str]) -> Optional[Draft.LUT]
    name = lutInfo[1]
    if( name == "sRGB" ):
        return Draft.LUT.CreateSRGB()
    elif( name == "rec709" ):
        return Draft.LUT.CreateRec709()
    elif( name == "Cineon" ):
        return Draft.LUT.CreateCineon()
    elif( name == "Gamma" ):
        return Draft.LUT.CreateGamma( float( lutInfo[2] ) )
    elif( name == "AlexaV3LogC" ):
        return Draft.LUT.CreateAlexaV3LogC()
    elif( name == "ASCCDL" ):
        return ReadASCCDL( lutInfo[2] )
    else:
        return None

def CreateOCIOLutFromFile( lutFile ):
    # type: (str) -> Optional[Draft.LUT]
    lut = None
    try:
        lut = Draft.LUT.CreateOCIOProcessorFromFile( lutFile )
    except Exception as e:
        print("Warning: Error while creating OCIO lut from file.", e, "No lut will be applied.")
        
    return lut
    print('Create LUT succefully')
    print(lutInfo[1])
