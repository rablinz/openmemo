from openmemo.conversion.exceptions import ConversionFailure
import fnmatch
from openmemo.i18n import N_

class Importer (object):
    def _find_index_file(self, dir, patterns):
        files = dir.listdir()
        if len(files) == 1 and dir.isdir(files[0]):
            files = dir.listdir(files[0], full=True) 
        for pattern in patterns:
            match = fnmatch.filter(files, pattern)
            if match:
                if len(match) > 1:
                    raise ConversionFailure(N_(u"Multiple files {match} matches pattern '%(pattern)s'. Examined patterns: %(patterns)s"), 
                                            match=match, pattern=pattern, patterns=patterns)
                return match[0]
        raise ConversionFailure(N_(u"Couldn't find an index file. Examined patterns: %(patterns)s"), patterns=patterns)
    