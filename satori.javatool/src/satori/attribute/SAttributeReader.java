package satori.attribute;

import satori.blob.SBlob;

public interface SAttributeReader {
	Iterable<String> getNames();
	boolean isBlob(String name);
	String getString(String name);
	SBlob getBlob(String name);
}
