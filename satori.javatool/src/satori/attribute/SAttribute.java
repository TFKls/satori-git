package satori.attribute;

import satori.common.SFile;

public interface SAttribute {
	boolean isBlob();
	String getString();
	SFile getBlob();
	boolean check(SAttributeReader source, String name);
}
