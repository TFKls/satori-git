package satori.attribute;

import satori.blob.SBlob;

public class SStringAttribute implements SAttribute {
	private String value;
	
	public SStringAttribute(String value) { this.value = value; }
	
	public String get() { return value; }
	
	public boolean equals(SStringAttribute other) {
		if (value == null) return other.value == null;
		return value.equals(other.value);
	}
	@Override public boolean equals(Object other) {
		if (!(other instanceof SStringAttribute)) return false;
		return equals((SStringAttribute)other);
	}
	@Override public int hashCode() {
		if (value == null) return 0;
		return value.hashCode();
	}
	
	@Override public boolean isBlob() { return false; }
	@Override public String getString() { return value; }
	@Override public SBlob getBlob() { return null; }
}
