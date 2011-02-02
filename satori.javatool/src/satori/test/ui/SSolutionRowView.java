package satori.test.ui;

import satori.common.ui.SPane;
import satori.test.impl.STestResult;

public interface SSolutionRowView extends SPane {
	void addColumn(STestResult result, int index);
	void removeColumn(int index);
}
