package satori.common.ui;

import satori.common.SView;

public interface STabs {
	static interface TabModel { String getTitle(); }
	
	void openPane(String title, SPane pane);
	SView openPane(TabModel model, SPane pane);
	void closePane(SPane pane);
}
