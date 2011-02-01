package satori.test;

import satori.common.ui.SPane;

public interface SSolutionRowView extends SPane {
	void addColumn(STestResult result, int index);
	void removeColumn(int index);
}
