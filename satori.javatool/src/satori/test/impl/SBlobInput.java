package satori.test.impl;

import satori.blob.SBlob;
import satori.common.SData;
import satori.metadata.SInputMetadata;

public class SBlobInput implements SData<SBlob> {
	private final SInputMetadata meta;
	private final STestImpl test;
	
	public SBlobInput(SInputMetadata meta, STestImpl test) {
		this.meta = meta;
		this.test = test;
	}
	
	@Override public SBlob get() { return (SBlob)test.getInput(meta); }
	@Override public boolean isEnabled() { return true; }
	@Override public boolean isValid() {
		SBlob data = get();
		return data != null ? meta.getType().isValid(data) : !meta.isRequired();
	}
	@Override public void set(SBlob data) { test.setInput(meta, data); }
}
