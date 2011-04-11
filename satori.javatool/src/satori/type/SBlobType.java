package satori.type;

import satori.common.SAssert;
import satori.data.SBlob;

public enum SBlobType implements SType {
	INSTANCE;
	
	@Override public boolean isValid(Object obj) {
		if (obj == null) return true;
		SAssert.assertTrue(obj instanceof SBlob, "Incorrect argument type");
		return true;
	}
}
