package satori.common;

public class SId {
	private long id;
	
	public SId() { id = -1; }
	public SId(long value) { id = value; }
	public SId(SId other) { id = other.id; }
	
	public boolean isSet() { return id != -1; }
	public long get() { return id; }
	
	public void clear() { id = -1; }
	public void set(long value) { id = value; }
	
	/*@Override public boolean equals(Object arg) {
		if (!(arg instanceof SId)) return false;
		return id == ((SId)arg).id;
	}
	@Override public int hashCode() { return (int)id; }*/
}
