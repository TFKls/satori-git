package satori.problem;

import java.util.List;

import satori.test.STestBasicReader;

public interface STestSuiteReader extends STestSuiteBasicReader {
	List<? extends STestBasicReader> getTests();
}
