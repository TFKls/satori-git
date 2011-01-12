package satori.attribute;

import satori.common.SFile;

public class SFileAttribute implements SAttribute {
	private SFile file;
	
	public SFileAttribute(SFile file) { this.file = file; }
	
	public SFile get() { return file; }
	public void set(SFile file) { this.file = file; }
	
	/*@Override public boolean equals(Object arg) {
		if (!(arg instanceof SFileAttribute)) return false;
		SFile arg_file = ((SFileAttribute)arg).file;
		if (file == null) return arg_file == null;
		else return file.equals(arg_file);
	}
	@Override public int hashCode() {
		if (file == null) return 0;
		return file.hashCode();
	}*/
	
	@Override public boolean isBlob() { return true; }
	@Override public String getString() { return null; }
	@Override public SFile getBlob() { return file; }
	
	@Override public boolean check(SAttributeReader source, String name) {
		SFile other = source.getBlob(name);
		if (other == null) return true;
		return file.check(other);
	}
}
