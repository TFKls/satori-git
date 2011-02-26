package satori.type;

import satori.common.SAssert;

public enum STextType implements SType {
	INSTANCE;
	
	@Override public boolean isValid(Object obj) {
		SAssert.assertTrue(obj instanceof String, "Incorrect argument type");
		return true;
	}
	@Override public Object getRaw(Object obj) {
		SAssert.assertTrue(obj instanceof String, "Incorrect argument type");
		return obj;
	}
	@Override public Object getFormatted(Object obj) {
		SAssert.assertTrue(obj instanceof String, "Incorrect argument type");
		return obj;
	}
}
