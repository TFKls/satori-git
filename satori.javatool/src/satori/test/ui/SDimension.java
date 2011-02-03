package satori.test.ui;

import java.awt.Dimension;

import javax.swing.JComponent;

public class SDimension {
	public static final int height = 20;
	public static final int labelWidth = 70;
	public static final int itemWidth = 111;
	
	public static final Dimension labelDim = new Dimension(labelWidth, height);
	public static final Dimension itemDim = new Dimension(itemWidth, height);
	public static final int buttonSize = 22;
	public static final Dimension buttonLabelDim = new Dimension(labelWidth, buttonSize);
	public static final Dimension buttonItemDim = new Dimension(itemWidth, buttonSize);
	public static final Dimension buttonDim = new Dimension(buttonSize, buttonSize);
	
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
	public static void setButtonLabelSize(JComponent c) {
		c.setPreferredSize(buttonLabelDim);
		c.setMinimumSize(buttonLabelDim);
		c.setMaximumSize(buttonLabelDim);
	}
	public static void setButtonItemSize(JComponent c) {
		c.setPreferredSize(buttonItemDim);
		c.setMinimumSize(buttonItemDim);
		c.setMaximumSize(buttonItemDim);
	}
	public static void setButtonSize(JComponent c) {
		c.setPreferredSize(buttonDim);
		c.setMinimumSize(buttonDim);
		c.setMaximumSize(buttonDim);
	}
	public static void setButtonHeight(JComponent c) {
		Dimension dim = c.getPreferredSize();
		dim.height = buttonSize;
		c.setPreferredSize(dim);
		c.setMinimumSize(dim);
		c.setMaximumSize(dim);
	}
}
