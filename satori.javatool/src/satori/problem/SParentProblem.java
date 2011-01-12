package satori.problem;

import satori.common.SIdReader;

public interface SParentProblem extends SIdReader {
	STestList getTestList();
	STestSuiteList getTestSuiteList();
}
