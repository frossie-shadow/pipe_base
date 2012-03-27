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
import os
import unittest

import eups
import lsst.utils.tests as utilsTests
import lsst.pex.config as pexConfig
import lsst.pex.logging as pexLog
import lsst.pipe.base as pipeBase

ObsTestDir = eups.productDir("obs_test")
if not ObsTestDir:
    print "Warning: you must setup obs_test to run these tests"
else:
    DataPath = os.path.join(ObsTestDir, "tests/data/input")
LocalDataPath = os.path.join(eups.productDir("pipe_base"), "tests/data")

class TestConfig(pexConfig.Config):
    f = pexConfig.Field(doc="test field", dtype=float, default=3.1)

class TestTask(pipeBase.CmdLineTask):
    ConfigClass = TestConfig
    _DefaultName = "processCcd"
    def __init__(self, *args, **kwargs):
        pipeBase.CmdLineTask.__init__(self, *args, **kwargs)
        self.idList = []

    def run(self, sensorRef):
        self.idList.append(sensorRef.dataId)
        
class CmdLineTaskTestCase(unittest.TestCase):
    """A test case for CmdLineTask
    """
    def setUp(self):
        os.environ.pop("PIPE_INPUT_ROOT", None)
        os.environ.pop("PIPE_CALIB_ROOT", None)
        os.environ.pop("PIPE_OUTPUT_ROOT", None)

    def testBasics(self):
        """Test basic construction and use of a command-line task
        """
        retVal = TestTask.parseAndRun(args=["test", DataPath, "--output", LocalDataPath, 
            "--id", "raft=0,3", "sensor=1,1", "visit=85470982"])
        task = retVal.task
        self.assertEqual(len(task.idList), 1)
        dataId = task.idList[0]
        self.assertEqual(dataId["raft"], "0,3")
        self.assertEqual(dataId["sensor"], "1,1")
        self.assertEqual(dataId["visit"], 85470982)
    
    def testOverrides(self):
        """Test config and log override
        """
        config = TestTask.ConfigClass()
        config.f = -99.9
        defLog = pexLog.getDefaultLog()
        log = pexLog.Log(defLog, "newname")
        retVal = TestTask.parseAndRun(
            args=["test", DataPath, "--output", LocalDataPath, 
                "--id", "raft=0,3", "sensor=1,1", "visit=85470982"],
            config = config,
            log = log
        )
        self.assertEquals(retVal.task.config.f, -99.9)
        self.assertTrue(retVal.parsedCmd.log is log)

def suite():
    """Return a suite containing all the test cases in this module.
    """
    utilsTests.init()

    suites = []

    suites += unittest.makeSuite(CmdLineTaskTestCase)
    suites += unittest.makeSuite(utilsTests.MemoryTestCase)

    return unittest.TestSuite(suites)


def run(shouldExit=False):
    """Run the tests"""
    if ObsTestDir is None:
        return
    utilsTests.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)