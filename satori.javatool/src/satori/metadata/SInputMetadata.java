package satori.metadata;

import satori.type.SType;

public class SInputMetadata implements SMetadata {
	private final String name;
	private final String desc;
	private final SType type;
	private final boolean required;
	private final Object def_value;
	
	public SInputMetadata(String name, String desc, SType type, boolean required, Object def_value) {
		this.name = name;
		this.desc = desc;
		this.type = type;
		this.required = required;
		this.def_value = def_value;
	}
	
	@Override public String getName() { return name; }
	public String getDescription() { return desc; }
	@Override public SType getType() { return type; }
	public boolean isRequired() { return required; }
	public Object getDefaultValue() { return def_value; }
}
