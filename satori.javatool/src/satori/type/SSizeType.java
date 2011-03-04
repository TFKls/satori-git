package satori.type;

import satori.common.SAssert;

public enum SSizeType implements SType {
	INSTANCE;
	
	private static final long KILO = 1024;
	private static final long MEGA = 1024*1024;
	private static final long GIGA = 1024*1024*1024;
	
	@Override public boolean isValid(Object obj) {
		try { getRaw(obj); }
		catch(STypeException ex) { return false; }
		return true;
	}
	@Override public Object getRaw(Object obj) throws STypeException {
		if (obj == null) return null;
		SAssert.assertTrue(obj instanceof String, "Incorrect argument type");
		String str = (String)obj;
		if (str.endsWith("GB")) {
			long size;
			try { size = Long.valueOf(str.substring(0, str.length()-2))*GIGA; }
			catch(NumberFormatException ex) { throw new STypeException("Invalid format: " + str); }
			if (size <= 0) throw new STypeException("Invalid format: " + str);
			return String.valueOf(size);
		} else if (str.endsWith("MB")) {
			long size;
			try { size = Long.valueOf(str.substring(0, str.length()-2))*MEGA; }
			catch(NumberFormatException ex) { throw new STypeException("Invalid format: " + str); }
			if (size <= 0) throw new STypeException("Invalid format: " + str);
			return String.valueOf(size);
		} else if (str.endsWith("KB")) {
			long size;
			try { size = Long.valueOf(str.substring(0, str.length()-2))*KILO; }
			catch(NumberFormatException ex) { throw new STypeException("Invalid format: " + str); }
			if (size <= 0) throw new STypeException("Invalid format: " + str);
			return String.valueOf(size);
		} else if (str.endsWith("B")) {
			long size;
			try { size = Long.valueOf(str.substring(0, str.length()-1)); }
			catch(NumberFormatException ex) { throw new STypeException("Invalid format: " + str); }
			if (size <= 0) throw new STypeException("Invalid format: " + str);
			return String.valueOf(size);
		} else throw new STypeException("Invalid format: " + str);
	}
	@Override public Object getFormatted(Object obj) throws STypeException {
		if (obj == null) return null;
		SAssert.assertTrue(obj instanceof String, "Incorrect argument type");
		String str = (String)obj;
		long size;
		try { size = Long.valueOf(str); }
		catch(NumberFormatException ex) { throw new STypeException("Invalid attribute data: " + str); }
		if (size <= 0) throw new STypeException("Invalid attribute data: " + str);
		if (size%GIGA == 0) return String.valueOf(size/GIGA) + "GB";
		else if (size%MEGA == 0) return String.valueOf(size/MEGA) + "MB";
		else if (size%KILO == 0) return String.valueOf(size/KILO) + "KB";
		else return String.valueOf(size) + "B";
	}
}
