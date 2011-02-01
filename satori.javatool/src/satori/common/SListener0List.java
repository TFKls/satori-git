package satori.common;

import java.util.ArrayList;
import java.util.List;

public class SListener0List {
	private List<SListener0> listeners = new ArrayList<SListener0>();
	
	public void add(SListener0 listener) { listeners.add(listener); }
	public void remove(SListener0 listener) { listeners.remove(listener); }
	public void call() { for (SListener0 listener : listeners) listener.call(); }
}
