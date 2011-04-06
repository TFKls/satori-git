package satori.task;

import satori.common.SException;

@SuppressWarnings("serial")
public class STaskException extends SException {
	public STaskException() { super("Task failed"); }
}
