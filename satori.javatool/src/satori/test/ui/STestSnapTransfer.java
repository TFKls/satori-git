package satori.test.ui;

import java.awt.datatransfer.DataFlavor;
import java.util.ArrayList;
import java.util.Collection;

import satori.test.STestSnap;

public class STestSnapTransfer {
	public static DataFlavor flavor = new DataFlavor(STestSnapTransfer.class, "Satori test snaps");
	
	private Collection<STestSnap> tests = new ArrayList<STestSnap>();
	
	public Collection<STestSnap> get() { return tests; }
	public void add(STestSnap test) { tests.add(test); }
}
