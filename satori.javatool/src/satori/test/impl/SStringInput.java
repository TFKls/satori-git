package satori.test.impl;

import satori.common.SData;
import satori.metadata.SInputMetadata;

public class SStringInput implements SData<String> {
	private final SInputMetadata meta;
	private final STestImpl test;
	
	public SStringInput(SInputMetadata meta, STestImpl test) {
		this.meta = meta;
		this.test = test;
	}
	
	@Override public String get() { return (String)test.getInput(meta); }
	@Override public boolean isEnabled() { return true; }
	@Override public boolean isValid() {
		String data = get();
		return data != null ? meta.getType().isValid(data) : !meta.isRequired();
	}
	@Override public void set(String data) { test.setInput(meta, data); }
}
