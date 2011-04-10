package satori.common;

public class SId {
	private final static SId unsetId = new SId();
	
	private long id;
	
	public SId(long value) { id = value; }
	private SId() { id = -1; }
	
	public static SId unset() { return unsetId; }
	
	public boolean isSet() { return id != -1; }
	public long get() { return id; }
	
	@Override public boolean equals(Object other) {
		if (!(other instanceof SId)) return false;
		return id == ((SId)other).id;
	}
	@Override public int hashCode() { return (int)id; }
}
