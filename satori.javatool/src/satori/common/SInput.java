package satori.common;

import satori.task.STaskException;

public interface SInput<T> extends SData<T> {
	boolean isValid();
	void set(T data) throws STaskException;
}
