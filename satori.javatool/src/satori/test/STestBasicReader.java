package satori.test;

import satori.common.SIdReader;

public interface STestBasicReader extends SIdReader {
	long getProblemId();
	String getName();
}
