#!/usr/bin/env python
# 
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
# 
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the LSST License Statement and 
# the GNU General Public License along with this program.  If not, 
# see <http://www.lsstcorp.org/LegalNotices/>.
#
import time
import unittest

import lsst.utils.tests as utilsTests
import lsst.daf.base as dafBase
import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase

class AddConfig(pexConfig.Config):
    addend = pexConfig.Field(doc="amount to add", dtype=float, default=3.1)

class AddTask(pipeBase.Task):
    ConfigClass = AddConfig

    @pipeBase.timeMethod
    def run(self, val):
        return pipeBase.Struct(
            val = val + self.config.addend,
        )

class MultConfig(pexConfig.Config):
    multiplicand = pexConfig.Field(doc="amount by which to multiply", dtype=float, default=2.5)

class MultTask(pipeBase.Task):
    ConfigClass = MultConfig

    @pipeBase.timeMethod
    def run(self, val):
        return pipeBase.Struct(
            val = val * self.config.multiplicand,
        )

class AddMultConfig(pexConfig.Config):
    add = pexConfig.ConfigurableField(doc="", target=AddTask)
    mult = pexConfig.ConfigurableField(doc="", target=MultTask)

class AddMultTask(pipeBase.Task):
    ConfigClass = AddMultConfig
    _DefaultName = "addMult"

    """First add, then multiply"""
    def __init__(self, **keyArgs):
        pipeBase.Task.__init__(self, **keyArgs)
        self.makeSubtask("add")
        self.makeSubtask("mult")

    @pipeBase.timeMethod
    def run(self, val):
        with self.timer("context"):
            addRet = self.add.run(val)
            multRet = self.mult.run(addRet.val)
            return pipeBase.Struct(
                val = multRet.val,
            )
    
    @pipeBase.timeMethod
    def failDec(self):
        """A method that fails with a decorator
        """
        raise RuntimeError("failDec intentional error")
    
    def failCtx(self):
        """A method that fails inside a context manager
        """
        with self.timer("failCtx"):
            raise RuntimeError("failCtx intentional error")

class AddTwiceTask(AddTask):
    """Variant of AddTask that adds twice the addend"""
    def run(self, val):
        addend = self.config.addend
        return pipeBase.Struct(val = val + (2 * addend))


class TaskTestCase(unittest.TestCase):
    """A test case for Task
    """
    def setUp(self):
        self.valDict = dict()
        
    def tearDown(self):
        self.valDict = None

    def testBasics(self):
        """Test basic construction and use of a task
        """
        for addend in (1.1, -3.5):
            for multiplicand in (0.9, -45.0):
                config = AddMultTask.ConfigClass()
                config.add.addend = addend
                config.mult.multiplicand = multiplicand
                addMultTask = AddMultTask(config=config)
                for val in (-1.0, 0.0, 17.5):
                    ret = addMultTask.run(val=val)
                    self.assertAlmostEqual(ret.val, (val + addend) * multiplicand)
    
    def testNames(self):
        """Test getName() and getFullName()
        """
        addMultTask = AddMultTask()
        self.assertEqual(addMultTask.getName(), "addMult")
        self.assertEqual(addMultTask.add.getName(), "add")
        self.assertEqual(addMultTask.mult.getName(), "mult")

        self.assertEqual(addMultTask.getFullName(), "addMult")
        self.assertEqual(addMultTask.add.getFullName(), "addMult.add")
        self.assertEqual(addMultTask.mult.getFullName(), "addMult.mult")
    
    def testGetFullMetadata(self):
        """Test getFullMetadata()
        """
        addMultTask = AddMultTask()
        fullMetadata = addMultTask.getFullMetadata()
        self.assertTrue(isinstance(fullMetadata.getPropertySet("addMult"), dafBase.PropertySet))
        self.assertTrue(isinstance(fullMetadata.getPropertySet("addMult:add"), dafBase.PropertySet))
        self.assertTrue(isinstance(fullMetadata.getPropertySet("addMult:mult"), dafBase.PropertySet))
            
    def testReplace(self):
        """Test replacing one subtask with another
        """
        for addend in (1.1, -3.5):
            for multiplicand in (0.9, -45.0):
                config = AddMultTask.ConfigClass()
                config.add.retarget(AddTwiceTask)
                config.add.addend = addend
                config.mult.multiplicand = multiplicand
                addMultTask = AddMultTask(config=config)
                for val in (-1.0, 0.0, 17.5):
                    ret = addMultTask.run(val=val)
                    self.assertAlmostEqual(ret.val, (val + (2 * addend)) * multiplicand)
    
    def testFail(self):
        """Test timers when the code they are timing fails
        """
        addMultTask = AddMultTask()
        try:
            addMultTask.failDec()
            self.fail("Expected RuntimeError")
        except RuntimeError:
            self.assertIsNotNone(addMultTask.metadata.get("failDecEndCpuTime", None))
        try:
            addMultTask.failCtx()
            self.fail("Expected RuntimeError")
        except RuntimeError:
            self.assertIsNotNone(addMultTask.metadata.get("failCtxEndCpuTime", None))
        
    
    def testNames(self):
        """Test task names
        """
        addMultTask = AddMultTask()
        self.assertEquals(addMultTask._name, "addMult")
        self.assertEquals(addMultTask.add._name, "add")
        self.assertEquals(addMultTask.mult._name, "mult")
        self.assertEquals(addMultTask._fullName, "addMult")
        self.assertEquals(addMultTask.add._fullName, "addMult.add")
        self.assertEquals(addMultTask.mult._fullName, "addMult.mult")
    
    def testTimeMethod(self):
        """Test that the timer is adding the right metadata
        """
        addMultTask = AddMultTask()
        addMultTask.run(val=1.1)
        currCpuTime = time.clock()
        self.assertLessEqual(
            addMultTask.metadata.get("runStartCpuTime"),
            addMultTask.metadata.get("runEndCpuTime"),
        )
        self.assertLessEqual(addMultTask.metadata.get("runEndCpuTime"), currCpuTime)
        self.assertLessEqual(
            addMultTask.metadata.get("contextStartCpuTime"),
            addMultTask.metadata.get("contextEndCpuTime"),
        )
        self.assertLessEqual(addMultTask.metadata.get("contextEndCpuTime"), currCpuTime)
        self.assertLessEqual(
            addMultTask.add.metadata.get("runStartCpuTime"),
            addMultTask.metadata.get("runEndCpuTime"),
        )
        self.assertLessEqual(addMultTask.add.metadata.get("runEndCpuTime"), currCpuTime)


def suite():
    """Return a suite containing all the test cases in this module.
    """
    utilsTests.init()

    suites = []

    suites += unittest.makeSuite(TaskTestCase)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)

    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    utilsTests.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)