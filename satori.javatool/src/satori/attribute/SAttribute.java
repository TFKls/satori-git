package satori.attribute;

import satori.blob.SBlob;

public interface SAttribute {
	boolean isBlob();
	String getString();
	SBlob getBlob();
	
	SAttribute copy();
	
	boolean check(SAttributeReader source, String name);
}
