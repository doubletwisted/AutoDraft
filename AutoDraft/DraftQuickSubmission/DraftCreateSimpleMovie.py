from __future__ import absolute_import, print_function
import sys

import Draft
import DraftParamParser

expectedTypes = {
    "frameList" : '<string>',
    "inFile" : '<string>',
    "outFile" : '<string>'
}

params = DraftParamParser.ParseCommandLine( expectedTypes, sys.argv )
frames = DraftParamParser.FrameRangeToFrames( params['frameList'] )

inputPath = params['inFile']
outWidth = 1280
outHeight = 720

encoder = None
progressCounter = 0
lastPercentage = -1

for frameNum in frames:
    inFile = DraftParamParser.ReplaceFilenameHashesWithNumber( inputPath, frameNum )
    frame = Draft.Image.ReadFromFile( inFile )

    if not encoder:
        ratio = float(frame.width) / float(frame.height)
        # round width to nearest even number
        outWidth = int( round( 0.5 * ratio * outHeight ) * 2 )

        if frame.width != outWidth or frame.height != outHeight:
            print("WARNING: Resizing image from {0}x{1} to {2}x{3}".format( frame.width, frame.height, outWidth, outHeight ))

        print("Creating H264 video encoder ({0}x{1} @ {2}fps)".format( outWidth, outHeight, 24 ))
        encoder = Draft.VideoEncoder( params['outFile'], 24, outWidth, outHeight, codec='H264' )

    frame.Resize( outWidth, outHeight, 'height' )
    encoder.EncodeNextFrame( frame )

    progressCounter = progressCounter + 1
    percentage = progressCounter * 100 // len( frames )

    if percentage != lastPercentage:
        lastPercentage = percentage
        print("Encoding Progress: {0}%".format( percentage ))

if encoder:
    print("Finalizing encoding...")
    encoder.FinalizeEncoding()
    print("Done!")
