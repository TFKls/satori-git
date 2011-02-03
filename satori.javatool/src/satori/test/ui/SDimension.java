package satori.test.ui;

import java.awt.Dimension;

import javax.swing.JComponent;

public class SDimension {
	public static final int height = 20;
	public static final Dimension labelDim = new Dimension(100, height);
	public static final Dimension itemDim = new Dimension(120, height);
	
	public static void setLabelSize(JComponent c) {
		c.setPreferredSize(labelDim);
		c.setMinimumSize(labelDim);
		c.setMaximumSize(labelDim);
	}
	public static void setItemSize(JComponent c) {
		c.setPreferredSize(itemDim);
		c.setMinimumSize(itemDim);
		c.setMaximumSize(itemDim);
	}
	public static void setSize(JComponent c, int width) {
		Dimension dim = new Dimension(width, height);
		c.setPreferredSize(dim);
		c.setMinimumSize(dim);
		c.setMaximumSize(dim);
	}
	public static void setHeight(JComponent c) {
		Dimension dim = c.getPreferredSize();
		dim.height = height;
		c.setPreferredSize(dim);
		c.setMinimumSize(dim);
		c.setMaximumSize(dim);
	}
}
