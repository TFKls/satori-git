package satori.type;

import satori.common.SAssert;

public enum STextType implements SType {
	INSTANCE;
	
	@Override public boolean isValid(Object obj) {
		if (obj == null) return true;
		SAssert.assertTrue(obj instanceof String, "Incorrect argument type");
		return true;
	}
}
