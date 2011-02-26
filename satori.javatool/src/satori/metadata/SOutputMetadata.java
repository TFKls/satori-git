package satori.metadata;

import satori.type.SType;

public class SOutputMetadata implements SMetadata {
	private final String name;
	private final String desc;
	private final SType type;
	
	public SOutputMetadata(String name, String desc, SType type) {
		this.name = name;
		this.desc = desc;
		this.type = type;
	}
	
	@Override public String getName() { return name; }
	public String getDescription() { return desc; }
	@Override public SType getType() { return type; }
}
