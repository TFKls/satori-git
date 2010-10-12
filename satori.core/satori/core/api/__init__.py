# vim:ts=4:sts=4:sw=4:expandtab

from satori.ars import wrapper
from satori.core import cwrapper

import ApiBlob
import ApiContestant
import ApiContest
import ApiContestRanking
import ApiGlobal
import ApiJudge
import ApiLogin
import ApiMachine
import ApiMessageContest
import ApiMessageGlobal
import ApiMessage
import ApiEntity
import ApiOpenIdentity
import ApiPrivilege
import ApiProblemMapping
import ApiProblem
import ApiProblemResult
import ApiRoleMapping
import ApiRole
import ApiSecurity
import ApiSubmit
import ApiSubpage
import ApiTestMapping
import ApiTest
import ApiTestResult
import ApiTestSuite
import ApiTestSuiteResult
import ApiUser

wrapper.register_middleware(cwrapper.TransactionMiddleware())

wrapper.register_middleware(cwrapper.TokenVerifyMiddleware())
wrapper.global_throws(cwrapper.TokenInvalid)
wrapper.global_throws(cwrapper.TokenExpired)

wrapper.register_middleware(wrapper.TypeConversionMiddleware())

wrapper.register_middleware(cwrapper.CheckRightsMiddleware())

ars_interface = wrapper.generate_interface()

