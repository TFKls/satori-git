package satori.test.ui;

import satori.common.ui.SPane;
import satori.test.impl.STestImpl;

public interface SRow extends SPane {
	void addColumn(STestImpl test, int index);
	void removeColumn(int index);
}
