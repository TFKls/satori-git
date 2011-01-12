package satori.problem;

import satori.test.STestBasicReader;

public interface STestSuiteReader extends STestSuiteBasicReader {
	Iterable<? extends STestBasicReader> getTests();
}
