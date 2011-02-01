package satori.attribute;

import satori.blob.SBlob;

public interface SAttributeSaver {
	void saveString(String name, String value);
	void saveFile(String name, SBlob blob);
}
