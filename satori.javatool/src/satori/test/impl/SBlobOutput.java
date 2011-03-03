package satori.test.impl;

import satori.blob.SBlob;
import satori.common.SData;
import satori.metadata.SOutputMetadata;

public class SBlobOutput implements SData<SBlob> {
	private final SOutputMetadata meta;
	private final STestResult result;
	
	public SBlobOutput(SOutputMetadata meta, STestResult result) {
		this.meta = meta;
		this.result = result;
	}
	
	@Override public SBlob get() { return (SBlob)result.getOutput(meta); }
}
