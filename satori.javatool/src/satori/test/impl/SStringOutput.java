package satori.test.impl;

import satori.common.SOutput;
import satori.metadata.SOutputMetadata;

public class SStringOutput implements SOutput<String> {
	private final SOutputMetadata meta;
	private final STestResult result;
	
	public SStringOutput(SOutputMetadata meta, STestResult result) {
		this.meta = meta;
		this.result = result;
	}
	
	@Override public String get() { return (String)result.getOutput(meta); }
}
