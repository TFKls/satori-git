package satori.type;

import satori.common.SAssert;

public enum STimeType implements SType {
	INSTANCE;
	
	@Override public boolean isValid(Object obj) {
		try { getRaw(obj); }
		catch(STypeException ex) { return false; }
		return true;
	}
	@Override public Object getRaw(Object obj) throws STypeException {
		if (obj == null) return null;
		SAssert.assertTrue(obj instanceof String, "Incorrect argument type");
		String str = (String)obj;
		if (str.endsWith("s")) {
			double time;
			try { time = Double.valueOf(str.substring(0, str.length()-1))*1000.0; }
			catch(NumberFormatException ex) { throw new STypeException("Invalid format: " + str); }
			long rnd_time = Math.round(time);
			if (rnd_time != time) throw new STypeException("Invalid format: " + str);
			if (rnd_time <= 0) throw new STypeException("Invalid format: " + str);
			return String.valueOf(rnd_time);
		} else throw new STypeException("Invalid format: " + str);
	}
	@Override public Object getFormatted(Object obj) throws STypeException {
		if (obj == null) return null;
		SAssert.assertTrue(obj instanceof String, "Incorrect argument type");
		String str = (String)obj;
		long time;
		try { time = Long.valueOf(str); }
		catch(NumberFormatException ex) { throw new STypeException("Invalid attribute data: " + str); }
		if (time <= 0) throw new STypeException("Invalid attribute data: " + str);
		return String.valueOf(time*0.001) + "s";
	}
}
