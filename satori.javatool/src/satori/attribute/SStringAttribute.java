package satori.attribute;

import satori.blob.SBlob;

public class SStringAttribute implements SAttribute {
	private String value = null;
	
	public SStringAttribute(String value) { this.value = value; }
	
	public String get() { return value; }
	public void set(String value) { this.value = value; }
	
	/*@Override public boolean equals(Object arg) {
		if (!(arg instanceof SStringAttribute)) return false;
		String arg_value = ((SStringAttribute)arg).value;
		if (arg_value == null) return value == null;
		else return arg_value.equals(value);
	}
	@Override public int hashCode() {
		if (value == null) return 0;
		return value.hashCode();
	}*/
	
	@Override public boolean isBlob() { return false; }
	@Override public String getString() { return value; }
	@Override public SBlob getBlob() { return null; }
	
	@Override public boolean check(SAttributeReader source, String name) {
		String other = source.getString(name);
		if (other == null) return true;
		return !value.equals(other);
	}
}
