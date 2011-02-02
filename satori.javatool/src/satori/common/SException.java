package satori.common;

@SuppressWarnings("serial")
public class SException extends Exception {
	public SException(String msg) { super(msg); }
	public SException(Exception ex) { super(ex); }
}
