package satori.problem;

import satori.common.SIdReader;

public interface STestSuiteBasicReader extends SIdReader {
	long getProblemId();
	String getName();
	String getDescription();
}
