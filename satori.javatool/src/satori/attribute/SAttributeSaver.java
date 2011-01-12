package satori.attribute;

import satori.common.SFile;

public interface SAttributeSaver {
	void saveString(String name, String value);
	void saveFile(String name, SFile file);
}
