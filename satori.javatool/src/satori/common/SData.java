package satori.common;

public interface SData<T> {
	T get();
	void set(T data);
	boolean isEnabled();
	boolean isValid();
}
