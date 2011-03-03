package satori.test.impl;

import satori.blob.SBlob;
import satori.common.SInput;
import satori.metadata.SInputMetadata;

public class SBlobInput implements SInput<SBlob> {
	private final SInputMetadata meta;
	private final STestImpl test;
	
	public SBlobInput(SInputMetadata meta, STestImpl test) {
		this.meta = meta;
		this.test = test;
	}
	
	@Override public SBlob get() { return (SBlob)test.getInput(meta); }
	@Override public boolean isValid() {
		SBlob data = get();
		return data != null ? meta.getType().isValid(data) : !meta.isRequired();
	}
	@Override public void set(SBlob data) { test.setInput(meta, data); }
}
