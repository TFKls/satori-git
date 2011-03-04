package satori.test.ui;

import java.awt.datatransfer.DataFlavor;
import java.util.ArrayList;
import java.util.List;

import satori.test.STestSnap;

public class STestSnapTransfer {
	public static DataFlavor flavor = new DataFlavor(STestSnapTransfer.class, "Satori test snaps");
	
	private List<STestSnap> tests = new ArrayList<STestSnap>();
	
	public List<STestSnap> get() { return tests; }
	public void add(STestSnap test) { tests.add(test); }
}
