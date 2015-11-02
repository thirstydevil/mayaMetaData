'''
MetaData is data about data.  This module provides a base class `MetaData` that creates
a **metaNode** inside of maya.  The base class `MetaData` then provides methods to write
attributes to the created **metaNode**.  This can be achieved by simply setting attributes
onto the the MetaData instance or by modifing this behaviour in a sub class.  To then attach this
data into your system you can call `ConnectMetaDataTo` which physically connects to nodes together.

MetaData can also be connected to other **metaNodes** and therefore can be used to describe complex
systems, with a custom **meta hierarchy**.

MetaData can be connected to multiple nodes and nodes can have multiple **metaNodes** attached.

MetaData also has the concept of **Parts** providing methods such as GetPart and IsPart.  Part data
is a **dagNode** connected to the **metaNode** as if it was standard MetaData.  The only difference is
the dagNode has a attribute that starts with the "MetaData.__class__.__name__"+ "_Part".  This is useful
to describe subsystems within the MetaData.
'''

# Research a undo callback to remove MetaNode[0] attributes from connected nodes if metaNode is deleted
# see http://bit.ly/Ozotoz to read on how to handle problem
# code to reproduce the problem
# Add 2 message links.  Then delete on node to see the attribute isn't cleaned up.  Must leave in a referenced pipeline
# meta.eMetaData.MetaData("pCube1")
# meta.eMetaData.MetaData("pCube1")
# pCore.mel.removeMultiInstance("pCube1.MetaNode[1]") # cleans up the attr


import json
import inspect
import logging

import pymel.core as pCore
import maya.cmds as cmds

import mCore

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)


def registerMClassInheritanceMapping():
    global RIGISTERED_METACLASS
    RIGISTERED_METACLASS = {}
    RIGISTERED_METACLASS['MetaClass'] = MetaData
    for mclass in mCore.itersubclasses(MetaData):
        _logger.debug('registering MetaClass : %s' % mclass)
        RIGISTERED_METACLASS[mclass.__name__] = mclass


def registerMClass(mclass):
    global RIGISTERED_METACLASS
    RIGISTERED_METACLASS = {}
    RIGISTERED_METACLASS['MetaClass'] = MetaData
    RIGISTERED_METACLASS[mclass.__name__] = mclass


ANIMATED_EXPORT_PLUGS = ["matrix", "float3", "float", "double3", "double", "long"]
META_NODES = ['network']
ROOT_IGNORE_PLUGS = ['caching', 'isHistoricallyInteresting', 'binMembership', 'nodeState']
META_TRANSFORM_IGNORE_PLUGS = ['publishedNodeInfo']

META_NODE_IGNORE_PLUGS = {'metaNode': ROOT_IGNORE_PLUGS,
                          'network': ROOT_IGNORE_PLUGS,
                          'EMetaTransform': ROOT_IGNORE_PLUGS + META_TRANSFORM_IGNORE_PLUGS}


def IterFilterMetaNodesForClass(Nodes, ClassData, asMetaData=True):
    toFind = ""
    isList = False

    def toString(node):
        if issubclass(type(node), basestring):
            return node
        elif issubclass(node, MetaData):
            return node.__name__

    def isNode(node):
        if isList:
            return pCore.cmds.getAttr("%s.%s" % (node, "metaClass")) in toFind
        else:
            return pCore.cmds.getAttr("%s.%s" % (node, "metaClass")) == toFind

    if getattr(ClassData, "__iter__", None):
        toFind = [toString(n) for n in ClassData]
        isList = True
    else:
        toFind = toString(ClassData)

    if toFind:
        for m in Nodes:
            if isNode(m):
                if asMetaData:
                    yield MetaData(m)
                else:
                    yield m


def IterMetaNodesForClass(ClassData, asMetaData=True):
    """
    Iterates over the scene looking for a particular metaNode and yields any that match

    :param ClassData: str or Class of type META_NODES
    :param asMetaData: bool
    :return: [str,] or [MetaData,]
    """

    toFind = ""
    isList = False

    def toString(node):
        if issubclass(type(node), basestring):
            return node
        elif issubclass(node, MetaData):
            return node.__name__

    def isNode(node):
        if pCore.cmds.objExists("%s.%s" % (node, "metaClass")):
            if isList:
                return pCore.cmds.getAttr("%s.%s" % (node, "metaClass")) in toFind
            else:
                return pCore.cmds.getAttr("%s.%s" % (node, "metaClass")) == toFind

    if getattr(ClassData, "__iter__", None):
        toFind = [toString(n) for n in ClassData]
        isList = True
    else:
        toFind = toString(ClassData)

    if toFind:
        for m in IterAllMetaNodes(asMetaData=False):
            if isNode(m):
                if asMetaData:
                    yield MetaData(m)
                else:
                    yield m


def IterMetaNodesForBaseClass(MetaNodeClass, asMetaData=True):
    """
    Iterates over the scene looking for a particular metaNode and yields any that match

    :param MetaNodeClass: str or Class of type META_NODES
    :param asMetaData: bool
    :return: [str,] or [MetaData,]
    """
    toFind = ""
    if isinstance(MetaNodeClass, basestring):
        toFind = MetaNodeClass
    elif issubclass(MetaNodeClass, MetaData):
        toFind = MetaNodeClass.__name__
    if toFind:
        for m in pCore.cmds.ls(type=META_NODES):
            if pCore.objExists("%s.%s" % (m, "metaInheritance")):
                if toFind in json.loads(pCore.cmds.getAttr("%s.%s" % (m, "metaInheritance"))):
                    if asMetaData:
                        yield MetaData(m)
                    else:
                        yield m
            else:
                # This is for MetaData that doesn't have the metaInheritance attr and we split the name
                # by _ and returns [0]
                if pCore.objExists("%s.%s" % (m, "metaClass")):
                    klasses = pCore.cmds.getAttr("%s.%s" % (m, "metaClass")).split("_")
                    if toFind in klasses:
                        if asMetaData:
                            yield MetaData(m)
                        else:
                            yield m


def IterAllMetaNodes(asMetaData=True):
    """
    Wrapper the iterates over all metaNodes in the Scene
    :param asMetaData: bool
    :return: [str,] or [MetaData,]
    """
    for m in pCore.cmds.ls(type="network"):
        if pCore.cmds.objExists("%s.%s" % (m, "metaClass")):
            if asMetaData:
                yield MetaData(m)
            else:
                yield m


def GetMetaNodeClass(MayaNode):
    '''
    :Returns: <<Class>> class MetaNode cls from the Maya MetaNode
    '''
    global RIGISTERED_METACLASS
    MetaNode = pCore.PyNode(MayaNode)
    __metaKlass__ = str(MetaNode.metaClass.get())

    if RIGISTERED_METACLASS:
        _logger.debug("Using Cached mCore.itersubclasses set")
        for s in RIGISTERED_METACLASS:
            if RIGISTERED_METACLASS[s].__name__ == __metaKlass__:
                _logger.debug("mCore.itersubclasses >> %s" % s)
                return RIGISTERED_METACLASS[s]
    else:
        _logger.debug("Using non cached mCore.itersubclasses set")
        for s in mCore.itersubclasses(MetaData):
            if s.__name__ == __metaKlass__:
                _logger.debug("mCore.itersubclasses >> %s" % s)
                return s


def IsValidMetaNode(node):
    '''
    A Valid MetaNode as connections either to other metaNodes or tagged objects via
    the message arrays metaLinks and metaTagged
    :param node: str or PyNode
    :return: bool
    '''
    try:
        if any([pCore.listConnections("%s.metaLinks" % node),
                pCore.listConnections("%s.%s" % (node, "metaTagged"))]):
            return True
    except pCore.MayaAttributeError as e:
        pass
    return False


def GetConnectedMetaNode(MayaNode):
    node = pCore.PyNode(MayaNode)
    if getattr(node, "MetaNode", None):
        res = [n for n in node.MetaNode.inputs() if IsValidMetaNode(n)]
        if res:
            return res[0]


class MetaEnumValue(pCore.util.EnumValue):
    '''
    SubClass of pCore.util.EnumValue returned by Enum attributes on a MetaNode
    Useful because it has no had coded link to the pCore.util.EnumValue as __enumtype
    Also added a more generic __eq__ override so only key and index gets compared
    '''

    def __init__(self, enumtype, index, key, doc=None):
        """ Create an enumeration instance """
        self.__enumtype = enumtype
        self.__index = index
        self.__key = key
        self.__doc = doc
        super(MetaEnumValue, self).__init__(enumtype, index, key, doc=None)

    def __repr__(self):
        if self.__doc:
            return "MetaEnumValue({0!r:s}, {1!r:s}, {2!r:s}, {3!r:s}, {4!r:s})".format(
                self.__enumtype,
                self.__index,
                self.__key,
                self.__doc)
        else:
            return "MetaEnumValue({0!r:s}, {1!r:s}, {2!r:s})".format(self.__enumtype,
                                                                     self.__index,
                                                                     self.__key)

    def __eq__(self, Obj):
        if issubclass(type(Obj), pCore.util.EnumValue):
            if self.index == Obj.index and str(self.key) == str(self.key):
                return True
        return False


class MetaDataDecorators:
    """
    Decorator's for use with this module
    """

    @staticmethod
    def DebugInheritance(Log):
        import inspect

        def __init__(func):
            def with_logging(self, *args, **kwargs):
                argspec = inspect.getargspec(func)
                MRO = inspect.getmro(self.__class__)
                # Can't seem to get self.__class__ to be the current __init__ being logged
                _logger.debug("\nIntializing ... %s" % self.__class__)

                _logger.debug("%s" % argspec.__repr__())
                string = ("MRO:", [x.__name__ for x in MRO])
                _logger.debug(string)

                string = ("*args:", [x for x in args])
                _logger.debug(string)
                string = ("**kwargs:", [x for x in kwargs])
                _logger.debug(string)

                return func(self, *args, **kwargs)

            return with_logging

        return __init__

    @staticmethod
    def FilterGetParts(Index=0, List=False):
        '''
        Get Parts returns a tuple with (PyNode, PartData).
        If your only interested in the PyNode then you can get
        the PyNode using this decorator and then return the list or
        just the 1st element
        '''

        def funcWrap(func):
            def wrap(*args):
                res = func(*args)
                if res:
                    if List:
                        return [j[Index] for j in res]
                    else:
                        filteredList = [j[Index] for j in res]
                        if filteredList:
                            return filteredList[0]
                        else:
                            return None
                else:
                    if List: return []
                    return None

            return wrap

        return funcWrap

    @staticmethod
    def SearchPartDataDict(func):
        '''
        Search for data in dict stored on a MetaNode as PartData
        :param *args: Pass (Key, Value) pairs as tuples or a single `dict`
        :keyword Absolute: `bool` returns joints with *all* of the args passed
        '''

        def SeachFunc(self, *args, **kw):
            kw.setdefault("Absolute", True)
            if args:
                if isinstance(args[0], dict):
                    args = tuple(args[0].items())

            def Compare(Key, Value, Data):
                if not Data.has_key(Key): return False
                if issubclass(type(Value), str) and issubclass(type(Data[Key]), str):
                    if Value != None:
                        return Data[Key].upper() == Value.upper()
                    return Key.upper() == Data[Key].upper()
                else:
                    if Value != None:
                        return Data[Key] == Value
                    else:
                        return Data[Key] == Key

            def CompareWrap(Data):
                for Key, Value in args:
                    if not Compare(Key, Value, Data):
                        return False
                return True

            res = []
            if kw["Absolute"]:
                for Joint, Data in self.m_GetParts():
                    dataKey = CompareWrap(Data)
                    if dataKey:
                        res.append(Joint)
                return list(set(res))
            else:
                for Joint, Data in self.m_GetParts():
                    for Key, Value in args:
                        dataKey = Compare(Key, Value, Data)
                        if dataKey:
                            res.append(Joint)

                heatDict = {}
                cache = []
                for each in res:
                    if each not in cache:
                        cache.append(each)
                        if heatDict.has_key(res.count(each)):
                            heatDict[res.count(each)].append(each)
                        else:
                            heatDict[res.count(each)] = [each]
                res = []
                for keys in reversed(sorted(heatDict)):
                    res.append(heatDict[keys])
                return res

        return SeachFunc


class MetaData(object):
    '''
    This class is the base class of all MetaNodes in Maya.  It's role is to
    support the metaNode plug-in.  Creating a MetaNode instance will create a metaNode
    with in the Maya scene.  You can then add attributes to this class and the attribute
    will automatically added to the metaNode in Maya.  In truth this is a utility class that
    extends the metaNode plug-in so that interaction is easy through code.

    :param Node: `str` or `PyNode` that is either a dagNode you want to add metaData to or
    a **metaNode** itself.

    :keyword: METAVERSION, default = 1
    '''

    # This is the attribute that gets added to tagged/connected nodes
    MetaNodeMessageAttr = "MetaNode"

    def __new__(cls, *args, **kw):
        Node = None
        if args:
            Node = args[0]
        if Node:
            if isinstance(Node, MetaData):
                Node = pCore.PyNode(Node.MetaNode)
            else:
                Node = pCore.PyNode(Node)
            if Node.type() in META_NODES:
                if Node.hasAttr("metaClass"):
                    try:
                        metaClass = GetMetaNodeClass(Node)
                        if metaClass:
                            _logger.debug("Found MetaNode Class >> %r" % metaClass)
                            return super(cls.__class__, cls).__new__(metaClass)
                        else:
                            pass
                    except StandardError, Err:
                        _logger.exception(Err)
                        raise Err
            else:
                return super(cls.__class__, cls).__new__(cls)
        return super(cls.__class__, cls).__new__(cls)

    @MetaDataDecorators.DebugInheritance(_logger)
    def __init__(self, Node=None, **kw):
        # super at this level upsets multiple inheritance model
        # Prove my once more, do NOT do this with meta Data multiple inheritence
        # eg Mcharacter(MCharacterABC)

        # super(MetaData,self).__init__()

        kw = self.__CapKwargs(**kw)

        # Capture the default if they haven't been over-ridden
        kw.setdefault('METAVERSION', 1.0)
        kw.setdefault('NAME', "")
        self._HiddenAttributes = set(["__dict__",
                                      "__doc__",
                                      "__weakref__",
                                      "__module__",
                                      "nodeState",
                                      "caching",
                                      "_HiddenAttributes",
                                      "_LockedAttributes",
                                      "_PrivateAttributes",
                                      "_SerializeForExportAttributes",
                                      "_MetaNodeName",
                                      "_eHealthObject",
                                      "MetaNode",
                                      "PartAttributeName",
                                      "_STOPSET"])

        self._LockedAttributes = set(["metaClass",
                                      "metaVersion",
                                      "SerializeForExport",
                                      "metaInheritance"])
        self._PrivateAttributes = set([])
        self._SerializeForExportAttributes = set([])
        self._eHealthObject = None
        self._STOPSET = False

        # set the base internal properties, these are the ones on the MetaNode plug-in by default
        self.metaClass = self.__class__.__name__
        self.metaVersion = kw['METAVERSION']
        self.MetaNode = None
        self._MetaNodeName = kw['NAME']
        self.PartAttributeName = self.__class__.__name__ + "_Part"

        # If a Node has been given.  This node may be a MetaNode of a Node that we
        # want to tag with metaData.  Determine they type of node and the either
        # read the data back or create a new MetaNode
        if Node:
            if isinstance(Node, MetaData):
                Node = pCore.PyNode(Node.MetaNode)
            else:
                Node = pCore.PyNode(Node)

            # nType = Node.type(i=True)
            if Node.type() in META_NODES:
                self.__InstantiatedFromMetaDataNode(Node)

            # elif 'dagNode' in nType:
            # We need to check that the dagNode doesn't already have metaData.  If it does then
            # the best way to add extra data to the node is not passing the dagNode.  But instead
            # passing no Node and then connecting the metaData with ConnectMetaDataTo()
            if self.HasMetaNodeMessageAttr(Node):
                _logger.debug("dagNode %s has the MetaNode message attribute" % Node.name())
                metaNodeInputs = self.m_HasMetaData(Node)
                if metaNodeInputs:
                    self.__create__(Node, Name=kw["NAME"])
                    # raise StandardError("%s already has MetaNode" % Node.name())
                else:
                    self.__create__(Node, Name=kw["NAME"])
            else:
                self.__create__(Node, Name=kw["NAME"])
                # else:
                # raise StandardError("Expected MetaNode or a dagNode")
        else:
            self.__create__(Name=kw["NAME"])

        self._STOPSET = False

        if self.__MetaNodeExists():
            if not any([self.MetaNode.isReferenced(), self.MetaNode.isLocked()]):
                self.__fillInheritanceAttr()

                # sync the object data
                # self.__MetaNodeUpdate()

    def __create__(self, Node=None, Name="", metaType="network"):
        '''
        Create the MetaNode for this instance, Override to handle connecting
        data other nodes at creation time.  This where the self.__metaClass is
        set via the property metaClass
        '''
        NodeName = self.__class__.__name__
        if not self.m_Exists():
            if Name:
                NodeName = Name
            self.MetaNode = pCore.createNode(metaType, ss=True)
            if metaType == "network":
                self.__ensureAttrs__()

            self.m_SetName(NodeName)
            self.__MetaNodeSetAttr("metaClass", self.metaClass)
            if Node:
                self.m_ConnectMetaDataTo(Node)
            return True
        return False

    def __ensureAttrs__(self):
        import maya.OpenMaya as OpenMaya

        mAttr = OpenMaya.MFnMessageAttribute()
        MetaTagNode = self.MetaNode.__apimfn__()

        MetaTagNode.TagNetwork = mAttr.create("metaLinks", "mNetwork")
        mAttr.setArray(1)
        mAttr.setConnectable(1)
        mAttr.setIndexMatters(0)
        mAttr.setDisconnectBehavior(OpenMaya.MFnAttribute.kDelete)

        MetaTagNode.TaggedObject = mAttr.create("metaTagged", "mTagged")
        mAttr.setConnectable(1)
        mAttr.setArray(1)
        mAttr.setIndexMatters(0)
        mAttr.setDisconnectBehavior(OpenMaya.MFnAttribute.kDelete)

        MetaTagNode.addAttribute(MetaTagNode.TagNetwork)
        MetaTagNode.addAttribute(MetaTagNode.TaggedObject)

    def __setattr__(self, item, value):
        """
        Override the default implementation to include adding attributes to the MetaNode
        """
        super(MetaData, self).__setattr__(item, value)
        if not callable(value):
            if self.__MetaNodeExists():
                if self.__IsSerializable(item, value):
                    self.__MetaNodeSetAttr(item, value)
            else:
                _logger.debug("MetaNode not set on instance yet to add %s :: %s" % (item, value))

    def __getattribute__(self, attrName):
        '''
        Always try to get properties from the MetaNode in Maya before the PyObject instance
        '''
        # return any functions straight away
        attr_ = object.__getattribute__(self, attrName)
        if callable(attr_):
            _logger.debug("Getting callable from MetaData :: %s" % attrName)
            return attr_
        ## return attributes which are not serialised to the MetaNode or static attrs
        elif attrName in object.__getattribute__(self, "_HiddenAttributes"):
            return attr_
        else:
            try:
                object.__getattribute__(self, "MetaNode")
                try:
                    if object.__getattribute__(self, "_MetaNodeGetAttr"):
                        try:
                            func = object.__getattribute__(self, "_MetaNodeGetAttr")
                            data = func(attrName)
                            if type(data) == unicode:
                                return str(data)
                            else:
                                return data
                        except:
                            _logger.debug("Error Getting data from MetaNode :: %s" % attrName)
                            return object.__getattribute__(self, attrName)
                        return object.__getattribute__(self, attrName)
                    else:
                        _logger.debug("Getting data from Object Memory :: No MetaNode exists yet")
                        return object.__getattribute__(self, attrName)
                except StandardError, Err:
                    _logger.exception(Err)
                    return object.__getattribute__(self, attrName)
            except StandardError, Err:
                # _logger.exception(Err)
                return attr_

    def __delattr__(self, name):
        """
        Override the default implementation to include deleting attributes from the MetaNode
        """

        object.__delattr__(self, name)
        metaProperty = None

        if self.MetaNode:
            if self.MetaNode.hasAttr(name):
                metaProperty = pCore.Attribute('%s.%s' % (self.MetaNode, name))
                if metaProperty.isLocked():
                    metaProperty.setLocked(False)
                metaProperty.delete()
                self.m_RefreshAE()

    def __eq__(self, obj):
        if isinstance(obj, self.__class__):
            if obj.MetaNode and self.MetaNode:
                if obj.MetaNode == self.MetaNode:
                    return True
                else:
                    return False
            elif obj.__dict__ == self.__dict__:
                return True
            else:
                return False
        else:
            return False

    def __repr__(self):
        '''
        Debug class representation
        '''
        Node = ""
        if self.__MetaNodeExists():
            Node = self.MetaNode
        return "%s(%r)" % (self.__class__.__name__, Node)

    def __fillInheritanceAttr(self):
        '''
        fills the metaInheritance attribute on the metaNode
        :return:
        '''
        try:
            i = []
            for c in reversed(self.__class__.__mro__):
                if c != object:
                    i.append(c.__name__)
            self.metaInheritance = i
        except:
            pass

    def __AddMetaNodeMessageAttr(self, Node, **kw):
        '''
        Adds the message attribute responsible for hooking MetaData to nodes
        '''
        kw.setdefault("m", True)
        kw.setdefault("im", False)
        Node = str(Node)
        cmds.addAttr(Node, longName=self.MetaNodeMessageAttr, **kw)
        _attr = Node + "." + self.MetaNodeMessageAttr
        return _attr

    @classmethod
    def HasMetaNodeMessageAttr(cls, Node):
        '''
        :returns: if the message attribute responsible for hooking MetaData to nodes exists
        '''
        _attr = str(Node) + "." + cls.MetaNodeMessageAttr
        return cmds.objExists(_attr)

    @classmethod
    def GetMetaNodeMessageAttr(cls, Node, asString=False):
        '''
        :returns: if the message attribute responsible for hooking MetaData to nodes exists
        '''
        if cls.HasMetaNodeMessageAttr(Node):
            if asString:
                return str(Node) + "." + cls.MetaNodeMessageAttr
            else:
                Node = pCore.PyNode(Node)
                return getattr(Node, cls.MetaNodeMessageAttr)

    def __InstantiatedFromMetaDataNode(self, Node):
        '''
        Grabs all the Attributes on the MetaNode and sets them on the instance __dict__
        Used when we are creating a new instance of a metaNode from and existing metaNode in the scene
        IE MetaData("MyMetaNode")
        '''
        self.MetaNode = Node
        MetaNodeAttrs = self.m_GetMetaNodeAttributes()
        for attr in MetaNodeAttrs:
            name = str(attr.plugAttr(longName=True))
            value = self._MetaNodeGetAttr(attr.plugAttr(longName=True))
            super(MetaData, self).__setattr__(name, value)

    def __MetaNodeExists(self):
        '''
        Checks that this instance has the MetaNode and that the Node Exists in the Maya scene
        '''
        if self.__dict__.has_key('MetaNode') and self.__dict__['MetaNode']:
            if pCore.objExists(self.__dict__['MetaNode']):
                return True
        return False

    def __MetaNodeHasAttr(self, attrName):
        '''
        Wrap that checks for the MetaNode then the attribute
        :returns: `bool`
        '''
        if self.__MetaNodeExists():
            return self.MetaNode.hasAttr(attrName)
        return False

    def __IsSerializable(self, attributeName, value):
        '''
        :returns: If this attribute should be written to the MetaNode
        :rtype: `bool`
        '''
        _logger.debug("__IsSerializable :: %s , %s" % (attributeName, value))
        if attributeName in self._HiddenAttributes:
            _logger.debug("__IsSerializable >> FALSE")
            return False
        return True

    def __MetaNodeSetAttr(self, attributeName, value):
        '''
        A prerequisite is that the MetaNode exists and the property is a valid MetaProperty
        to set on the instance.  The __setattr__ method will then call this method.
        '''

        if self._STOPSET:
            _logger.warning("Set to not set Data via _STOPSET")
            return

        AttributeData = self.__GetAttributeDataDict(attributeName, value)
        if _logger.getEffectiveLevel() == logging.DEBUG:
            print "__MetaNodeSetAttr :: AttributeName=%s , Value=%s" % (attributeName, value)
            for keys in AttributeData:
                print "AttributeData[%s] = %s" % (keys, AttributeData[keys])
            print "\n"

        if AttributeData["Delete"] and AttributeData["PyNodeAttribute"]:
            if AttributeData["Locked"]:
                AttributeData["PyNodeAttribute"].setLocked(False)
            AttributeData["PyNodeAttribute"].delete()
            AttributeData["AddMethod"](attributeName, **AttributeData)
        elif AttributeData["PyNodeAttribute"]:
            try:
                if AttributeData["PyNodeAttributeType"] in [pCore.util.Enum, pCore.util.EnumValue,
                                                            MetaEnumValue]:
                    self.__SetEnumAttr(**AttributeData)
                elif AttributeData["AddMethod"] == self.__AddJsonAttr:
                    self.__SetJsonData(**AttributeData)
                else:
                    self.__SetStandardAttr(**AttributeData)
            except StandardError, Err:
                _logger.exception(Err)
        else:
            if AttributeData["Locked"] and AttributeData["PyNodeAttribute"]:
                AttributeData["PyNodeAttribute"].setLocked(False)
            AttributeData["AddMethod"](attributeName, **AttributeData)

        if AttributeData["Locked"]:
            try:
                # If it's the 1st time the attribute is created then this doesn't exists in the
                # dict
                AttributeData["PyNodeAttribute"].setLocked(True)
            except:
                try:
                    # Manually try to lock the 1st time created attrs
                    attr = pCore.Attribute("%s.%s" % (self.MetaNode, attributeName))
                    attr.setLocked(True)
                except:
                    pass

    def _MetaNodeGetAttr(self, PropertyName):
        '''
        prerequisite :: self.MetaNode and PropertyName must exist

        Gets the property from self.MetaNode. IE self.MetaNode.PropertyName.get().  Inspects
        the attribute on the MetaNode to understand what to return.  Attributes that shortName start
        with json_ will be decoded by the json parser.

        :returns: decoded attribute value
        '''
        pnAttr = pCore.PyNode("%s.%s" % (object.__getattribute__(self, "MetaNode"), PropertyName))
        pnAttrType = self.m_AttributeTypeToPythonType(pnAttr)
        if str(pnAttr.shortName()).startswith("json_"):
            _logger.debug("Getting data from MetaNode %s as JSON)" % pnAttr.longName())
            # strip unicode
            try:
                data = pnAttr.get().replace("u'", "'")
                return json.loads(str(data))
            except:
                return ""
        if pnAttrType == bool:
            _logger.debug("Getting data from MetaNode %s as bool(int)" % pnAttr.longName())
            return bool(pnAttr.get())
        elif pnAttrType == pCore.util.Enum:
            _logger.debug("Getting data from MetaNode %s as enum()" % pnAttr.longName())
            data = MetaEnumValue(pnAttr.longName(),
                                 pnAttr.get(),
                                 str(pnAttr.get(asString=True)))
            return data
        else:
            _logger.debug("Getting data from MetaNode %s" % pnAttr.longName())
            return pnAttr.get()

    def __MetaNodeUpdate(self):
        '''
        Loop through all the attributes on the object updating the MetaData
        '''
        if self.__MetaNodeExists():
            for property_ in self.__dict__:
                if self.__IsSerializable(property_, self.__dict__[property_]):
                    self.__MetaNodeSetAttr(property_, self.__dict__[property_])

    def __GetMetaNodeAttribute(self, AttributeName):
        try:
            return pCore.PyNode("%s.%s" % (object.__getattribute__(self, "MetaNode"), AttributeName))
        except:
            return None

    def __GetAttributeDataDict(self, attributeName, value):
        '''
        Collects data about the attribute and value into a dict so we can process it
        efficiently when added or updating the data

        :returns: `dict`
        '''
        StandardMayaTypes = [str, unicode, int, bool, float, pCore.util.Enum, pCore.util.EnumValue, MetaEnumValue]
        setLocked = attributeName in self._LockedAttributes
        setPrivate = attributeName in self._PrivateAttributes

        DataDict = dict(PyNodeAttribute=None, PyNodeAttributeType=None,
                        Delete=False, Locked=setLocked, Private=setPrivate, AddMethod=None, Value=value,
                        StandardTypes=StandardMayaTypes,
                        ValueType=self.m_GetPyObjectType(value))

        if self.__MetaNodeHasAttr(attributeName):
            DataDict["PyNodeAttribute"] = self.__GetMetaNodeAttribute(attributeName)
            DataDict["PyNodeAttributeType"] = self.m_AttributeTypeToPythonType(DataDict["PyNodeAttribute"])
            DataDict["Locked"] = DataDict["PyNodeAttribute"].isLocked()
            DataDict["Private"] = DataDict["PyNodeAttribute"].isHidden()

        if DataDict["ValueType"] in DataDict["StandardTypes"]:
            if DataDict["PyNodeAttribute"]:
                if DataDict["ValueType"] != DataDict["PyNodeAttributeType"]:
                    if DataDict["ValueType"] not in [pCore.util.EnumValue, MetaEnumValue]:
                        DataDict["Delete"] = True
                if DataDict["ValueType"] in [pCore.util.Enum]:
                    DataDict["AddMethod"] = self.__AddEnumAttr
                else:
                    DataDict["AddMethod"] = self.__AddStandardAttr

                if DataDict["PyNodeAttribute"].shortName().startswith("json_"):
                    DataDict["Delete"] = True
            else:
                if DataDict["ValueType"] == pCore.util.Enum:
                    DataDict["AddMethod"] = self.__AddEnumAttr
                else:
                    DataDict["AddMethod"] = self.__AddStandardAttr
        else:
            if DataDict["PyNodeAttributeType"] != str:
                DataDict["Delete"] = True
            elif DataDict["PyNodeAttribute"] and not (DataDict["PyNodeAttribute"].shortName().startswith("json_")):
                DataDict["Delete"] = True

            DataDict["AddMethod"] = self.__AddJsonAttr

        ## we have to delete Private Attributes because we can't set a visible attr to hidden
        if DataDict["Private"]:
            DataDict["Delete"] = True

        return DataDict

    def __AddEnumAttr(self, attributeName, **DataDict):
        valuesList = ":".join(["%s=%s" % (v.key, v.index) for v in DataDict["Value"].values()])
        if DataDict["Private"]:
            _logger.debug("setting property as as Private")
            self.MetaNode.addAttr(attributeName, at="enum", en=valuesList, h=True)
        else:
            self.MetaNode.addAttr(attributeName, at="enum", en=valuesList)
        DataDict["PyNodeAttribute"] = self.__GetMetaNodeAttribute(attributeName)

    def __SetEnumAttr(self, **DataDict):
        '''
        You can only set an EnumAttr if DataDict["ValueType"] is a EnumValue
        '''
        if DataDict["ValueType"] in [pCore.util.EnumValue, MetaEnumValue]:
            if DataDict["Value"].key in DataDict["PyNodeAttribute"].getEnums().keys() and \
                            DataDict["Value"].index == DataDict["PyNodeAttribute"].getEnums()[DataDict["Value"].key]:
                if DataDict["PyNodeAttribute"].isLocked():
                    DataDict["PyNodeAttribute"].setLocked(False)
            else:
                raise TypeError("Attemped to set and Invalid Enum, please make sure EnumValues match attr.getEnums")

            DataDict["PyNodeAttribute"].set(DataDict["Value"].index)

    def __AddJsonAttr(self, attributeName, **DataDict):
        if DataDict["Private"]:
            _logger.debug("setting property as as Private")
            self.MetaNode.addAttr(attributeName, sn="json_" + attributeName, dt="string", h=True)
        else:
            self.MetaNode.addAttr(attributeName, sn="json_" + attributeName, dt="string")
        DataDict["PyNodeAttribute"] = self.__GetMetaNodeAttribute(attributeName)
        _logger.debug("Adding %s as json data" % attributeName)
        self.__SetJsonData(**DataDict)
        # DataDict["PyNodeAttribute"].set(json.dumps(DataDict["Value"]))
        return DataDict

    def __SetJsonData(self, **DataDict):
        if DataDict["PyNodeAttribute"].isLocked():
            DataDict["PyNodeAttribute"].setLocked(False)
        DataDict["PyNodeAttribute"].set(json.dumps(DataDict["Value"]))

    def __AddStandardAttr(self, attributeName, **DataDict):
        if DataDict["ValueType"] == str:
            if DataDict["Private"]:
                _logger.debug("setting property as as Private")
                self.MetaNode.addAttr(attributeName, dt="string", h=True)
            else:
                self.MetaNode.addAttr(attributeName, dt="string", )
        else:
            if DataDict["Private"]:
                _logger.debug("setting property as as Private")
                self.MetaNode.addAttr(attributeName, at=DataDict["ValueType"], h=True)
            else:
                self.MetaNode.addAttr(attributeName, at=DataDict["ValueType"])

        DataDict["PyNodeAttribute"] = self.__GetMetaNodeAttribute(attributeName)
        self.__SetStandardAttr(**DataDict)
        return DataDict

    def __SetStandardAttr(self, **DataDict):
        _logger.debug("__SetStandardAttr :: %s" % DataDict["Value"])
        if DataDict["PyNodeAttribute"].isLocked():
            DataDict["PyNodeAttribute"].setLocked(False)
        DataDict["PyNodeAttribute"].set(DataDict["Value"])

    def __CapKwargs(self, **kw):
        '''
        Convert all the **kw to upper so that so it's easier to filter data
        '''
        res = {}
        for keys in kw:
            res[keys.upper()] = kw[keys]
        return res

    @staticmethod
    def m_FindConnectedMetaClass(StartNode, Node, upstream=True, ExcludeGroups=True, AsMetaData=True):
        '''
        Given a some data about the class your looking for.  This will return all
        the metaNode found on a metaNode.metaLinks direction.

        :param Node: `str`, `PyNode` or `MetaNode` where we're expecting the metaClass
        name as a `str` or the metaNode via a `MetaNode` or a `PyNode`
        :param upstream: `bool` set the direction
        :rtype `MetaNode`:
        '''

        if isinstance(Node, MetaData):
            data = pCore.PyNode(Node.MetaNode).metaClass.get()
        elif issubclass(type(Node), basestring):
            try:
                data = pCore.PyNode(Node.MetaNode).metaClass.get()
            except:
                data = Node
        else:
            try:
                if Node.__bases__[0] == MetaData or object:
                    data = Node.__name__
                else:
                    data = Node
            except:
                data = Node

        iter = []

        def getMetaClass(n, className):
            return pCore.cmds.getAttr("%s.metaClass" % n) == className

        if upstream:
            iter = (m for m in MetaData.m_FastIterParents(StartNode=StartNode, ExcludeGroups=ExcludeGroups) \
                    if getMetaClass(m, data))
        else:
            iter = (m for m in MetaData.m_FastIterChildren(StartNode=StartNode, ExcludeGroups=ExcludeGroups) \
                    if getMetaClass(m, data))

        result = []
        for n in iter:
            if AsMetaData:
                result.append(MetaData(n))
            else:
                result.append(n)
        return result

    def m_RefreshAE(self):
        '''
        Will deselect the metaNode and reselect if it's selected
        '''
        import AEmetaNodeTemplate

        oSel = pCore.cmds.ls(sl=True, l=True)
        if self.MetaNode.longName() in oSel:
            pCore.select(cl=True)
            pCore.dgdirty(a=True)
            AEmetaNodeTemplate.AEmetaNodeTemplate.reload()
            pCore.select(oSel)
            return True
        return True

    def m_SetInitialProperty(self, Name, Value, RegisterAs=None):
        '''
        It's important to understand how the __init__ of the MetaData works.  When sub-classing
        MetaData you will want to set a property for 1st time creation but use the properties on
        the MetaNode when you get a MetaData instance from an already existing node.  In this instance
        you will want to use this Method to set you properties in you subclass instance's __init__.
        '''
        if RegisterAs:
            if RegisterAs.upper() == "PRIVATE":
                self.m_RegisterPrivateAttr(Name)
            elif RegisterAs.upper() == "LOCKED":
                self.m_RegisterLockedAttr(Name)
            else:
                if RegisterAs.upper() == "HIDDEN":
                    self.m_RegisterHiddenAttr(Name)
        if self.__MetaNodeHasAttr(Name):
            _logger.debug("SetInitialProperty already has the attr %s" % Name)
        else:
            self.__setattr__(Name, Value)

    def m_SetPropertyMin(self, Name, Value):
        self.__GetMetaNodeAttribute(Name).setMin(Value)

    def m_SetPropertyMax(self, Name, Value):
        self.__GetMetaNodeAttribute(Name).setMax(Value)

    def m_SetPropertyKeyable(self, Name, Bool):
        if self.__MetaNodeHasAttr(Name):
            if Name in self._PrivateAttributes | self._HiddenAttributes:
                raise StandardError, "Private or Hidden properties can't be keyable"
            else:
                attr = self.__GetMetaNodeAttribute(Name)
                attr.setKeyable(Bool)

    def m_SetPropertyLocked(self, Name, Bool):
        '''
        Unregisters locked properties and unlocks the Maya attribute
        :param Name: existing propertyName
        :param Bool: `bool` True/False  True=Register and lock, Fasle=UnRegister and UnLock
        '''
        if self.__MetaNodeHasAttr(Name):
            if Name in self._HiddenAttributes:
                raise StandardError, " Hidden properties can't be locked"
            else:
                if Bool:
                    self.m_RegisterLockedAttr(Name)
                else:
                    if Name in self._LockedAttributes:
                        self._LockedAttributes.remove(Name)
                    self.__GetMetaNodeAttribute(Name).setLocked(Bool)

    def m_SerializePropertyForExport(self, Name, ExportName, Animated):
        '''
        The is for recording the MetaData in a lib withing the Collada.

        .. eg:

            self.FOV = 10.0
            self.m_SerializePropertyForExport("FOV", "FocalDistance", True)
            self.m_SerializeExportData()

        :param Name: The Name of the attribute you would like to serialize during the collada export
        :param ExportName: The name EL4 will use for the attribute
        :param Animated: Bool, True if the attribute us animated for example FOV
        :return: None
        '''
        if self.__MetaNodeExists():
            if not getattr(self.MetaNode, Name, None):
                raise AttributeError("MetaNode has no Attribute to serialise : %s" % Name)
            if Animated:
                pnAttr = getattr(self.MetaNode, Name)
                if pnAttr.type() not in ANIMATED_EXPORT_PLUGS:
                    raise TypeError("Attribute : %s is not a supported export animated type" % Name)

        data = (Name, ExportName, Animated)
        self._SerializeForExportAttributes.add(data)

    def m_GetSerializeForExportData(self):
        '''
        :return: [(attributeName, EL4AttributeName, IsAnimated),]
        '''
        return list(self._SerializeForExportAttributes)

    def m_SerializeExportData(self):
        '''
        Writes the SerializeForExport attribute with the data if the data exists
        :return: None
        '''
        data = self.m_GetSerializeForExportData()
        if data:
            self.SerializeForExport = data

    @classmethod
    def m_GetPyObjectType(cls, value):
        '''
        Gets a valid Maya type for standard Maya mapped types. IE types that can be
        added to the interface as standard.  If this returns None then the value
        should be added as Json data
        '''
        if type(value) in [str, unicode, int, bool, float, pCore.util.Enum, pCore.util.EnumValue, MetaEnumValue]:
            if issubclass(type(value), basestring):
                return str
            else:
                return type(value)
        else:
            return None

    @classmethod
    def m_AttributeTypeToPythonType(cls, pnAttr):
        '''
        Used by MetaData to understand what a Maya attribute.type() is equivalent to.
        For instance 'string' == `str`, 'double' == `float`

        :param pnAttr: pCore.Attribute
        :returns: `int`, `str`, `bool` etc or "string" of the Attribute.type() if it isn't compatible
                   python basetype
        '''
        if pnAttr.type() == "string":
            return str
        elif pnAttr.type() == "enum":
            return pCore.util.Enum
        elif pnAttr.type() == "bool":
            return bool
        elif pnAttr.type() == "double":
            return float
        elif pnAttr.type() == "long":
            return int
        else:
            return pnAttr.type()

    def m_RegisterPrivateAttr(self, attr):
        if isinstance(attr, basestring):
            self._LockedAttributes.add(attr)
            self._PrivateAttributes.add(attr)
            _logger.debug("Added %s as Private" % attr)
        else:
            raise TypeError()

    def m_RegisterHiddenAttr(self, attr):
        """
        Hidden Attibutes are not serialised to the MetaNode and are
        only stored in the class instance

        :param attr: string, name
        """
        if isinstance(attr, basestring):
            self._HiddenAttributes.add(attr)
        else:
            raise TypeError()

    def m_RegisterLockedAttr(self, attr):
        if isinstance(attr, basestring):
            self._LockedAttributes.add(attr)
            if self.MetaNode:
                if self.MetaNode.hasAttr(attr):
                    pCore.Attribute("%s.%s" % (self.MetaNode, attr)).setLocked(True)
        else:
            raise TypeError()

    @classmethod
    def m_GetConnectionMethod(cls, Node, SetNodeAs="Parent"):
        '''
        Returns: The correct connection method for the given node.  Basicaly all MetaNodes
        should be connected via SetParent an SetChild and PyNodes should be connected via
        connectMetaDataTo
        '''
        if isinstance(Node, MetaData) and Node.__MetaNodeExists():
            if SetNodeAs.upper() == "PARENT":
                return cls.m_SetChild
            else:
                return cls.m_SetParent
        else:
            Node = pCore.PyNode(Node)
            nType = Node.type(i=True)
            if "dagNode" in nType:
                return cls.m_ConnectMetaDataTo

    @classmethod
    def m_ForceCreate(cls, ConnectioNode=None, ConnectionType="Child", **kw):
        '''
        Because of the logic of the `MetaData` base class.  It's impossible to create
        MetaData and connect the new node to another MetaData object.

        If you want to do this at creation time then you should use this method.

        :param ConnectioNode: `PyNode`, `str` or `MetaData` class
        :param ConnectionType: "Child" or "Parent".  Calls `SetParent` or `SetChild` respectfully.

        example::

            >>> ZeroPose = MPose.ForceCreate(MetaData, PoseName="ZeroPose")
            >>> ZeroPose.AddPoseAttr("ControlArray", pCore.melGlobals["ControlArray"])
        '''
        if not any((ConnectionType == "Child", ConnectionType == "Parent",
                    ConnectionType == None, ConnectionType == "")):
            raise TypeError("param ConnectionType expected 'Child','Parent' or `None`, got %s" \
                            % ConnectionType)

        Klass = None

        def __Create(ConnectionType):
            Klass = cls(None, **kw)
            if ConnectionType:
                if ConnectionType == "Parent":
                    Klass.m_SetChild(ConnectioNode)
                elif ConnectionType == "Child":
                    ConnectioNode.m_SetChild(Klass)
            else:
                Klass.m_ConnectMetaDataTo(ConnectioNode)

            return Klass

        if ConnectioNode:
            connectionMethod = cls.m_GetConnectionMethod(ConnectioNode, ConnectionType)
            if connectionMethod:
                Klass = cls(None, **kw)
                if connectionMethod == cls.m_SetChild:
                    Klass.m_SetChild(ConnectioNode)
                elif connectionMethod == cls.m_SetParent:
                    ConnectioNode.m_SetChild(Klass)
                else:
                    Klass.m_ConnectMetaDataTo(ConnectioNode)
        else:
            Klass = cls(None, **kw)
        return Klass

    def m_GetTagged(self, asPyNode=True):
        '''
        Returns all the Maya nodes connected with this MetaNode

        :rtype: `list`
        '''

        if self.MetaNode:
            if asPyNode:
                return self.MetaNode.metaTagged.outputs(sh=True)
            else:
                res = cmds.listConnections("%s.metaTagged" % self.MetaNode, s=0, d=1, sh=1)
                if res is None: return []
                return res
        return []

    def m_RemoveTag(self, Node):
        if self.m_IsTagged(Node):
            self.m_DisConnectMetaDataFrom(Node)

    def m_IsTagged(self, Node):
        '''
        Is this node connected to this MetaData
        '''
        pnAttr = self.GetMetaNodeMessageAttr(Node, asString=True)
        if self.MetaNode and pnAttr:
            attr = "%s.metaTagged" % self.MetaNode
            connected = pCore.cmds.listConnections(attr, p=1)
            return pnAttr in connected
            # return bool(self.MetaNode.metaTagged.isConnectedTo(pnAttr,
            #                                                    checkLocalArray=True,
            #                                                    checkOtherArray=True))
        else:
            return False

    def m_GetTaggedWith(self, Node, MetaNodeClass, AsMetaData=False):
        '''
        :param MetaNodeClass: `class` (not instance) or `string`
        '''
        if issubclass(type(MetaNodeClass), basestring):
            return self.m_GetMetaData(Node, AsMetaData, MetaDataType=MetaNodeClass)
        elif inspect.isclass(MetaNodeClass):
            res = []
            metadata = self.m_GetMetaData(Node, AsMetaData=True)
            if metadata:
                for data in metadata:
                    if isinstance(data, MetaNodeClass):
                        res.append(data)
            return res

        elif issubclass(type(MetaNodeClass), self):
            res = []
            metadata = self.m_GetMetaData(Node, AsMetaData=True)
            if metadata:
                for data in metadata:
                    if issubclass(type(data), MetaNodeClass):
                        res.append(data)
            return res

    @property
    def m_DictMetaLinks(self):
        '''
        Returns a dict containing all the metaNodes attached to this MetaNode

        :rtype: `dict`
        :returns: dict(children=[], parents=[])
        '''

        if self.MetaNode:
            return dict(children=self.MetaNode.metaLinks.outputs(type='MetaNode'),
                        parents=self.MetaNode.metaLinks.inputs(type='MetaNode'))
        else:
            return []

    def m_GetName(self):
        '''
        Returns the self.MetaNode.Name() or self._MetaNodeName if no MetaNdoe exists
        '''
        if self.__MetaNodeExists():
            return self.MetaNode.name()
        else:
            try:
                if not self._MetaNodeName:
                    self._MetaNodeName = "Meta_1"
                return self._MetaNodeName
            except:
                self.m_SetName("")
                return self._MetaNodeName

    def m_SetName(self, Name, PrefixName=True):
        '''
        Sets the self.MetaNode.Name() and self._MetaNodeName

        :param Name: `string` Name of the MetaNdoe you want to set
        :param PrefixName: `bool` default is True and will prefix the metaNode with the class name ONLY if they are not
        the same
        '''
        shortName = Name.split(":")[-1]
        namespace = ":".join(Name.split(":")[:-1])
        if PrefixName:
            if self.__class__.__name__ == shortName:
                preFixedName = shortName
            else:
                preFixedName = self.__class__.__name__ + "_" + shortName
            Name = namespace + ":" + preFixedName
        else:
            Name = namespace + ":" + shortName

        if self.__MetaNodeExists():
            if not self.MetaNode.isReferenced():
                self.MetaNode.rename(str(Name))
            self._MetaNodeName = str(Name)
        else:
            self._MetaNodeName = str(Name)

    @classmethod
    def m_HasMetaData(cls, Node, **kw):
        '''
        :kw MetaDataType: `str` Name of the metaClass you want to check for.
        :returns: `bool`
        .. Note::
            Because the MetaNode attribute is added as and array.  We have to get all the
            elements and test them for the objects.
        '''

        kw.setdefault("MetaDataType", None)
        kw.setdefault("MetaDataRelaxedType", None)
        pnAttr = cls.GetMetaNodeMessageAttr(Node)
        if not pnAttr:
            return False
        for i in range(pnAttr.numElements()):
            try:
                for c in pnAttr[i].inputs():
                    if c.type() in META_NODES and pCore.objExists(c):
                        if kw["MetaDataType"]:
                            if c.metaClass.get() == kw['MetaDataType']:
                                return True
                            else:
                                continue
                        if kw["MetaDataRelaxedType"]:
                            if kw['MetaDataRelaxedType'] in c.metaClass.get():
                                return True
                            else:
                                continue
                        else:
                            return True
            except:
                pass
        return False

    def m_SetHealthObject(self, HealthObject):
        self._eHealthObject = HealthObject

    def m_HealthObject(self):
        return self._eHealthObject

    def m_GetHealthStatus(self):
        obj = self.m_HealthObject()
        if obj:
            return obj.GetStatus()
        return "Passed"

    def m_RunHealthCheck(self):
        obj = self.m_HealthObject()
        if obj:
            return obj.RunCheck()

    def m_GetMetaNodeAttributes(self, Node=None):
        '''
        Returns a list of `pymel.Attributes` that have been set on the MetaNode

        :rtype: `list`
        '''
        if Node:
            if isinstance(Node, MetaData):
                Node = pCore.PyNode(Node.MetaNode)
            else:
                Node = pCore.PyNode(Node)
            ignorePlugs = META_NODE_IGNORE_PLUGS[Node.type()]
            return [a for a in Node.listAttr(ud=True) \
                    if a.plugAttr(longName=True) not in ignorePlugs]

        else:
            if self.__MetaNodeExists():
                ignorePlugs = META_NODE_IGNORE_PLUGS[self.MetaNode.type()]
                return [a for a in self.MetaNode.listAttr(ud=True) \
                        if a.plugAttr(longName=True) not in ignorePlugs]
        return []

    def __NextAvailableArrayIndex(self, attr):
        """
        Find the nearest index to add a connection in the metaTags array

        :param Attr: `pCore.Attribute`
        :return: `int`
        """
        try:
            indices = set(int(x) for x in cmds.getAttr(str(attr), multiIndices=True))
        except TypeError:
            return 0

        diff = set(range(0, max(indices) + 2)) - indices
        return min(diff)
        # for i in Attr.getArrayIndices():
        #     SubAttr = pCore.Attribute("%s.%s" % (Attr, Attr.name(False)))
        #     if not SubAttr[i].isConnected():
        #         return i
        # else:
        #     index = Attr.getArrayIndices()
        #     if index:
        #         index = index[-1] + 1
        #     else:
        #         index = 0
        #     return index

    def m_IsMyParent(self, Node):
        if isinstance(Node, MetaData):
            Node = pCore.PyNode(Node.MetaNode)
        else:
            Node = pCore.PyNode(Node)

        if Node.type() in META_NODES:
            for n in self.m_Parents():
                if n.MetaNode == Node:
                    return True
        return False

    def m_IsMyChild(self, Node):
        if isinstance(Node, MetaData):
            Node = pCore.PyNode(Node.MetaNode)
        else:
            Node = pCore.PyNode(Node)

        if Node.type() in META_NODES:
            for n in self.m_Children():
                if n.MetaNode == Node:
                    return True
        return False

    def m_SetParent(self, Node, allowCyclicTree=False, autoDisconnect=True):
        '''
        Set a MetaNode as Parent via the meteLinks message array.

        :param MetaNode: `MetaNode` or `PyNode` of MetaNode
        '''
        if isinstance(Node, MetaData):
            Node = pCore.PyNode(Node.MetaNode)
        elif Node is None:
            self.MetaNode.metaLinks.disconnect()
            return
        else:
            Node = pCore.PyNode(Node)

        doIt = True
        if Node.type() in META_NODES:
            if self.m_IsMyChild(Node):
                if not allowCyclicTree:
                    doIt = False

            if doIt:
                if autoDisconnect:
                    try:
                        # this node may have another metaData parent
                        # autoDisconnect only allows 1 parent
                        # so get any parents of this node and remove this
                        # node from the parents children
                        currentParents = self.m_Parents()
                        for p in currentParents:
                            p.m_RemoveChild(self)
                    except:
                        pass
                if not self.m_IsMyParent(Node):
                    Index = self.__NextAvailableArrayIndex(self.MetaNode.metaLinks)
                    Node.metaLinks.connect(self.MetaNode.metaLinks[Index], f=True)
                else:
                    _logger.warning("%s is already a parent of %s" % (Node, self))
        else:
            raise TypeError("Expected MetaNode")

    def m_SetChild(self, Node, allowCyclicTree=False, autoDisconnect=True):
        '''
        Set a MetaNode as Child via the meteLinks message array.

        :param MetaNode: `MetaNode` or `PyNode` of MetaNode
        '''

        if isinstance(Node, MetaData):
            Node = pCore.PyNode(Node.MetaNode)
        elif Node is None:
            for n in self.m_Children():
                self.m_RemoveChild(n)
            return
        else:
            Node = pCore.PyNode(Node)

        doIt = True
        if Node.type() in META_NODES:
            if self.m_IsMyParent(Node):
                if not allowCyclicTree:
                    doIt = False
            if doIt:
                if autoDisconnect:
                    try:
                        # this node may have another metaData parent
                        # autoDisconnect only allows 1 parent
                        # so get any parents of this node and remove this
                        # node from the parents children
                        mNode = MetaData(Node)
                        parents = mNode.m_Parents()
                        for p in parents:
                            p.m_RemoveChild(mNode)
                    except:
                        pass
                if not self.m_IsMyChild(Node):
                    Index = self.__NextAvailableArrayIndex(Node.metaLinks)
                    self.MetaNode.metaLinks.connect(Node.metaLinks[Index], f=True)
                else:
                    _logger.warning("%s is already a child of %s" % (Node, self))
        else:
            raise StandardError("Expected MetaNode")

    def m_RemoveChild(self, Node):
        '''
        Set a MetaNode as Child via the meteLinks message array.

        :param MetaNode: `MetaNode` or `PyNode` of MetaNode
        '''
        if isinstance(Node, MetaData):
            Node = pCore.PyNode(Node.MetaNode)
        else:
            Node = pCore.PyNode(Node)

        if Node.type() in META_NODES:
            # note that we're now dealing with the Array of links for children
            if Node.metaLinks.getArrayIndices():
                for i in Node.metaLinks.getArrayIndices():
                    if self.MetaNode.metaLinks.isConnectedTo(Node.metaLinks[i]):
                        self.MetaNode.metaLinks // Node.metaLinks[i]
            else:
                self.MetaNode.metaLinks // Node.metaLinks
        else:
            raise StandardError("Expected MetaNode")

    def m_Walk(self, DownStream=True):
        '''
        Generator.  Walks over the MetaData heirarchy yeilding PyNode
        For speed, it doesn't return MetaData(i) as it's up to you
        to decide if you want to create the class to access the functions.
        This way walk can maintain it's speed.
        '''
        Visited = set([self.MetaNode])

        def _GetChildren(Node):
            for c in Node.metaLinks.outputs(type=META_NODES):
                if c not in Visited:
                    return c

        def _GetParents(Node):
            cache = set([])
            for c in Node.metaLinks.inputs(type=META_NODES):
                if c not in Visited:
                    return c
                cache.add(c)
            if cache:
                return list(cache)[0]
            else:
                return []

        def _GetSiblings(Node):
            res = set([])
            Parents = Node.metaLinks.inputs(type=META_NODES)
            for _ in Parents:
                res = res.union(set(Node.metaLinks.outputs(type=META_NODES)))
            return [n for n in res if n not in Visited]

        def _GetNodesInDirection(Node):
            if DownStream:
                return _GetChildren(Node)
            else:
                return _GetParents(Node)

        def _StepBack(Node):
            if not DownStream:
                return _GetChildren(Node)
            else:
                return _GetParents(Node)

        if self.MetaNode:
            NodesInDirection = _GetNodesInDirection(self.MetaNode)
            if NodesInDirection:
                Root = NodesInDirection
            else:
                Root = None
            i = 0
            while Root:
                i += 1
                if i > 4000:
                    Root = False
                    pCore.mel.warning("Walk maximum recursion reached... break")
                    break

                if Root not in Visited:
                    Visited.add(Root)
                    yield Root
                NodesInDirection = _GetNodesInDirection(Root)
                if NodesInDirection:
                    Root = NodesInDirection
                else:
                    if DownStream:
                        Siblings = _GetSiblings(Root)
                        if Siblings:
                            Root = Siblings[0]
                        else:
                            NodesInDirection = _GetNodesInDirection(Root)
                            if NodesInDirection:
                                Root = NodesInDirection
                            else:
                                BackNode = _StepBack(Root)
                                if BackNode:
                                    if BackNode == self.MetaNode:
                                        if not _GetNodesInDirection(BackNode):
                                            Root = False
                                        else:
                                            Root = BackNode
                                    else:
                                        Root = BackNode
                                else:
                                    Root = False
                    else:
                        Root = None

    @staticmethod
    def m_FastIterChildren(StartNode, ExcludeGroups=True):
        """
        Works like m_IterChildren but is a static method and uses cmds.
        :param StartNode: MetaNode to start from.
        :return: str
        """

        def __IncludeGroups():
            cons = pCore.cmds.listConnections('%s.metaLinks' % StartNode, d=1, s=0)
            if cons:
                for c in cons:
                    if pCore.cmds.objectType(c) not in META_NODES:
                        continue
                    yield c
            else:
                raise StopIteration

        def __ExcludeGroups():
            cons = pCore.cmds.listConnections('%s.metaLinks' % StartNode, d=1, s=0)
            if cons:
                for c in cons:
                    if pCore.cmds.objectType(c) not in META_NODES:
                        continue
                    if pCore.cmds.getAttr('%s.metaClass' % StartNode) == MGroup.__name__:
                        g = MetaData.m_FastIterChildren(c)
                        for o in g:
                            yield o
                    yield c
            else:
                raise StopIteration

        if ExcludeGroups:
            for i in __ExcludeGroups():
                yield i
        else:
            for i in __IncludeGroups():
                yield i

    def m_IterChildren(self, ExcludeGroups=True, AsMetaData=True):
        '''
        Iter over direct children.

        :rtype: `PyNode`
        :returns: Doesn't return a `MetaData` instance because of the overhead of __init__
                  Instead it's up to you to decide what to do with the MetaNode.
        '''

        for n in self.m_FastIterChildren(self.MetaNode, ExcludeGroups=ExcludeGroups):
            if AsMetaData:
                yield MetaData(n)
            else:
                yield n

    @staticmethod
    def m_FastIterParents(StartNode, ExcludeGroups=True):
        """
        Works like m_IterChildren but is a static method and uses cmds.
        :param StartNode: MetaNode to start from.
        :return: str
        """

        def __IncludeGroups():
            cons = pCore.cmds.listConnections('%s.metaLinks' % StartNode, d=0, s=1)
            if cons:
                for c in cons:
                    if pCore.cmds.objectType(c) not in META_NODES:
                        continue
                    yield c
            else:
                raise StopIteration

        def __ExcludeGroups():
            cons = pCore.cmds.listConnections('%s.metaLinks' % StartNode, d=0, s=1)
            if cons:
                for c in cons:
                    if pCore.cmds.objectType(c) not in META_NODES:
                        continue
                    if pCore.cmds.getAttr('%s.metaClass' % StartNode) == MGroup.__name__:
                        g = MetaData.m_FastIterChildren(c)
                        for o in g:
                            yield o
                    yield c
            else:
                raise StopIteration

        if ExcludeGroups:
            for i in __ExcludeGroups():
                yield i
        else:
            for i in __IncludeGroups():
                yield i

    def m_IterParents(self, ExcludeGroups=True, AsMetaData=True):
        '''
        Itter over direct parents.

        :rtype: `PyNode`
        :returns: Doesn't return a `MetaData` instance because of the overhead of __init__
                  Instead it's up to you to decide what to do with the MetaNode.
        '''

        for n in self.m_FastIterParents(self.MetaNode, ExcludeGroups=ExcludeGroups):
            if AsMetaData:
                data = MetaData(n)
                yield data
            else:
                yield n

    def m_GetParts(self, asPyNode=True):
        '''
        Parts are attributes on tagged objects in a MetaData system.  The Attribute
        added to the object will be treated as json data, so therefore must json
        compatible with json.  The attribute name will be self.__class__.__name__+"_Part".

        :rtype: [(PyNode,PartData),]
        '''
        if asPyNode:
            return [(pCore.PyNode(t), json.loads(str(cmds.getAttr("%s.%s" % (t, self.PartAttributeName))))) \
                    for t in self.m_GetTagged(asPyNode=False) if cmds.objExists("%s.%s" % (t, self.PartAttributeName))]
        else:
            return [(t, json.loads(str(cmds.getAttr("%s.%s" % (t, self.PartAttributeName))))) \
                    for t in self.m_GetTagged(asPyNode=False) if cmds.objExists("%s.%s" % (t, self.PartAttributeName))]

    def m_GetPartsWithData(self, Value):
        return [t for t in self.m_GetParts() if t[1] == Value]

    def m_IsPart(self, Node):
        if not self.m_IsTagged(Node): return False
        _attr = str(Node) + "." + self.PartAttributeName
        if cmds.objExists(_attr):
            return True
        else:
            return False

    def m_SearchSystem(self):
        raise NotImplementedError, "Subclasses must implement this functionality"

    @classmethod
    def m_GetAllPartData(cls, Node):

        def getAttrs(Node):
            Node = pCore.PyNode(Node)
            ignorePlugs = []
            try:
                ignorePlugs = META_NODE_IGNORE_PLUGS[Node.type()]
            except:
                pass
            return [a for a in Node.listAttr(ud=True) \
                    if a.plugAttr() not in ignorePlugs]

        attrIter = (at for at in getAttrs(Node) if at.name().find("_Part") != -1)
        res = []
        for attr in attrIter:
            res.append(json.loads(str(attr.get())))
        return res

    def m_GetPartData(self, Node, BypassIsPart=False):
        '''
        From this MetaData instance return the PartData on the Node given.

        :prop BypassIsPart: `bool` bypass's the IsPart check and reads the data is it can
        '''
        # Node = pCore.PyNode(Node)
        if not BypassIsPart:
            if not self.m_IsPart(Node): return None
            return json.loads(str(cmds.getAttr("%s.%s" % (Node, self.PartAttributeName))))
        else:
            return json.loads(str(cmds.getAttr("%s.%s" % (Node, self.PartAttributeName))))

    @classmethod
    def m_GetPartDataFromPartAttribute(cls, Node, Attr=None):
        '''
        From this MetaData instance return the PartData on the Node given.
        '''
        Node = pCore.PyNode(Node)
        if not Attr:
            Attr = cls.__name__ + "_Part"

        return json.loads(str(pCore.Attribute("%s.%s" % (Node, Attr)).get()))

    def m_SetAsPart(self, Node, Label):
        Node = str(Node)
        _attr = Node + "." + self.PartAttributeName
        if not self.m_IsTagged(Node):
            # _logger.debug("SetAsPart :: %s is Tagged" % Node)
            self.m_ConnectMetaDataTo(Node)
        if cmds.objExists(_attr):
            # _logger.debug("SetAsPart :: Attribute PartAttributeName exists:: %s on :: %s" % (self.PartAttributeName, Node))
            cmds.setAttr(_attr, l=False)
            cmds.setAttr(_attr, json.dumps(Label), type="string")
            cmds.setAttr(_attr, l=True)
        else:
            # _logger.debug("SetAsPart :: No PartAttributeName :: %s on :: %s" % (self.PartAttributeName, Node))
            cmds.addAttr(Node, longName=self.PartAttributeName, dt="string")
            cmds.setAttr(_attr, l=False)
            cmds.setAttr(_attr, json.dumps(Label), type="string")
            cmds.setAttr(_attr, l=True)

    def m_RemovePart(self, Node, deleteConnection=False):
        Node = pCore.PyNode(Node)
        if not self.m_IsTagged(Node):
            raise StandardError("Node is not attached to this MetaData")
        if Node.hasAttr(self.PartAttributeName):
            Attr = pCore.Attribute("%s.%s" % (Node, self.PartAttributeName))
            Attr.setLocked(False)
            Attr.delete()
        if deleteConnection:
            self.m_RemoveTag(Node)

    def m_Parents(self, MetaClass=None, ExcludeGroups=True):
        '''
        Return the metaNodes Parents

        :param MetaClass: `str`, `PyNode(MetaNode)` or `MetaData` class pointer
        '''

        if self.MetaNode:
            if MetaClass:
                return self.m_FindConnectedMetaClass(self.MetaNode, MetaClass, upstream=True,
                                                     ExcludeGroups=ExcludeGroups, AsMetaData=True)
            return [m for m in self.m_IterParents(ExcludeGroups=ExcludeGroups)]
        else:
            return []

    def m_Children(self, MetaClass=None, ExcludeGroups=True):
        '''
        Return the metaNodes Children
        '''
        if self.MetaNode:
            if MetaClass:
                return self.m_FindConnectedMetaClass(self.MetaNode, MetaClass, upstream=False,
                                                     ExcludeGroups=ExcludeGroups, AsMetaData=True)
            return [m for m in self.m_IterChildren(ExcludeGroups=ExcludeGroups)]
        else:
            return []

    def m_GetSiblings(self, MetaClass=None, ExcludeGroups=True):
        '''
        Get metaNodes on the same level as the current node.

        :rtype: `MetaData`
        '''
        res = []
        if self.MetaNode:
            Parents = self.m_Parents(MetaClass=MetaClass, ExcludeGroups=ExcludeGroups)
            if Parents:
                for Node in Parents:
                    for n in Node.m_IterChildren(ExcludeGroups=ExcludeGroups):
                        if n != self.MetaNode:
                            res.append(n)
        return res

    def m_Type(self):
        '''
        Same as type(self)
        '''
        return type(self)

    def m_IsExportTag(self):
        return "MExportTag" in self.MetaNode.metaClass.get()

    @classmethod
    def m_MetaNodeIsExportTag(cls, metaNode):
        metaNode = pCore.PyNode(metaNode)
        return "MExportTag" in metaNode.metaClass.get()

    def m_Select(self, **kws):
        '''
        Select the MetaNode
        '''

        if self.__MetaNodeExists():
            pCore.select(self.MetaNode, **kws)

    def m_Delete(self, *args, **kw):
        '''
        Delete the MetaNode
        '''

        if self.MetaNode:
            pCore.delete(self.MetaNode)
            del (self)

    def m_Exists(self):
        '''
        :rtype: `bool`
        :returns: if the metaNode exists
        '''
        return self.__MetaNodeExists()

    def m_IsValid(self):
        '''
        The basic m_IsValid is running the module level `IsValidMetaNode` method
        :return: bool
        '''
        if self.__MetaNodeExists():
            return IsValidMetaNode(self.MetaNode)
        return False

    @classmethod
    def m_GetMetaData(cls, Node, AsMetaData=True, **kw):
        '''
        Return all `MetaData` attached to this MayaNode.

        .. Note::

            This funcction is expecting a Maya Node and not a `MetaData.MetaNode`

        :param Node: `str` or `PyNode`
        :keyword MetaDataType: `str` of the metaClass to search for
        :rtype: `list`
        '''

        kw.setdefault("MetaDataType", None)
        Node = pCore.PyNode(Node)
        res = []
        pnAttr = cls.GetMetaNodeMessageAttr(Node)
        if pnAttr:
            if kw["MetaDataType"]:
                if AsMetaData:
                    res = [MetaData(n) for n in pnAttr.inputs(type=META_NODES) \
                           if n.metaClass.get() == kw['MetaDataType']]
                else:
                    res = [n for n in pnAttr.inputs(type=META_NODES) \
                           if n.metaClass.get() == kw['MetaDataType']]
            elif AsMetaData:
                res = [MetaData(n) for n in pnAttr.inputs(type=META_NODES)]
            else:
                res = [n for n in pnAttr.inputs(type=META_NODES)]
        return list(set(res))

    def m_ConnectMetaDataTo(self, Node, **kw):
        '''
        Connect the MetaData to a Maya dagNode

        :param Node: `str` or `PyNode`
        '''
        kw.setdefault("f", True)
        kw.setdefault("na", True)

        if self.MetaNode:
            if issubclass(type(Node), MetaData):
                if Node.__MetaNodeExists():
                    self.m_SetChild(Node)
                    return
            pnAttr = self.GetMetaNodeMessageAttr(Node, asString=True)
            if not pnAttr:
                pnAttr = self.__AddMetaNodeMessageAttr(Node)
            # _logger.debug("Connecting MetaNode %s to %s, attr: %s" % (self.MetaNode.name(), Node, pnAttr))
            try:
                index = self.__NextAvailableArrayIndex(self.MetaNode.metaTagged)
                self.MetaNode.metaTagged[index].connect(pnAttr, **kw)
            except StandardError as e:
                raise e
        else:
            raise StandardError("MetaNode not set on instance")

    def m_DisConnectMetaDataFrom(self, Node, **kw):
        '''
        DisConnect the MetaData to a Maya dagNode

        :param Node: `str` or `PyNode`
        '''
        kw.setdefault("na", True)
        if self.MetaNode:
            if issubclass(type(Node), MetaData):
                if Node.__MetaNodeExists():
                    self.m_RemoveChild(Node)
                    return
            else:
                Node = pCore.PyNode(Node)
            pnAttr = self.GetMetaNodeMessageAttr(Node)
            if pnAttr:
                _logger.debug("DisConnecting MetaNode %s to %s" % (self.MetaNode.name(), Node))
                self.MetaNode.metaTagged.disconnect(pnAttr, **kw)
        else:
            raise StandardError("MetaNode not set on instance")


class MGroup(MetaData):
    '''
    MGroup is a empty MetaData Node that's primary use is to tidy the hypershade and
    also to group MetaData or Maya dagNodes together.  It should be used as such.
    '''

    def __init__(self, Node=None, Parent=None, Children=None, **kw):
        MetaData.__init__(self, Node, **kw)
        kw.setdefault("GroupType", "")
        kw.setdefault("GroupName", "")
        self.m_SetInitialProperty("GroupType", kw["GroupType"], "Locked")
        self.m_SetInitialProperty("GroupName", kw["GroupName"], "Locked")

        if Parent:
            if isinstance(Parent, MetaData):
                pass
            elif isinstance(Parent, str) or isinstance(Parent, str):
                Parent = MetaData(pCore.PyNode(Parent))
            Parent.m_SetChild(self)

        _Children = []
        if Children:
            if getattr(Children, '__iter__', False):
                for i in Children:
                    if isinstance(i, MetaData):
                        _Children.append(i)
                    elif isinstance(i, str) or isinstance(i, str):
                        _Children.append(MetaData(pCore.PyNode(i)))
            else:
                if isinstance(Children, MetaData):
                    _Children.append(Children)
                elif isinstance(Children, str) or isinstance(Children, str):
                    _Children.append(MetaData(pCore.PyNode(Children)))

        if _Children:
            for c in _Children:
                self.m_SetChild(c)

    def ChildGroups(self):
        return [g for g in self.m_Children("MGroup", False) if g.GroupType == self.GroupType]

    def ParentGroups(self):
        return [g for g in self.m_Parents("MGroup", False) if g.GroupType == self.GroupType]

    def AddChildGroup(self, GroupName):
        if not self.HasChildGroup(GroupName):
            Group = self.__class__(None, self, GroupName=GroupName,
                                   GroupType=str(self.GroupType))
            Group.m_SetName(GroupName)
            return Group
        else:
            _logger.warning("MGroup already has child with GroupName : %s" % GroupName)
            return self.GetChildGroup(GroupName)

    def HasChildGroup(self, GroupName):
        return bool([g for g in self.m_Children("MGroup", False) if g.GroupName == GroupName])

    def HasParentGroup(self, GroupName):
        return bool([g for g in self.m_Parents("MGroup", False) if g.GroupName == GroupName])

    def GetChildGroup(self, GroupName):
        cache = [g for g in self.m_Children("MGroup", False) if g.GroupName == GroupName]
        if cache:
            return cache[0]
        else:
            return None

    def GetParentGroup(self, GroupName):
        cache = [g for g in self.m_Parents("MGroup", False) if g.GroupName == GroupName]
        if cache:
            return cache[0]
        else:
            return None


class MetaTransform(MetaData):
    def __init__(self, Node=None, **kw):
        super(MetaTransform, self).__init__(Node, **kw)

    def __create__(self, Node=None, Name="", metaType="EMetaTransform"):
        metaType = "EMetaTransform"
        return super(MetaTransform, self).__create__(Node, Name, metaType)


class Error(Exception):
    """Base class for exceptions in eMetaData Module."""
    pass


class HasMetaDataError(Error):
    """
    Exception raised when a node already has MetaData of that type attached.
    Used in MCharacter for instance as there should only be one MCharacter attached
    to the rig

    :param Node: `str` Name of the node that has the MetaData
    :param MetaDataClass: `str` Name of the MetaDataClass
    """

    def __init__(self, Node, MetaDataClass):
        self.msg = "%s already has %s MetaData" % (Node, MetaDataClass)


class MultipleIndexError(Error):
    """
    Exception raised when 2 or more nodes in the array have the same index"""

    def __init__(self, msg):
        self.msg = msg
