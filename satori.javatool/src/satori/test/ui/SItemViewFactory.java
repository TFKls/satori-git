package satori.test.ui;

import satori.common.ui.SPaneView;
import satori.test.impl.STestImpl;

public interface SItemViewFactory {
	SPaneView createView(STestImpl test);
}
