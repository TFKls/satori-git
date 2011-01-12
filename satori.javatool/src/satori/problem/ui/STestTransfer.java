package satori.problem.ui;

import java.awt.datatransfer.DataFlavor;
import java.util.ArrayList;
import java.util.Collection;

import satori.test.STestSnap;

public class STestTransfer {
	public static DataFlavor flavor = new DataFlavor(STestTransfer.class, "Satori tests");
	
	private Collection<STestSnap> tests = new ArrayList<STestSnap>();
	
	public Iterable<STestSnap> getTests() { return tests; }
	public void addTest(STestSnap test) { tests.add(test); }
}
