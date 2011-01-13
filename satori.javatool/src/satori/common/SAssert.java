package satori.common;

public class SAssert {
	public static void assertTrue(boolean cond, String message) {
		if (!cond) throw new SAssertException(message);
	}
	public static void assertFalse(boolean cond, String message) {
		if (cond) throw new SAssertException(message);
	}
	public static void assertEquals(Object arg1, Object arg2, String message) {
		if (!arg1.equals(arg2)) throw new SAssertException(message);
	}
	public static void assertNull(Object ref, String message) {
		if (ref != null) throw new SAssertException(message);
	}
	public static void assertNotNull(Object ref, String message) {
		if (ref == null) throw new SAssertException(message);
	}
}
