package satori.attribute;

import java.util.Map;
import java.util.Set;

import satori.blob.SBlob;

public interface SAttributeReader {
	Set<String> getNames();
	boolean isBlob(String name);
	String getString(String name);
	SBlob getBlob(String name);
	Map<String, ? extends SAttribute> getMap();
}
