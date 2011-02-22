package satori.test.meta;

import satori.attribute.SAttribute;

public class SInputMetadata {
	private final String name;
	private final String desc;
	private final boolean is_blob;
	private final boolean required;
	private final SAttribute def_value;
	private final SConverter converter;
	
	public String getName() { return name; }
	public String getDescription() { return desc; }
	public boolean isBlob() { return is_blob; }
	public boolean isRequired() { return required; }
	public SAttribute getDefaultValue() { return def_value != null ? def_value : null; }
	public SConverter getConverter() { return converter; }
	
	public SInputMetadata(String name, String desc, boolean is_blob, boolean required, SAttribute def_value, SConverter converter) {
		this.name = name;
		this.desc = desc;
		this.is_blob = is_blob;
		this.required = required;
		this.def_value = def_value;
		this.converter = converter;
	}
}
