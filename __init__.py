# Currently installed metaClass definitions, redefined on imports
import logging
import mCore
from metaData import *
import mAsset
import mExportTag

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

global RIGISTERED_METACLASS
metaData.registerMClassInheritanceMapping()

def _Reload():
    """
    Reloads the modules defined by this init and any other imported modules
    from used by them
    """

    reload(metaData)
    reload(mAsset)
    reload(mExportTag)
    metaData.registerMClassInheritanceMapping()



# Very Very Important
# -------------------

# Error: super(type, obj): obj must be an instance or subtype of type
# Traceback (most recent call last):
#   File "<maya console>", line 1, in <module>
#   File "G:/Maya/Maya_Modules/Modules/CoreLibs/PyLib\core\meta\mRig.py", line 738, in __init__
#     super(MShoulderTwister, self).__init__(RootJoint, **kw)
# TypeError: super(type, obj): obj must be an instance or subtype of type #

# The above error is because a sub module of the core.meta package has been reloaded.  This is not
# supported by eMetaData.MetaData as it's dynamically choosing the class types.  Python gets confused
# as the weak referring in the subclass structure is refreshed.  So... Don't reload sub packages at all.
#
# Dont do is in MEL IE (python(reload(meta.eMRig))) - This will break MetaData subclassing.
#
# Don't do it in Python packages outside of this package.  IE import meta.eMRig relaod(meta.eMRig)


# Important - See above
# ---------------------

# These are the cached subclasses of eMetaData.MetaData.  They have to be setup here as all the sub modules
# need to be loaded.  eMetaData.MetaData will use this set of class for it's dynamic class generation
# in it's __new__ method.


def RemoveUnusedMetaNodes():
    """Optimiser code for main file menu.  Does a basic connections check and then converts to MetaData if fails
    to run the m_IsValid method.  Finally deletes the metaNode"""
    for m in metaData.pCore.ls(type="network"):
        if not metaData.IsValidMetaNode(m):
            name = m.name()
            if not m.isReferenced():
                metaClass = metaData.MetaData(m)
                if not metaClass.m_IsValid():
                    try:
                        metaData.pCore.delete(m)
                        print "removed metaNode", name
                    except StandardError, Err:
                        raise Err

