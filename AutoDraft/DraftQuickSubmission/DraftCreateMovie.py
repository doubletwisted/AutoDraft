from __future__ import absolute_import, print_function
import json
import os

try:
    from typing import Any
except ImportError:
    pass

import Draft
from DraftParamParser import FrameRangeToFrames, ParseParams, ReplaceFilenameHashesWithNumber
from DraftCreateLuts import CreateLuts
from DraftCreateAnnotations import ChangeDefaultFramePadding, DrawAllAnnotations

def CreateMovie( params ):
    # type: (Any) -> None
    expectedTypes = {
        "inFile" : '<string>',
        "outFile" : '<string>',
        "resolution" : '<float>',
        "codec" : '<string>',
        "quality" : '<string>',
        "frameRate" : '<float>',
        "colorSpaceIn" : '<string>',
        "colorSpaceOut" : '<string>',
        "annotationsFilePath": '<string>',
        "isDistributed" : '<string>',
        "taskStartFrame" : '<int>',
        "taskEndFrame" : '<int>'
    }

    params = ParseParams( expectedTypes, params )
    
    inFilePattern = params['inFile']
    outFile = params['outFile']
    resolution = params['resolution']
    codec = params['codec']
    qualityString = params['quality']
    frameRate = params['frameRate']
    colorSpaceIn = params['colorSpaceIn']
    colorSpaceOut = params['colorSpaceOut']
    annotationsFilePath = params['annotationsFilePath']
    isDistributed = params['isDistributed']
    taskStartFrame = params['taskStartFrame']
    taskEndFrame = params['taskEndFrame']
    
    try:
        quality = int( qualityString )
    except:
        quality = 85
    
    taskFramesList = str( taskStartFrame ) + '-' + str( taskEndFrame )
    frames = FrameRangeToFrames( taskFramesList )

    # Append frame range to outFile if we are in distributed mode
    if( isDistributed == "True" ):
        outFile = os.path.splitext( outFile )[0] + taskFramesList + os.path.splitext( outFile )[1]

    encoder = None
    newWidth = -1
    newHeight = -1

    progressCounter = 0
    lastPercentage = -1
    luts = []

    # Create luts if necessary
    if colorSpaceIn != 'None' and colorSpaceOut != 'None':
        luts = CreateLuts( colorSpaceIn, colorSpaceOut )

    annotationsDict = None
    try:
        if annotationsFilePath.strip() != "None" and annotationsFilePath.strip() != "" and os.path.exists( annotationsFilePath ):
            annotationsFile = open( annotationsFilePath, 'r' )
            annotationsString = annotationsFile.read()
            annotationsFile.close()
            annotationsDict = json.loads( annotationsString )
            os.remove( annotationsFilePath )
    except Exception as e:
        print(e)

    ChangeDefaultFramePadding( "####" )

    for currFrame in frames:
        # Read in current frame from file
        currInFile = ReplaceFilenameHashesWithNumber( inFilePattern, currFrame )
        frame = Draft.Image.ReadFromFile( currInFile )
        
        # Determine the new dimensions
        if( newWidth == -1 or newHeight == -1 ):
            newWidth = int( frame.width * resolution )
            newHeight = int( frame.height * resolution )
            
            requestedWidth = newWidth
            requestedHeight = newHeight
            
            # In the case of DNXHD, make sure the dimensions are valid
            if( codec.lower() == 'dnxhd' ):
                if( newWidth <= 1280 and newHeight <= 720 ):
                    newWidth = 1280
                    newHeight = 720
                else:
                    newWidth = 1920
                    newHeight = 1080
            # In the case of H264, make sure the dimensions are even
            elif( codec.lower() == 'h264' ):
                if newWidth % 2 != 0:
                    newWidth = newWidth // 2 * 2
                if newHeight % 2 != 0:
                    newHeight = newHeight // 2 * 2
        
            if requestedWidth != newWidth or requestedHeight != newHeight:
                warningMsg = "Warning: Requested resolution " + str( requestedWidth ) + "x" + str( requestedHeight ) + " is not valid for codec " + codec + ". "
                warningMsg += "Will use resolution " + str( newWidth ) + "x" + str( newHeight ) + " instead."
                print(warningMsg)
        
        frame.Resize( newWidth, newHeight, 'fit', 'transparent' )
        
        for lut in luts:
            lut.Apply( frame )

        if annotationsDict:
            DrawAllAnnotations( frame, annotationsDict, currFrame )

        # Create the VideoEncoder
        if encoder is None:
            #old
            encoder = Draft.VideoEncoder( outFile, frameRate, newWidth, newHeight, codec = codec, quality = quality )
            #fix
            # fix
            #encoder = Draft.VideoEncoder(outFile, frameRate, newWidth, newHeight, codec=codec, kbitRate=int((int(quality) / 100) * 25000))
        
        # Encode current frame
        encoder.EncodeNextFrame( frame )
        
        progressCounter = progressCounter + 1
        percentage = progressCounter * 100 // len( frames )

        if percentage != lastPercentage:
            lastPercentage = percentage
            print("Encoding Progress: {0}%".format( percentage ))

    if encoder is not None:
        encoder.FinalizeEncoding()
