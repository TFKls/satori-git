package satori.attribute;

import satori.blob.SBlob;

public class SBlobAttribute implements SAttribute {
	private SBlob blob;
	
	public SBlobAttribute(SBlob blob) { this.blob = blob; }
	
	public SBlob get() { return blob; }
	public void set(SBlob blob) { this.blob = blob; }
	
	/*@Override public boolean equals(Object arg) {
		if (!(arg instanceof SFileAttribute)) return false;
		SFile arg_blob = ((SFileAttribute)arg).blob;
		if (blob == null) return arg_blob == null;
		else return blob.equals(arg_blob);
	}
	@Override public int hashCode() {
		if (blob == null) return 0;
		return blob.hashCode();
	}*/
	
	@Override public boolean isBlob() { return true; }
	@Override public String getString() { return null; }
	@Override public SBlob getBlob() { return blob; }
	
	@Override public boolean check(SAttributeReader source, String name) {
		SBlob other = source.getBlob(name);
		if (other == null) return true;
		return blob.check(other);
	}
}
