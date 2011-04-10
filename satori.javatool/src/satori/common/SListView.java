package satori.common;

public interface SListView<T> {
	void add(T item);
	void add(Iterable<T> items);
	void remove(T item);
	void removeAll();
}
