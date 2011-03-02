package satori.test.impl;

import satori.blob.SBlob;
import satori.common.SOutput;
import satori.metadata.SOutputMetadata;

public class SBlobOutput implements SOutput<SBlob> {
	private final SOutputMetadata meta;
	private final STestResult result;
	
	public SBlobOutput(SOutputMetadata meta, STestResult result) {
		this.meta = meta;
		this.result = result;
	}
	
	@Override public SBlob get() { return (SBlob)result.getOutput(meta); }
}
