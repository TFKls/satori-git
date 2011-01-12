package satori.attribute;

import satori.common.SFile;

public interface SAttributeReader {
	Iterable<String> getNames();
	boolean isBlob(String name);
	String getString(String name);
	SFile getBlob(String name);
}
