package satori.problem;

import java.util.List;
import java.util.Map;

import satori.common.SPair;
import satori.metadata.SInputMetadata;
import satori.metadata.SParametersMetadata;
import satori.test.STestBasicReader;

public interface STestSuiteReader extends STestSuiteBasicReader {
	List<? extends STestBasicReader> getTests();
	SParametersMetadata getDispatcher();
	List<SParametersMetadata> getAccumulators();
	SParametersMetadata getReporter();
	Map<SInputMetadata, Object> getGeneralParameters();
	Map<SPair<SInputMetadata, Long>, Object> getTestParameters();
}
