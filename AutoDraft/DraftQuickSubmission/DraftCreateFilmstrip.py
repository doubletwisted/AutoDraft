from __future__ import absolute_import, print_function
import sys

from six.moves import range

import Draft
import DraftParamParser

expectedTypes = {
    "frameList" : '<string>',
    "inFile" : '<string>',
    "outFile" : '<string>'
}

params = DraftParamParser.ParseCommandLine( expectedTypes, sys.argv )
frames = DraftParamParser.FrameRangeToFrames( params['frameList'] )

maxThumbs = 50 # maximum number of thumbnails to put in the filmstrip
count = min( len(frames), maxThumbs )

#figure out which frames to use in our thumbstrip
if count == 1:
    #easy case, return first item
    thumbFrames = [frames[0]]
elif count == 2:
    #easy case, return first + last items
    thumbFrames = [frames[0], frames[-1]]
else:
    #more complex
    skip = float(len(frames)) / float(count - 1)

    thumbFrames = []
    for i in range( 0, count - 1 ): #will grab count-1 frames
        pos = int( i * skip )
        thumbFrames.append( frames[pos] )

    thumbFrames.append( frames[-1] ) #grab very last frame as our final one

print("Using following frames for thumbnails: {0} ".format( thumbFrames ))

thumbWidth = 240
stripWidth = thumbWidth * len( thumbFrames )
stripImage = None

counter = 0

posSkip = 1.0 / len( thumbFrames )

for frameNum in thumbFrames:
    inFile = DraftParamParser.ReplaceFilenameHashesWithNumber( params['inFile'], frameNum )

    frame = Draft.Image.ReadFromFile( inFile )

    if not stripImage:
        #need to create the strip image now
        ratio = float( frame.width ) / frame.height
        print(ratio)
        stripHeight = int( thumbWidth / ratio )
        print(stripHeight)
        stripImage = Draft.Image.CreateImage( stripWidth, stripHeight )
        stripImage.SetToColor( Draft.ColorRGBA( 0.0, 0.0, 0.0, 1.0 ) ) #set black background to comp onto

    frame.Resize( thumbWidth, stripHeight, 'width' )
    print("resized to {0}x{1}".format( thumbWidth, stripHeight ))
    stripImage.CompositeWithPositionAndAnchor( frame, counter * posSkip, 0, Draft.Anchor.SouthWest, Draft.CompositeOperator.OverCompositeOp )

    counter += 1

    print("{0} / {1} done.".format( counter, len(thumbFrames)))

if stripImage:
    stripImage.WriteToFile( params['outFile'] )
