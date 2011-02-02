package satori.test.impl;

import satori.blob.SBlob;
import satori.common.SData;
import satori.test.meta.SInputMetadata;

public class SBlobInput implements SData<SBlob> {
	public static enum Status { VALID, INVALID, DISABLED };
	
	private final SInputMetadata meta;
	private final STestImpl test;
	
	public SBlobInput(SInputMetadata meta, STestImpl test) {
		this.meta = meta;
		this.test = test;
	}
	
	@Override public SBlob get() { return test.getData().getBlob(meta.getName()); }
	@Override public void set(SBlob data) { test.setDataBlob(meta.getName(), data); }
	
	public Status getStatus() {
		if (meta.isRequired() && get() == null) return Status.INVALID;
		else return Status.VALID;
	}
	
	@Override public boolean isEnabled() { return getStatus() != Status.DISABLED; }
	@Override public boolean isValid() { return getStatus() == Status.VALID; }
}
