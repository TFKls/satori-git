package satori.attribute;

import satori.blob.SBlob;

public class SBlobAttribute implements SAttribute {
	private SBlob blob;
	
	public SBlobAttribute(SBlob blob) { this.blob = blob; }
	
	public SBlob get() { return blob; }
	
	public boolean equals(SBlobAttribute other) {
		if (other == null) return false;
		if (blob == null) return other.blob == null;
		return blob.equals(other.blob);
	}
	@Override public boolean equals(Object other) {
		if (!(other instanceof SBlobAttribute)) return false;
		return equals((SBlobAttribute)other);
	}
	@Override public int hashCode() {
		if (blob == null) return 0;
		return blob.hashCode();
	}
	
	@Override public boolean isBlob() { return true; }
	@Override public String getString() { return null; }
	@Override public SBlob getBlob() { return blob; }
}
