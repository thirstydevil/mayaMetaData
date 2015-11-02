import pymel.core as pCore

import tdtools.meta

tdtools.meta_Reload()
from nose.tools import eq_
from tdtools.eCoreTests import BaseTestClass
import tdtools.meta_testMetaData as _testMetaData

#tctest

#MAYA_TEST_FILES_DIR = os.path.dirname(__file__) + "/eMetaData/"
MAYA_TEST_FILES_DIR = "\\\\SERVER9\\Maya-Tools\\testFiles\\eMetaData\\"

def test_PluginLoading():
    assert pCore.pluginInfo('metaNode.py', query=True, loaded=True)

class TestFamilyTree(BaseTestClass):

    def setup(self):
        pCore.openFile(MAYA_TEST_FILES_DIR+"FamilyTree.mb", f=True)
        self.CreateFamily()

    def CreateFamily(self):
        self.Family = _testMetaData._tFamily()
        self.Family.SetFather("Fred")
        self.Family.SetMother("Willma")
        self.Family.SetSon("Rich")
        self.Family.SetDaughter("Lou")
        self.Family.AddHome("House")
        self.Family.AddCar("Car")

    def MakeFriendTree(self):
        '''
        Makes a simple network with MetaData that we can test against

            Rich
              |                Circle          Circle
             Friends            Mates          footy
            Ewan Jack Dan    Dan Ewan Jack      Will

            Lou
              |                 Circle        Circle
            Friends         SchoolFriends    BoyFriend
           Dan Sarah          Sarah Jes        Dan
        '''

        # Rich
        fTag = _testMetaData._tFriends("Rich")
        fTag.AddFriend("Ewan")
        fTag.AddFriend("Jack")
        fTag.AddFriend("Dan")

        # Rich circles
        c = fTag.CreateCircle("Mates")
        c.SetMember("Dan")
        c.SetMember("Ewan")
        c.SetMember("Jack")

        c = fTag.CreateCircle("footy")
        c.SetMember("Will")

        # lou
        fTag = _testMetaData._tFriends("Lou")
        fTag.AddFriend("Dan")
        fTag.AddFriend("Sarah")

        # lous circles
        c = fTag.CreateCircle("Boyfriend")
        c.SetMember("Dan")

        c = fTag.CreateCircle("SchoolFriends")
        c.SetMember("Sarah")
        c.SetMember("Jes")


    def Test_GetTagged(self):
        self.CreateFamily()
        t = [n.name() for n in self.Family.m_GetTagged()]
        assert t == [u"Willma", u"Fred", u"Rich", u"Lou", u"House", u"Car"]

    def Test_GetParts(self):
        self.CreateFamily()
        p = [p[0].name() for p in self.Family.m_GetParts()]
        assert p == [u"Willma", u"Fred", u"Rich", u"Lou"]

    def Test_GetFather(self):
        self.CreateFamily()
        f = self.Family.GetFather()
        assert f.name() == "Fred"

    def Test_GetMother(self):
        self.CreateFamily()
        f = self.Family.GetMother()
        assert f.name() == "Willma"

    def Test_GetCar(self):
        self.CreateFamily()
        cars = self.Family.GetCars()
        assert cars[0].name() == "Car"

    def Test_AddCar(self):
        self.CreateFamily()
        newCar = pCore.polyCube(n="CarNew")[0]
        self.Family.AddCar(newCar)
        assert self.Family.m_IsTagged(newCar)
        assert len(self.Family.GetCars()) == 2

    def Test_HiddenAttribute(self):
        self.CreateFamily()
        assert self.Family.Secretes == "Dad's got a promotion"
        assert not(self.Family.MetaNode.hasAttr("Secretes"))

    def Test_LockedAttributes(self):
        self.CreateFamily()
        assert not(self.Family.MetaNode.hasAttr("Address"))
        self.Family.Address = "1 Tile House"
        assert self.Family.MetaNode.Address.isLocked()

    def Test_ChangeAttribute(self):
        self.CreateFamily()
        self.Family.Address = "1 Tile House"
        assert self.Family.MetaNode.Address.get() == u"1 Tile House"
        self.Family.Address = {"Foo":"Bar"}
        assert self.Family.MetaNode.Address.get() == u'{"Foo": "Bar"}'

    def Test_GetRichFriendsNode(self):
        self.CreateFamily()
        self.MakeFriendTree()
        friends = eMetaData.MetaData.m_GetMetaData("Jack", MetaDataType="_tFriends")
        assert all((lambda x: isinstance(x, _testMetaData._tFriends), friends))

    def Test_GetMetaData(self):
        self.CreateFamily()
        self.MakeFriendTree()
        Data = eMetaData.MetaData.m_GetMetaData("Jack")
        assert len(Data) == 2
        assert all((lambda x: isinstance(x, _testMetaData._tCircle), Data))

    def Test_NoRefEdits_WhenGettingMetaData(self):
        pCore.cmds.file(MAYA_TEST_FILES_DIR + "FamilyTree_Cousins.mb", r=True)
        md = eMetaData.MetaData.m_GetMetaData("FamilyTree_Cousins_Jimmy")
        assert len(md) == 1
        assert md[0].MetaNode.isReferenced()
        refNode = md[0].MetaNode.referenceFile()
        assert refNode.getReferenceEdits() == []


class TestMetaData(BaseTestClass):
    def setup(self):
        self.SupressWindows(True)
        self.MetaNode = eMetaData.MetaData()
        self.TestNodes = []
        self.standardAttrs = {"MyString":"Test", "MyInt":5, "MyFloat":10.998547}

    def __AddTestNodes(self):
        cube = pCore.polyCube()[0]
        sphere = pCore.polySphere()[0]
        null = pCore.spaceLocator()
        metaNode = eMetaData.MetaData()
        self.TestNodes.extend([cube, sphere, null, metaNode.MetaNode])

    def tearDown(self):
        for node in self.TestNodes:
            try:
                pCore.delete(node)
            except:
                pass
        pCore.delete(pCore.ls(type="metaNode"))
        self.TestNodes = []
        self.standardAttrs = {"MyString":"Test", "MyInt":5, "MyFloat":10.998547, "MyBool":True}
        self.MetaNode = None
        self.SupressWindows(False)

    def test_AddStandardAttributes(self):
        for keys in self.standardAttrs:
            setattr(self.MetaNode, keys, self.standardAttrs[keys])

    def test_GetStandardAttributes(self):
        self.test_AddStandardAttributes()
        for keys in self.standardAttrs:
            eq_(getattr(self.MetaNode, keys), self.standardAttrs[keys])

    def test_GetTagged(self):
        eq_(self.MetaNode.m_GetTagged(), [])
        cube = pCore.polyCube()[0]
        self.TestNodes.append(cube)
        self.MetaNode.m_ConnectMetaDataTo(cube)
        eq_(self.MetaNode.m_GetTagged(), [cube])

    def test_SetName(self):
        self.MetaNode.m_SetName("FooBar")

    def test_GetName(self):
        self.test_SetName()
        name = self.MetaNode.m_GetName()
        eq_(self.MetaNode.m_GetName(), u"MetaData_FooBar")

    def test_ConnectMetaDataTo(self):
        self.__AddTestNodes()
        for n in self.TestNodes:
            self.MetaNode.m_ConnectMetaDataTo(n)
        assert all((lambda x: x in self.TestNodes, self.MetaNode.m_GetTagged()))

    def test_RegisterHiddenAttrself(self):
        self.MetaNode.m_RegisterHiddenAttr("Foo")
        self.MetaNode.Foo = "Bar"
        assert self.MetaNode.Foo == "Bar"
        assert self.MetaNode.MetaNode.hasAttr("Foo") == False

    def test_RegisterLockedAttr(self):
        self.MetaNode.m_RegisterLockedAttr("Foo")
        self.MetaNode.Foo = "Bar"
        assert self.MetaNode.Foo == "Bar"
        assert self.MetaNode.MetaNode.Foo.isLocked() == True

    def test_RegisterPrivateAttr(self):
        self.MetaNode.m_RegisterPrivateAttr("Foo")
        self.MetaNode.Foo = "Bar"
        assert self.MetaNode.Foo == "Bar"
        assert self.MetaNode.MetaNode.Foo.isLocked() == True
        assert self.MetaNode.MetaNode.Foo.isHidden() == True

    def test_SwapAttributeTypes(self):
        '''
        The standard types that will be created a a none json attribute are :-

        [str, unicode, int, bool, float, pCore.util.Enum, pCore.util.EnumValue, MetaEnumValue]

        They will be created as standard attributes on the MetaNode

        when swapping to a json data type the short name should change to be prefixed with "json_"
        this tells the MetaData to get the data as json.  Swapping between these types to json types should
        alternate this prefix
        '''

        standardTypes = [(str, "Test String"),
                         (unicode, "Test Unicode"),
                         (int, 10),
                         (bool, False),
                         (float, 0.0243 ),
                         (pCore.util.Enum, pCore.util.Enum("Colors", ["Red", "Blue", "Green"])),
                         #(pCore.util.EnumValue, pCore.util.EnumValue("Colors", 0, "Red")),
                         #(eMetaData.MetaEnumValue, eMetaData.MetaEnumValue("Colors", 0, "Blue"))
                         ]

        jsonData = {"Name":"Bar", "NumberList":[1,2,3]}
        for sType, instance in standardTypes:
            self.MetaNode.TestAttr = instance
            if type(instance) == pCore.util.Enum:
                self.MetaNode.TestAttr == eMetaData.MetaEnumValue("test", 0, "Red")
            else:
                assert self.MetaNode.TestAttr == instance
            assert self.MetaNode.MetaNode.TestAttr.shortName() == "TestAttr"
            # now swap to the json data
            self.MetaNode.TestAttr = jsonData
            assert self.MetaNode.TestAttr != instance
            print "old type", sType, instance
            assert self.MetaNode.MetaNode.TestAttr.shortName().startswith("json_")
            assert self.MetaNode.TestAttr == jsonData

    def test_AddJsonData(self):
        self.MetaNode.MyJsonList = [1, 2.00, "Foo", True, {"Foo": "Bar"}]
        assert self.MetaNode.MyJsonList == [1, 2.00, "Foo", True, {"Foo": "Bar"}]

        # test if the data isn't locked
        assert self.MetaNode.MetaNode.MyJsonList.isLocked() == False
        # now lock it
        self.MetaNode.m_RegisterLockedAttr("MyJsonList")
        assert self.MetaNode.MetaNode.MyJsonList.isLocked() == True
        # now swap the data back out to another Json data object and test the lock
        newData = {"Foo":"Bar", "ShouldBeLocked":True}
        self.MetaNode.MyJsonList = newData
        assert self.MetaNode.MetaNode.MyJsonList.isLocked() == True
        assert self.MetaNode.MyJsonList == newData


    def test_SetEnum(self):
        self.MetaNode.MyEnum = pCore.util.Enum("MyEnum", ("Red", "Greem", "Blue"))
        assert self.MetaNode.MetaNode.MyEnum.type() == "enum"

    def test_GetEnum(self):
        self.test_SetEnum()
        EnumVal = self.MetaNode.MyEnum
        assert isinstance(EnumVal, eMetaData.MetaEnumValue)
        assert EnumVal.index == 0
        assert EnumVal.key == "Red"
        assert EnumVal.enumtype == "MyEnum"

        self.MetaNode.MetaNode.MyEnum.set(2)
        EnumVal = self.MetaNode.MyEnum
        assert isinstance(EnumVal, eMetaData.MetaEnumValue)
        assert EnumVal.index == 2
        assert EnumVal.key == "Blue"
        assert EnumVal.enumtype == "MyEnum"
        assert EnumVal.__repr__() == "MetaEnumValue(u'MyEnum', 2, 'Blue')"

    def test_SetMetaEnumValue(self):
        self.test_SetEnum()
        self.MetaNode.MyEnum = eMetaData.MetaEnumValue(u'MyEnum', 2, 'Blue')
        EnumVal = self.MetaNode.MyEnum
        assert isinstance(EnumVal, eMetaData.MetaEnumValue)
        assert EnumVal == eMetaData.MetaEnumValue(u'MyEnum', 2, 'Blue')

    def test_InstanciateFromMetaDataNode(self):
        self.test_AddStandardAttributes()
        self.standardAttrs = {"MyString":"Test", "MyInt":5, "MyFloat":10.998547}

        self.MetaNode.MyString = "NewString"
        self.MetaNode.MyInt = 10
        self.MetaNode.MyFloat = .0999
        self.MetaNode.MyBool = False

        self.MetaNode.MyStringCustom = "Foo"
        self.MetaNode.MyIntCustom = 25
        self.MetaNode.MyFloatCustom = 0.11
        self.MetaNode.MyBoolCustom = True

        Data = eMetaData.MetaData("MetaData")
        assert Data.MyStringCustom == "Foo"
        assert Data.MyIntCustom == 25
        assert Data.MyFloatCustom == 0.11
        assert Data.MyBoolCustom == True

        assert Data.MyString == "NewString"
        assert Data.MyInt == 10
        assert Data.MyFloat == 0.0999
        assert Data.MyBool == False

    def test_ForceCreate(self):
        Data = _testMetaData._tMetaSubClass.m_ForceCreate(self.MetaNode, "Child")
        assert Data.m_Parents() == [self.MetaNode]
        Data = _testMetaData._tMetaSubClass.m_ForceCreate(self.MetaNode, "Parent")
        assert Data.m_Children() == [self.MetaNode]
        Data = _testMetaData._tMetaSubClass.m_ForceCreate()
        assert Data.m_Children() == []
        assert Data.m_Parents() == []

    def test_EqualTo(self):
        assert self.MetaNode == self.MetaNode
        assert (self.MetaNode == self.MetaNode.MetaNode) == False
        Data = eMetaData.MetaData()
        assert (self.MetaNode == Data) == False

    def test_repr(self):
        assert self.MetaNode.__repr__() == "MetaData(nt.MetaNode(u'MetaData'))"
        Data = _testMetaData._tMetaSubClass()
        assert Data.__repr__() == "_tMetaSubClass(nt.MetaNode(u'_tMetaSubClass'))"

    def test_HasMetaData(self):
        self.__AddTestNodes()
        self.MetaNode.m_ConnectMetaDataTo(self.TestNodes[0])
        assert self.MetaNode.m_HasMetaData(self.TestNodes[0]) == True
        assert self.MetaNode.m_HasMetaData(self.TestNodes[-1]) == False

    def test_GetDataFromMetaNodeNotClass(self):
        self.MetaNode.Foo = True
        self.MetaNode.MetaNode.Foo.set(False)
        assert self.MetaNode.Foo == False

    def test_Select(self):
        self.MetaNode.m_Select()
        assert pCore.selected()[0] == self.MetaNode.MetaNode

    def test_Type(self):
        assert self.MetaNode.m_Type() == eMetaData.MetaData

    def test_Walk(self):
        def CreateMetaGroupTree(Root):
            Level_1A = eMetaData.MetaData(Name="Level_1A")
            self.MetaNode.m_ConnectMetaDataTo(Level_1A)

            Level_1B = eMetaData.MetaData(Name="Level_1B")
            Level_1B.m_SetParent(self.MetaNode)

            Level_2A = eMetaData.MetaData(Name="Level_2A")
            Level_1A.m_SetChild(Level_2A)
            Level_2B = eMetaData.MetaData.m_ForceCreate(Level_1A, Name="Level_2B")
            Level_2C = eMetaData.MetaData.m_ForceCreate(Level_1A, Name="Level_2C")

            Level_2D = eMetaData.MetaData.m_ForceCreate(Level_1B, Name="Level_2D")
            Level_2E = eMetaData.MetaData.m_ForceCreate(Level_1B, Name="Level_2E")
            Level_2F = eMetaData.MetaData.m_ForceCreate(Level_1B, Name="Level_2F")

            Level_3A = eMetaData.MetaData.m_ForceCreate(Level_2A, Name="Level_3A")
            Level_3B = eMetaData.MetaData.m_ForceCreate(Level_2A, Name="Level_3B")
            Level_3C = eMetaData.MetaData.m_ForceCreate(Level_2A, Name="Level_3C")
            MGroup = eMetaData.MGroup(None, Level_1A, [Level_2A, Level_2B, Level_2C],
                                           GroupType="TestGroup", GroupName="MyGroup")

            return [Level_1A,
                  MGroup,
                  Level_2A,
                  Level_3A,
                  Level_3B,
                  Level_3C,
                  Level_2B,
                  Level_2C,
                  Level_1B,
                  Level_2D,
                  Level_2E,
                  Level_2F]

        result = CreateMetaGroupTree(self.MetaNode)
        walkForwards = ["MetaData_Level_1B",
                    "MetaData_Level_2E",
                    "MetaData_Level_2D",
                    "MetaData_Level_2F",
                    "MetaData_Level_1A",
                    "MGroup",
                    "MetaData_Level_2B",
                    "MetaData_Level_2A",
                    "MetaData_Level_3B",
                    "MetaData_Level_3A",
                    "MetaData_Level_3C",
                    "MetaData_Level_2C"]

        for i, M in enumerate(self.MetaNode.m_Walk()):
            i, M, walkForwards[i]
            #assert M.name() == walkForwards[i]


    def test_RefreshAE(self):
        assert self.MetaNode.m_RefreshAE() == True

class TestMGroup(BaseTestClass):
    def setup(self):
        self.SupressWindows(True)
        self.MetaGroup = eMetaData.MGroup(GroupName="RootTestGroup", GroupType="Test")
        self.TestNodes = []

    def _CreateGroups(self):
        A = self.MetaGroup.AddChildGroup("Foo")
        B = self.MetaGroup.AddChildGroup("Bar")
        C = B.AddChildGroup("BarChild")
        return [A, B, C]

    def tearDown(self):
        for node in self.TestNodes:
            try:
                pCore.delete(node)
            except:
                pass
        pCore.delete(pCore.ls(type="metaNode"))
        self.TestNodes = []
        self.MetaGroup = None
        self.SupressWindows(False)

    def test_AddChildGroup(self):
        groups = self._CreateGroups()
        a = self.MetaGroup.ChildGroups()
        assert self.MetaGroup.ChildGroups() == [groups[1], groups[0]]

    def test_HasChildGroup(self):
        self._CreateGroups()
        assert self.MetaGroup.HasChildGroup("Foo") == True

    def test_GetChildGroup(self):
        Groups = self._CreateGroups()
        assert self.MetaGroup.GetChildGroup("Bar") == Groups[1]

    def test_HasParentGroup(self):
        Groups = self._CreateGroups()
        assert Groups[2].HasParentGroup("Bar") == True

    def test_ChildGroups(self):
        assert self.MetaGroup.ChildGroups() == []
        Groups = self._CreateGroups()
        print self.MetaGroup.ChildGroups()
        assert self.MetaGroup.ChildGroups() == [Groups[1], Groups[0]]

    def test_ParentGroups(self):
        assert self.MetaGroup.ParentGroups() == []
        Groups = self._CreateGroups()
        assert Groups[1].ParentGroups() == [self.MetaGroup]


class TestSubClassing:
    def setup(self):
        self.MetaNode = None
        self.TestNodes = []
        self.RegisteredAttrs = {"MyHidden":10.999, "MyLocked":True, "MyPrivates":"Willy"}

    def tearDown(self):
        pCore.newFile(f=True)
        self.standardAttrs = {"MyString":"Test", "MyInt":5, "MyFloat":10.998547}
        self.MetaNode = None

    def test_CreateSubClass(self):
        self.MetaNode = _testMetaData._tMetaSubClass()
        assert isinstance(self.MetaNode, _testMetaData._tMetaSubClass)

    def test_SubClassedRegisteredAttrs(self):
        self.test_CreateSubClass()
        for attr in self.RegisteredAttrs:
            assert getattr(self.MetaNode, attr) == self.RegisteredAttrs[attr]
            if attr != "MyHidden":
                assert pCore.Attribute("%s.%s" % \
                                       (self.MetaNode.MetaNode, attr)).get() == self.RegisteredAttrs[attr]

    def test_InstanciateFromSubClassNode(self):
        self.test_CreateSubClass()
        Data = eMetaData.MetaData("_tMetaSubClass")
        assert isinstance(Data, _testMetaData._tMetaSubClass)
        assert issubclass(type(Data), eMetaData.MetaData)

    def test_KeyWordDefaults(self):
        self.test_CreateSubClass()
        assert self.MetaNode.DefaultKeyWord == "I'm the deafult"

    def test_AlterKeyWordDefault(self):
        self.MetaNode = _testMetaData._tMetaSubClass(DefaultKeyWord="Altered Default")
        assert self.MetaNode.DefaultKeyWord == "Altered Default"

    def test_SetKeyWordDefaults(self):
        self.MetaNode = _testMetaData._tMetaSubClass(DefaultKeyWord="Altered Default")
        Data = eMetaData.MetaData("_tMetaSubClass")
        key = Data.DefaultKeyWord
        assert Data.DefaultKeyWord == "Altered Default"