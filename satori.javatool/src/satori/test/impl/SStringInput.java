package satori.test.impl;

import satori.common.SData;
import satori.test.meta.SConverter;
import satori.test.meta.SInputMetadata;

public class SStringInput implements SData<String> {
	private final SInputMetadata meta;
	private final STestImpl test;
	private final SConverter converter;
	private String data;
	private boolean valid;
	
	public SStringInput(SInputMetadata meta, STestImpl test) {
		this.meta = meta;
		this.test = test;
		this.converter = meta.getConverter();
		set(meta.getDefaultValue() != null ? meta.getDefaultValue().getString() : null);
	}
	
	@Override public String get() { return data; }
	@Override public boolean isEnabled() { return true; }
	@Override public boolean isValid() { return valid; }
	@Override public void update() {
		data = test.getData().getString(meta.getName());
		if (data != null) {
			if (converter != null) data = converter.encode(data);
			valid = data != null;
			if (data == null) data = "?";
		}
		else valid = !meta.isRequired();
	}
	@Override public void set(String data) {
		this.data = data;
		if (data != null) {
			if (converter != null) data = converter.decode(data);
			valid = data != null;
		}
		else valid = !meta.isRequired();
		test.setDataString(meta.getName(), valid ? data : null);
	}
}
