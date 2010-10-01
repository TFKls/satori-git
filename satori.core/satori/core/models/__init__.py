# vim:ts=4:sts=4:sw=4:expandtab
"""Database schema for satori.core.
"""

from satori.core.models._Association import Association
from satori.core.models._AttributeGroup import AttributeGroup
from satori.core.models._Blob import Blob
from satori.core.models._Contestant import Contestant
from satori.core.models._Contest import Contest
from satori.core.models._ContestRanking import ContestRanking
from satori.core.models._Global import Global
from satori.core.models._Login import Login
from satori.core.models._Machine import Machine
from satori.core.models._Message import Message
from satori.core.models._MessageGlobal import MessageGlobal
from satori.core.models._MessageContest import MessageContest
from satori.core.models._Nonce import Nonce
from satori.core.models._Entity import Entity
from satori.core.models._OpenAttribute import OpenAttribute
from satori.core.models._OpenIdentity import OpenIdentity
from satori.core.models._Privilege import Privilege
from satori.core.models._ProblemMapping import ProblemMapping
from satori.core.models._Problem import Problem
from satori.core.models._ProblemResult import ProblemResult
from satori.core.models._Role import Role
from satori.core.models._RoleMapping import RoleMapping
from satori.core.models._Session import Session
from satori.core.models._Subpage import Subpage
from satori.core.models._Submit import Submit
from satori.core.models._Test import Test
from satori.core.models._TestMapping import TestMapping
from satori.core.models._TestResult import TestResult
from satori.core.models._TestSuite import TestSuite
from satori.core.models._TestSuiteResult import TestSuiteResult
from satori.core.models._User import User

import satori.core.management
