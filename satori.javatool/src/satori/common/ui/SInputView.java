package satori.common.ui;

import java.awt.Dimension;

import satori.common.SView;

public interface SInputView extends SPane, SView {
	void setDimension(Dimension dim);
	void setDescription(String desc);
}
