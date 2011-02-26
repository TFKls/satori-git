package satori.type;

import satori.common.SException;

public interface SType {
	boolean matchType(Object arg);
	boolean isValid(Object arg);
	Object getRaw(Object arg) throws SException;
	Object getFormatted(Object arg) throws SException;
}
