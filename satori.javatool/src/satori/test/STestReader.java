package satori.test;

import java.util.Map;

import satori.metadata.SInputMetadata;
import satori.metadata.SJudge;

public interface STestReader extends STestBasicReader {
	SJudge getJudge();
	Map<SInputMetadata, Object> getInput();
}
