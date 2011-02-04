package satori.common;

public interface SData<T> {
	T get();
	void set(T data) throws SException;
	boolean isEnabled();
	boolean isValid();
}
