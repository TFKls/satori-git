package satori.common.ui;

import satori.common.SView;

public interface STabs {
	interface TabModel { String getTitle(); }
	
	void openPane(String title, STabPane pane);
	SView openPane(TabModel model, STabPane pane);
	void closePane(STabPane pane);
}
