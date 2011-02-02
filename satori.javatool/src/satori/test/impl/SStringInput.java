package satori.test.impl;

import satori.common.SData;
import satori.test.meta.SInputMetadata;

public class SStringInput implements SData<String> {
	public static enum Status { VALID, INVALID, DISABLED };
	
	private final SInputMetadata meta;
	private final STestImpl test;
	
	public SStringInput(SInputMetadata meta, STestImpl test) {
		this.meta = meta;
		this.test = test;
	}
	
	@Override public String get() { return test.getData().getString(meta.getName()); }
	@Override public void set(String data) { test.setDataString(meta.getName(), data); }
	
	public Status getStatus() {
		if (meta.isRequired() && get() == null) return Status.INVALID;
		else return Status.VALID;
	}
	
	@Override public boolean isEnabled() { return getStatus() != Status.DISABLED; }
	@Override public boolean isValid() { return getStatus() == Status.VALID; }
}
