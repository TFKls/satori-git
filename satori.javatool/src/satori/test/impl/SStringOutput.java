package satori.test.impl;

import satori.common.SData;
import satori.metadata.SOutputMetadata;

public class SStringOutput implements SData<String> {
	private final SOutputMetadata meta;
	private final STestResult result;
	
	public SStringOutput(SOutputMetadata meta, STestResult result) {
		this.meta = meta;
		this.result = result;
	}
	
	@Override public String get() { return (String)result.getOutput(meta); }
	@Override public String getDescription() { return meta.getDescription(); }
}
