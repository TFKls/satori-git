package satori.type;

import satori.blob.SBlob;
import satori.common.SAssert;

public enum SBlobType implements SType {
	INSTANCE;
	
	@Override public boolean isValid(Object obj) {
		if (obj == null) return true;
		SAssert.assertTrue(obj instanceof SBlob, "Incorrect argument type");
		return true;
	}
}
