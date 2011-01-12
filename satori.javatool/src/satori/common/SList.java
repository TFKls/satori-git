package satori.common;

public interface SList<T> {
	void add(T elem);
	void add(Iterable<T> elems);
	void remove(T elem);
	void removeAll();
}
