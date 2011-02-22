package satori.test.impl;

import satori.blob.SBlob;
import satori.common.SData;
import satori.test.meta.SInputMetadata;

public class SBlobInput implements SData<SBlob> {
	private final SInputMetadata meta;
	private final STestImpl test;
	private SBlob data;
	private boolean valid;
	
	public SBlobInput(SInputMetadata meta, STestImpl test) {
		this.meta = meta;
		this.test = test;
		set(meta.getDefaultValue() != null ? meta.getDefaultValue().getBlob() : null);
	}
	
	@Override public SBlob get() { return data; }
	@Override public boolean isEnabled() { return true; }
	@Override public boolean isValid() { return valid; }
	@Override public void update() {
		data = test.getData().getBlob(meta.getName());
		valid = data != null || !meta.isRequired();
	}
	@Override public void set(SBlob data) {
		this.data = data;
		valid = data != null || !meta.isRequired();
		test.setDataBlob(meta.getName(), valid ? data : null);
	}
}
