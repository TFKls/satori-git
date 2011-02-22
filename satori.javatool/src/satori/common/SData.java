package satori.common;

public interface SData<T> {
	T get();
	boolean isEnabled();
	boolean isValid();
	void update();
	void set(T data) throws SException;
}
