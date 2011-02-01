package satori.test;

import satori.attribute.SAttributeReader;

public interface STemporarySubmitReader {
	boolean getPending();
	SAttributeReader getResult();
}
