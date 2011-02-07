package satori.common.ui;

import java.util.ArrayList;
import java.util.List;

import javax.swing.JComponent;
import javax.swing.JTabbedPane;

import satori.common.SView;
import satori.common.SViewList;

public class STabbedPane implements SPane, STabs {
	private final List<STabPane> panes = new ArrayList<STabPane>();
	private final SViewList parent_views = new SViewList();
	private final JTabbedPane tabs = new JTabbedPane();
	
	@Override public JComponent getPane() { return tabs; }
	
	public boolean hasUnsavedData() {
		for (STabPane pane : panes) if (pane.hasUnsavedData()) return true;
		return false;
	}
	
	@Override public void openPane(String title, STabPane pane) {
		panes.add(pane);
		parent_views.update();
		tabs.addTab(title, pane.getPane());
		tabs.setSelectedComponent(pane.getPane());
	}
	
	private class TabView implements SView {
		private final TabModel model;
		private final STabPane pane;
		public TabView(TabModel model, STabPane pane) {
			this.model = model;
			this.pane = pane;
		}
		@Override public void update() {
			String title = model.getTitle();
			if (pane.hasUnsavedData()) title += "*";
			tabs.setTitleAt(tabs.indexOfComponent(pane.getPane()), title);
			parent_views.update();
		}
	}
	@Override public SView openPane(TabModel model, STabPane pane) {
		openPane(model.getTitle(), pane);
		return new TabView(model, pane);
	}
	
	@Override public void closePane(STabPane pane) {
		tabs.remove(pane.getPane());
		panes.remove(pane);
		parent_views.update();
	}
	
	public void addParentView(SView view) { parent_views.add(view); }
	public void removeParentView(SView view) { parent_views.remove(view); }
}
