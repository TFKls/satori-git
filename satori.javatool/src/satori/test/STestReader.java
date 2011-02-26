package satori.test;

import java.util.List;
import java.util.Map;

import satori.blob.SBlob;
import satori.metadata.SInputMetadata;
import satori.metadata.SOutputMetadata;

public interface STestReader extends STestBasicReader {
	SBlob getJudge();
	List<SInputMetadata> getInputMetadata();
	List<SOutputMetadata> getOutputMetadata();
	Map<SInputMetadata, Object> getInput();
}
