package satori.type;

import satori.common.SAssert;

public enum SSizeType implements SType {
	INSTANCE;
	
	private static final long KILO = 1024;
	private static final long MEGA = 1024*1024;
	private static final long GIGA = 1024*1024*1024;
	
	@Override public boolean isValid(Object obj) {
		if (obj == null) return true;
		SAssert.assertTrue(obj instanceof String, "Incorrect argument type");
		String str = (String)obj;
		long size;
		if (str.endsWith("GB")) {
			try { size = Long.valueOf(str.substring(0, str.length()-2))*GIGA; }
			catch(NumberFormatException ex) { return false; }
		} else if (str.endsWith("MB")) {
			try { size = Long.valueOf(str.substring(0, str.length()-2))*MEGA; }
			catch(NumberFormatException ex) { return false; }
		} else if (str.endsWith("KB")) {
			try { size = Long.valueOf(str.substring(0, str.length()-2))*KILO; }
			catch(NumberFormatException ex) { return false; }
		} else if (str.endsWith("B")) {
			try { size = Long.valueOf(str.substring(0, str.length()-1)); }
			catch(NumberFormatException ex) { return false; }
		} else return false;
		return size > 0;
	}
}
