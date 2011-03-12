package satori.type;

import satori.common.SAssert;

public enum SBoolType implements SType {
	INSTANCE;
	
	@Override public boolean isValid(Object obj) {
		if (obj == null) return true;
		SAssert.assertTrue(obj instanceof String, "Incorrect argument type");
		String str = (String)obj;
		return str.equals("true") || str.equals("false");
	}
}
