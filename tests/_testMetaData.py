'''
class's being used by the test frame work to make sure MetaData is working correctly
It's also a example of how you can write your a sub class of MetaData for your needs.
'''

import pymel.core as pCore

import metaData


class _tMetaSubClass(metaData.MetaData):
    def __init__(self, node=None, **kw):
        super(_tMetaSubClass, self).__init__(node, **kw)
        self.m_RegisterHiddenAttr("MyHidden")
        self.m_RegisterLockedAttr("MyLocked")
        self.m_RegisterPrivateAttr("MyPrivates")

        kw.setdefault("DefaultKeyWord", "I'm the deafult")
        self.m_SetInitialProperty("DefaultKeyWord", kw["DefaultKeyWord"], "Locked")
        self.MyHidden = 10.999
        self.MyLocked = True
        self.MyPrivates = "Willy"


class _tCircle(metaData.MetaData):
    def __init__(self, node=None, **kw):
        super(_tCircle, self).__init__(node, **kw)


    def SetMember(self, person, relationship):
        self.m_SetAsPart(person, {"relationship": relationship})


    def GetMember(self, relationship):
        for n, data in self.m_GetParts():
            try:
                if data["relationship"] == relationship:
                    return n
            except:
                pass


class _tFamily(_tCircle):
    '''
    Simple example of MetaData use.  Uses's single inheritence model with the
    base class implementing a setMember and GetMember wrapper over the MetaData "parts"
    methods.

    This is used in the test_eMetaData python file in the test folder to make sure
    that the base MetaData class is working as expected.
    '''


    def __init__(self, node=None, **kw):
        super(_tFamily, self).__init__(node, **kw)
        kw.setdefault("Origin", "British")
        self.m_SetInitialProperty("Origin", kw["Origin"], "Locked")

        # Should always be locked but editable via this tFamily class
        self.m_RegisterLockedAttr("Surname")
        self.m_RegisterLockedAttr("Address")

        # Serialised to the Maya Node but not exposed in AE or CB
        self.m_RegisterPrivateAttr("PhoneNumber")

        # This information only exists in the python instance and is never
        # serialised onto the Maya Node
        self.m_RegisterHiddenAttr("Secretes")
        self.Secretes = "Dad's got a promotion"


    def AddHome(self, home):
        self.m_ConnectMetaDataTo(home)


    def RemoveHome(self, home):
        if self.m_IsTagged(home):
            self.m_RemoveTag(home)


    def AddCar(self, car):
        self.m_ConnectMetaDataTo(car)


    def GetCars(self):
        res = []
        for n in self.m_GetTagged():
            if n.name().lower().startswith("car"):
                res.append(n)
        return res


    def RemoveCar(self, car):
        if self.m_IsTagged(car):
            self.m_RemoveTag(car)


    def GetHomes(self):
        res = []
        for n in self.m_GetTagged():
            if n.name().lower().startswith("house"):
                res.append(n)
        return res


    def GetSons(self):
        return self.GetMember("Son")


    def SetSon(self, member):
        self.SetMember(member, "Son")


    def GetDaughters(self):
        return self.GetMember("Daughter")


    def SetDaughter(self, member):
        self.SetMember(member, "Daughter")


    def GetFather(self):
        return self.GetMember("Father")


    def SetFather(self, member):
        self.SetMember(member, "Father")


    def SetMother(self, member):
        self.SetMember(member, "Mother")


    def GetMother(self):
        return self.GetMember("Mother")


    def SetCousin(self, member):
        self.SetMember(member, "Cousin")


    def GetCousins(self):
        return self.GetMember("Cousin")


class _tGroupCircle(_tCircle):
    def __init__(self, node=None, **kw):
        super(_tGroupCircle, self).__init__(node, **kw)
        self.m_SetInitialProperty("GroupName", "Ascociates", "Locked")


    def SetMember(self, member):
        self.m_ConnectMetaDataTo(member)


    def GetMembers(self):
        return self.m_GetTagged()


class _tFriends(_tCircle):
    def __new__(cls, *args, **kws):
        '''
        Warning: Only __new__() method with this decorator
        '''
        Node = None
        if args:
            Node = args[0]
        if Node:
            try:
                Node = pCore.PyNode(Node)
                if Node.type() != "metaNode":
                    f = metaData.MetaData.m_GetMetaData(Node, MetaDataType="tFreinds")
                    for m in f:
                        if m.GetOwner() == Node:
                            raise metaData.HasMetaDataError(Node.name(), cls.__name__)
            except metaData.HasMetaDataError as e:
                pCore.mel.warning(e.msg)
                return
        return super(cls.__class__, cls).__new__(cls)


    def __init__(self, node=None, **kw):
        super(_tFriends, self).__init__(node, **kw)
        node = pCore.PyNode(node)
        if node.type() != "metaNode":
            self.SetOwner(node)


    def GetOwner(self):
        for n in self.m_GetTagged():
            if n.hasAttr("owner"):
                if n.owner.inputs(type="metaNode") == [self.MetaNode]:
                    return n


    def SetOwner(self, node):
        node = pCore.PyNode(node)
        if not self.m_IsTagged(node):
            self.m_ConnectMetaDataTo(node)
        kw = {}
        kw.setdefault("m", True)
        kw.setdefault("im", False)
        if not node.hasAttr("owner"):
            node.addAttr("owner", **kw)
            self.MetaNode.metaLinks >> node.owner
        else:
            self.MetaNode.metaLinks >> node.owner


    def AddFriend(self, friend):
        self.m_ConnectMetaDataTo(friend)


    def GetCircles(self):
        return self.m_Children(MetaClass=_tGroupCircle)


    def GetCircleByName(self, name):
        for c in self.GetCircles():
            if c.GroupName == name:
                return c


    def CreateCircle(self, name):
        circle = self.GetCircleByName(name)
        if not circle:
            circle = _tGroupCircle()
            self.m_SetChild(circle)
            circle.GroupName = name
            return circle


