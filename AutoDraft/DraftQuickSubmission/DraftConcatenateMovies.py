from __future__ import absolute_import
import os
import re
import fnmatch

import Draft
from DraftParamParser import ParseParams

def ConcatenateMovies( params ):
    expectedTypes = {
        "outFile" : '<string>'
    }

    params = ParseParams( expectedTypes, params )
    outFile = params['outFile']

    draftDir = os.path.dirname( outFile )
    stem, extension = os.path.splitext( os.path.basename( outFile ) )

    inputDict = {}
    for filename in os.listdir( draftDir ):
        if fnmatch.fnmatch( filename, stem + '_movie_chunk_*' + extension ):
            m = re.search('(?<=movie_chunk_)\w+', filename)
            if m:
                inputDict[int( m.group( 0 ) )] = filename

    # Sort the input filenames so the movie is concatenated in the right order
    inputs = []
    for firstFrameFilename in sorted( inputDict.items() ):
        inputs.append( os.path.join( draftDir, firstFrameFilename[1] ) )

    Draft.ConcatenateVideoFiles( inputs, outFile )

    for file in os.listdir( draftDir ):
        if fnmatch.fnmatch( file, stem + '_movie_chunk_*'  + extension ):
            try:
                os.remove( os.path.join( draftDir, file ) )
            except:
                continue
                