package satori.test.impl;

import satori.task.STaskException;
import satori.test.STestSnap;

public interface STestFactory {
	STestImpl create(STestSnap snap) throws STaskException;
	STestImpl createNew();
}
