package satori.common.ui;

import java.awt.Component;
import java.awt.Container;
import java.awt.Dimension;
import java.awt.LayoutManager2;

public abstract class SLayoutManagerAdapter implements LayoutManager2 {
	@Override public void addLayoutComponent(String name, Component comp) {}
	@Override public void addLayoutComponent(Component comp, Object contraints) {}
	@Override public void removeLayoutComponent(Component comp) {}
	@Override public Dimension preferredLayoutSize(Container parent) { return new Dimension(); }
	@Override public Dimension minimumLayoutSize(Container parent) { return new Dimension(); }
	@Override public Dimension maximumLayoutSize(Container parent) { return new Dimension(Short.MAX_VALUE, Short.MAX_VALUE); }
	@Override public float getLayoutAlignmentX(Container target) { return 0.5f; }
	@Override public float getLayoutAlignmentY(Container target) { return 0.5f; }
	@Override public void invalidateLayout(Container target) {}
}
