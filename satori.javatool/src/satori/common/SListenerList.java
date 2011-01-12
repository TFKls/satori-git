package satori.common;

import java.util.List;
import java.util.ArrayList;

public class SListenerList<T> {
	private List<SListener<T>> listeners = new ArrayList<SListener<T>>();
	
	public void add(SListener<T> listener) { listeners.add(listener); }
	public void remove(SListener<T> listener) { listeners.remove(listener); }
	public void call(T source) { for (SListener<T> listener : listeners) listener.call(source); }
}
