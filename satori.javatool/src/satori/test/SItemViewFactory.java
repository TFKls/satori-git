package satori.test;

import satori.common.ui.SPaneView;

public interface SItemViewFactory {
	SPaneView createView(STestImpl test);
}
