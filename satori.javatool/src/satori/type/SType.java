package satori.type;

public interface SType {
	boolean isValid(Object arg);
	Object getRaw(Object arg) throws STypeException;
	Object getFormatted(Object arg) throws STypeException;
}
