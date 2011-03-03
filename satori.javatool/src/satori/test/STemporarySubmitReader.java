package satori.test;

import java.util.Map;

import satori.metadata.SOutputMetadata;

public interface STemporarySubmitReader {
	boolean getPending();
	Map<SOutputMetadata, Object> getResult();
}
