package satori.test.ui;

import satori.common.ui.SPane;
import satori.test.impl.STestImpl;

public interface SRowView extends SPane {
	void addColumn(STestImpl test, int index);
	void removeColumn(int index);
}
