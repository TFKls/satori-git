package satori.common.ui;

import javax.swing.JComponent;
import javax.swing.JTabbedPane;

import satori.common.SView;

public class STabbedPane implements SPane, STabs {
	private JTabbedPane tabs;
	
	public STabbedPane() { initialize(); }
	
	@Override public JComponent getPane() { return tabs; }
	
	@Override public void openPane(String title, SPane pane) {
		tabs.addTab(title, pane.getPane());
		tabs.setSelectedComponent(pane.getPane());
	}
	
	private class TabView implements SView {
		private final TabModel model;
		private final SPane pane;
		TabView(TabModel model, SPane pane) { this.model = model; this.pane = pane; }
		@Override public void update() { tabs.setTitleAt(tabs.indexOfComponent(pane.getPane()), model.getTitle()); }
	}
	@Override public SView openPane(TabModel model, SPane pane) {
		openPane(model.getTitle(), pane);
		return new TabView(model, pane);
	}
	
	@Override public void closePane(SPane pane) { tabs.remove(pane.getPane()); }
	
	private void initialize() { tabs = new JTabbedPane(); }
}
