package satori.problem;

import java.util.List;

import satori.metadata.SParameters;
import satori.test.STestBasicReader;

public interface STestSuiteReader extends STestSuiteBasicReader {
	List<? extends STestBasicReader> getTests();
	SParameters getDispatcher();
	List<SParameters> getAccumulators();
	SParameters getReporter();
}
