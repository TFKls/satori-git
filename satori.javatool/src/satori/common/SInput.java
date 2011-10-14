package satori.common;

import satori.task.STaskException;
import satori.task.STaskHandler;

public interface SInput<T> extends SData<T> {
	boolean isValid();
	void set(STaskHandler handler, T data) throws STaskException;
}
