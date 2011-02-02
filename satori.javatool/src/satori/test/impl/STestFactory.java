package satori.test.impl;

import satori.common.SException;
import satori.test.STestSnap;

public interface STestFactory {
	STestImpl create(STestSnap snap) throws SException;
	STestImpl createNew();
}
