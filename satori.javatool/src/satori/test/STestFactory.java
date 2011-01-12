package satori.test;

import satori.common.SException;

public interface STestFactory {
	STestImpl create(STestSnap snap) throws SException;
	STestImpl createNew();
}
