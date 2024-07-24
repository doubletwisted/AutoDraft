from __future__ import absolute_import, print_function
import Draft
import json
import os

try:
    from typing import Any
except ImportError:
    pass

from DraftParamParser import FrameRangeToFrames, ParseParams, ReplaceFilenameHashesWithNumber
from DraftCreateLuts import CreateLuts
from DraftCreateAnnotations import ChangeDefaultFramePadding, DrawAllAnnotations

def CreateImages( params ):
    # type: (Any) -> None
    expectedTypes = {
        "inFile" : '<string>',
        "outFile" : '<string>',
        "resolution" : '<float>',
        "codec" : '<string>',
        "quality": '<string>',
        "colorSpaceIn": '<string>',
        "colorSpaceOut": '<string>',
        "annotationsFilePath": '<string>',
        "annotationsFramePaddingSize": '<string>',
        "taskStartFrame" : '<int>',
        "taskEndFrame" : '<int>'
        }
    
    params = ParseParams( expectedTypes, params )

    inFilePattern = params['inFile']
    outFilePattern = params['outFile']
    resolution = params['resolution']
    compression = params['codec']
    quality = params['quality']
    colorSpaceIn = params['colorSpaceIn']
    colorSpaceOut = params['colorSpaceOut']
    annotationsFilePath = params['annotationsFilePath']
    annotationsFramePaddingSize = params['annotationsFramePaddingSize']
    taskStartFrame = params['taskStartFrame']
    taskEndFrame = params['taskEndFrame']
    
    taskFramesList = str( taskStartFrame ) + '-' + str( taskEndFrame )
    frames = FrameRangeToFrames( taskFramesList )

    progressCounter = 0
    lastPercentage = -1
    luts = []

    imageInfo = Draft.ImageInfo()

    # Set compression
    imageInfo.compression = compression
    
    # Set quality if necessary
    if quality != 'None':
        imageInfo.quality = int( quality )
    
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

    if annotationsFramePaddingSize != "None" and int( annotationsFramePaddingSize ) > 0:
        framePadding = "#" * int( annotationsFramePaddingSize )
        ChangeDefaultFramePadding( framePadding )
    else:
        ChangeDefaultFramePadding( "####" )
    
    # Create luts if necessary
    if colorSpaceIn != 'None' and colorSpaceOut != 'None':
        luts = CreateLuts( colorSpaceIn, colorSpaceOut )

    for currFrame in frames:
        # Read in current frame from file
        if( inFilePattern.find("#") != -1 ):
            currInFile = ReplaceFilenameHashesWithNumber( inFilePattern, currFrame )
        else:
            currInFile = inFilePattern
        frame = Draft.Image.ReadFromFile( currInFile )

        # Resize based on resolution
        newWidth = int( frame.width * resolution )
        newHeight = int( frame.height * resolution )
        frame.Resize( newWidth, newHeight, 'width', 'transparent' )

        for lut in luts:
            lut.Apply( frame )

        if annotationsDict:
            DrawAllAnnotations( frame, annotationsDict, currFrame )
        
        # Write current frame out to file
        if( inFilePattern.find("#") != -1 ):
            currOutFile = ReplaceFilenameHashesWithNumber( outFilePattern, currFrame )
        else:
            currOutFile = outFilePattern
        frame.WriteToFile( currOutFile, imageInfo )

        progressCounter = progressCounter + 1
        percentage = progressCounter * 100 // len( frames )

        if percentage != lastPercentage:
            lastPercentage = percentage
            print("Progress: {0}%".format( percentage ))
