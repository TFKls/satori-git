package satori.common;

import java.util.List;
import java.util.ArrayList;

public class SListener1List<T> {
	private List<SListener1<T>> listeners = new ArrayList<SListener1<T>>();
	
	public void add(SListener1<T> listener) { listeners.add(listener); }
	public void remove(SListener1<T> listener) { listeners.remove(listener); }
	public void call(T source) { for (SListener1<T> listener : listeners) listener.call(source); }
}
