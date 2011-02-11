package satori.test.ui;

import satori.common.ui.SPane;
import satori.test.impl.STestResult;

public interface SSolutionRow extends SPane {
	void addColumn(STestResult result, int index);
	void removeColumn(int index);
}
