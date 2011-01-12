package satori.test;

import satori.common.ui.SPane;

public interface SRowView extends SPane {
	void addColumn(STestImpl test);
	void addColumn(STestImpl test, int index);
	void removeColumn(int index);
}
