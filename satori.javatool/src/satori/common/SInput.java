package satori.common;

public interface SInput<T> extends SData<T> {
	boolean isValid();
	void set(T data) throws SException;
}
