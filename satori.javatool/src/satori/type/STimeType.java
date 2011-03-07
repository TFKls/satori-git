package satori.type;

import satori.common.SAssert;

public enum STimeType implements SType {
	INSTANCE;
	
	@Override public boolean isValid(Object obj) {
		if (obj == null) return true;
		SAssert.assertTrue(obj instanceof String, "Incorrect argument type");
		String str = (String)obj;
		if (str.endsWith("s")) {
			double time;
			try { time = Double.valueOf(str.substring(0, str.length()-1))*1000.0; }
			catch(NumberFormatException ex) { return false; }
			long rnd_time = Math.round(time);
			if (rnd_time != time) return false;
			if (rnd_time <= 0) return false;
		} else return false;
		return true;
	}
}
