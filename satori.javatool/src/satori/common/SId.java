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
}
