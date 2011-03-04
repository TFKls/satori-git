package satori.common.ui;

import java.awt.Component;
import java.awt.Container;
import java.awt.Dimension;
import java.awt.LayoutManager;

public abstract class SLayoutManagerAdapter implements LayoutManager {
	@Override public void addLayoutComponent(String name, Component comp) {}
	@Override public void removeLayoutComponent(Component comp) {}
	@Override public Dimension preferredLayoutSize(Container parent) { return new Dimension(); }
	@Override public Dimension minimumLayoutSize(Container parent) { return new Dimension(); }
}
