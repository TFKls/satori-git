package satori.problem;

import java.util.List;

import satori.common.SPair;
import satori.test.STestBasicReader;

public interface STestSuiteReader extends STestSuiteBasicReader {
	List<? extends STestBasicReader> getTests();
	List<SPair<String, String>> getDispatchers();
	List<SPair<String, String>> getAccumulators();
	List<SPair<String, String>> getReporters();
}
